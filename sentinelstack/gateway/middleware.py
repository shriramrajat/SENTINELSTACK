import uuid
import time
import datetime
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import JSONResponse
from jose import jwt, JWTError

from sentinelstack.config import settings
from sentinelstack.gateway.context import RequestCtx, set_context, reset_context
from sentinelstack.rate_limit.service import rate_limiter
from sentinelstack.logging.service import log_service
from sentinelstack.monitoring.metrics import (
    HTTP_REQUESTS_TOTAL,
    HTTP_REQUEST_DURATION_SECONDS,
    RATE_LIMIT_HITS,
    SYSTEM_ERRORS,
    LOG_QUEUE_SIZE
)

class RequestContextMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        start_time = time.time()
        
        # 1. Generate Request ID & IP
        request_id = str(uuid.uuid4())
        client_ip = request.client.host if request.client else "127.0.0.1"
        if "x-forwarded-for" in request.headers:
            client_ip = request.headers["x-forwarded-for"].split(",")[0].strip()
            
        # 2. Attempt Identity Extraction (Optimistic)
        user_id = None
        auth_header = request.headers.get("Authorization")
        if auth_header and auth_header.startswith("Bearer "):
            token = auth_header.split(" ")[1]
            try:
                # Verify signature only (CPU bound, fast)
                payload = jwt.decode(
                    token, 
                    settings.SECRET_KEY, 
                    algorithms=[settings.ALGORITHM]
                )
                user_id = payload.get("sub")
            except JWTError:
                # Invalid/Expired token -> Treat as Anonymous
                pass

        # 3. Create Context
        ctx = RequestCtx(
            request_id=request_id,
            client_ip=client_ip,
            user_id=user_id, 
            path=request.url.path,
            method=request.method
        )
        token = set_context(ctx)
        
        status_code = 500
        
        try:
            # 4. Rate Limit Check (Identity Aware)
            # Skip health checks/static/metrics
            if ctx.path not in ["/health", "/docs", "/openapi.json", "/metrics"] and \
               not ctx.path.startswith(("/stats", "/ai", "/dashboard", "/static")):
               
                allowed, headers = await rate_limiter.check_request(ctx)
                if not allowed:
                    status_code = 429
                    
                    # Record Rate Limit Metric
                    RATE_LIMIT_HITS.labels(path=ctx.path, client_ip=ctx.client_ip).inc()
                    
                    return JSONResponse(
                        status_code=429, 
                        content={"detail": "Rate limit exceeded"}, 
                        headers=headers
                    )

            # 5. Process Request
            response = await call_next(request)
            status_code = response.status_code
            response.headers["X-Request-ID"] = request_id
            return response
            
        except Exception as exc:
            # 6. Capture internal errors
            status_code = 500
            
            # Record System Error Metric
            SYSTEM_ERRORS.labels(
                path=ctx.path, 
                error_type=type(exc).__name__
            ).inc()
            
            raise exc
            
        finally:
            # 7. Metrics & Logging (Always runs)
            duration = time.time() - start_time
            
            # Update Metrics
            HTTP_REQUESTS_TOTAL.labels(
                method=ctx.method,
                path=ctx.path, 
                status_code=status_code
            ).inc()
            
            HTTP_REQUEST_DURATION_SECONDS.labels(
                method=ctx.method,
                path=ctx.path
            ).observe(duration)
            
            # Update Log Queue Gauge (Snapshot)
            if hasattr(log_service, 'queue'):
                LOG_QUEUE_SIZE.set(log_service.queue.qsize())

            # Async Logging (Fire and Forget)
            if ctx.path not in ["/health", "/metrics"]:
                log_data = {
                    "request_id": ctx.request_id,
                    "timestamp": datetime.datetime.utcnow(),
                    "client_ip": ctx.client_ip,
                    "user_id": ctx.user_id,
                    "method": ctx.method,
                    "path": ctx.path,
                    "status_code": status_code,
                    "latency_ms": duration * 1000,
                    "error_flag": status_code >= 400
                }
                log_service.log_request(log_data)
                
            reset_context(token)