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

# ---------------------------------------------------------------------------
# Emergency In-Memory Fallback Rate Limiter
# Used when Redis is unavailable. Bounded to MAX_FALLBACK_IPS entries to
# prevent unbounded memory growth from unique IPs during a Redis outage.
# ---------------------------------------------------------------------------
MAX_FALLBACK_IPS = 10_000
FALLBACK_RATES: dict = {}  # ip -> {"tokens": float, "last_refill": float}


def check_emergency_limit(ip: str) -> bool:
    """
    Token-bucket fallback that runs entirely in local memory.
    Allows 10 requests per 60 seconds per IP.
    Evicts the oldest tracked IP when the cap is reached (insertion-order eviction).
    """
    now = time.time()

    if ip not in FALLBACK_RATES:
        if len(FALLBACK_RATES) >= MAX_FALLBACK_IPS:
            # Python dicts are insertion-ordered since 3.7 — evict the oldest
            FALLBACK_RATES.pop(next(iter(FALLBACK_RATES)))
        FALLBACK_RATES[ip] = {"tokens": 10.0, "last_refill": now}

    state = FALLBACK_RATES[ip]

    # Refill tokens (10 per 60 seconds)
    delta = max(0.0, now - state["last_refill"])
    tokens = min(10.0, state["tokens"] + (delta * (10.0 / 60.0)))

    if tokens >= 1.0:
        state["tokens"] = tokens - 1.0
        state["last_refill"] = now
        return True  # Allowed

    state["tokens"] = tokens
    state["last_refill"] = now
    return False  # Blocked


class RequestContextMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        start_time = time.time()

        # 1. Generate Request ID & IP
        request_id = str(uuid.uuid4())
        client_ip = request.client.host if request.client else "127.0.0.1"
        if "x-forwarded-for" in request.headers:
            client_ip = request.headers["x-forwarded-for"].split(",")[0].strip()

        # 2. Attempt Identity Extraction (Optimistic — failures are silent)
        user_id = None
        role = None
        tier = None
        auth_header = request.headers.get("Authorization")
        if auth_header and auth_header.startswith("Bearer "):
            token = auth_header.split(" ")[1]
            try:
                # Verify signature only (CPU-bound but fast; no DB hit)
                payload = jwt.decode(
                    token,
                    settings.SECRET_KEY,
                    algorithms=[settings.ALGORITHM]
                )
                user_id = payload.get("sub")
                role = payload.get("role")
                tier = payload.get("tier", "free")
            except JWTError:
                # Invalid/Expired token → treat as anonymous
                pass

        # 3. Create Context
        ctx = RequestCtx(
            request_id=request_id,
            client_ip=client_ip,
            user_id=user_id,
            role=role,
            tier=tier,
            path=request.url.path,
            method=request.method
        )
        ctx_token = set_context(ctx)

        status_code = 500

        try:
            # 4. Rate Limit Check (Identity-Aware)
            # Skipped for infrastructure endpoints and read-only observability paths.
            # NOTE: /ai/* is intentionally included in rate limiting to prevent abuse.
            if ctx.path not in ["/health", "/docs", "/openapi.json", "/metrics"] and \
               not ctx.path.startswith(("/stats", "/dashboard", "/static")):

                # Fail-open circuit breaker: if Redis is down, fall back to local memory
                try:
                    allowed, headers = await rate_limiter.check_request(ctx)
                    if not allowed:
                        status_code = 429
                        RATE_LIMIT_HITS.labels(path=ctx.path).inc()
                        return JSONResponse(
                            status_code=429,
                            content={"detail": "Rate limit exceeded"},
                            headers=headers
                        )
                except Exception:
                    # Redis failed — activate emergency in-memory limiter
                    if not check_emergency_limit(ctx.client_ip):
                        RATE_LIMIT_HITS.labels(path=ctx.path).inc()
                        return JSONResponse(
                            status_code=429,
                            content={"detail": "Emergency rate limit exceeded. Service degraded."},
                            headers={"X-RateLimit-Fallback": "True"}
                        )

            # 5. Process Request
            response = await call_next(request)
            status_code = response.status_code
            response.headers["X-Request-ID"] = request_id
            return response

        except Exception as exc:
            # 6. Capture internal errors
            status_code = 500
            SYSTEM_ERRORS.labels(
                path=ctx.path,
                error_type=type(exc).__name__
            ).inc()
            raise exc

        finally:
            # 7. Metrics & Logging (always runs)
            duration = time.time() - start_time

            HTTP_REQUESTS_TOTAL.labels(
                method=ctx.method,
                path=ctx.path,
                status_code=status_code
            ).inc()

            HTTP_REQUEST_DURATION_SECONDS.labels(
                method=ctx.method,
                path=ctx.path
            ).observe(duration)

            # Snapshot log queue depth for the gauge
            if hasattr(log_service, "queue"):
                LOG_QUEUE_SIZE.set(log_service.queue.qsize())

            # Async logging — fire-and-forget, never blocks the request
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
                    "error_flag": status_code >= 400,
                }
                log_service.log_request(log_data)

            reset_context(ctx_token)