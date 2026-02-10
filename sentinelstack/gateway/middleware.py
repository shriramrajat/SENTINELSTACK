import uuid
import time
import datetime
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import JSONResponse
from sentinelstack.gateway.context import RequestCtx, set_context, reset_context
from sentinelstack.rate_limit.service import rate_limiter
from sentinelstack.logging.service import log_service

class RequestContextMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        start_time = time.time()
        
        # 1. Generate Request ID & IP
        request_id = str(uuid.uuid4())
        client_ip = request.client.host if request.client else "127.0.0.1"
        if "x-forwarded-for" in request.headers:
            client_ip = request.headers["x-forwarded-for"].split(",")[0].strip()
        
        # 2. Create Context
        ctx = RequestCtx(
            request_id=request_id,
            client_ip=client_ip,
            user_id=None, 
            path=request.url.path,
            method=request.method
        )
        token = set_context(ctx)
        
        status_code = 500
        
        try:
            # 3. Rate Limit Check
            if ctx.path not in ["/health", "/docs", "/openapi.json"]:
                allowed, headers = await rate_limiter.check_request(ctx)
                if not allowed:
                    status_code = 429
                    return JSONResponse(status_code=429, content={"detail": "Rate limit exceeded"}, headers=headers)

            # 4. Process Request
            response = await call_next(request)
            status_code = response.status_code
            response.headers["X-Request-ID"] = request_id
            return response
            
        except Exception as exc:
            # 5. Capture internal errors for logging
            status_code = 500
            raise exc
            
        finally:
            # 6. Async Logging (Fire and Forget)
            latency = (time.time() - start_time) * 1000
            
            # Don't log health in production usually, but ok for now
            if ctx.path != "/health":
                log_data = {
                    "request_id": ctx.request_id,
                    "timestamp": datetime.datetime.utcnow(),
                    "client_ip": ctx.client_ip,
                    "user_id": ctx.user_id,
                    "method": ctx.method,
                    "path": ctx.path,
                    "status_code": status_code,
                    "latency_ms": latency,
                    "error_flag": status_code >= 400
                }
                log_service.log_request(log_data)
                
            reset_context(token)