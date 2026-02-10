import uuid
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import JSONResponse
from sentinelstack.gateway.context import RequestCtx, set_context, reset_context
from sentinelstack.rate_limit.service import rate_limiter

class RequestContextMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        # 1. Generate Request ID
        request_id = str(uuid.uuid4())
        
        # 2. Determine Client IP (Handle Proxy Headers)
        client_ip = request.client.host if request.client else "127.0.0.1"
        if "x-forwarded-for" in request.headers:
            client_ip = request.headers["x-forwarded-for"].split(",")[0].strip()
        elif "x-real-ip" in request.headers:
            client_ip = request.headers["x-real-ip"]
            
        # 3. Create Context Object
        # Note: authentication usually happens *after* middleware context but *before* logic.
        # Ideally, we would detect user_id from JWT here if we want rate limiting per user.
        # For Day 6, we assume anonymous mostly, unless we parse the header manually (advanced).
        ctx = RequestCtx(
            request_id=request_id,
            client_ip=client_ip,
            user_id=None, # In v1, we populate this via Dependencies or manual JWT check
            path=request.url.path,
            method=request.method
        )
        
        # 4. Set Global Context
        token = set_context(ctx)
        
        try:
            # 5. Rate Limiting Check (Skip for health check and docs)
            if ctx.path not in ["/health", "/docs", "/openapi.json"]:
                allowed, headers = await rate_limiter.check_request(ctx)
                
                if not allowed:
                    # REJECT REQUEST
                    return JSONResponse(
                        status_code=429,
                        content={"detail": "Rate limit exceeded"},
                        headers=headers
                    )
            
                # If allowed, proceed but keep headers to attach later?
                # Actually, attaching headers to the *successful* response is good practice too.
                # For simplicity in v1, we only attach on 429 or rely on context.

            # 6. Process Request
            response = await call_next(request)
            
            # 7. Attach Request ID
            response.headers["X-Request-ID"] = request_id
            
            # (Optional) Attach Rate Limit headers to success response if you want
            # This requires passing them out of the [if](cci:1://file:///d:/Rajat/Projects/SentinelStack/sentinelstack/gateway/main.py:9:0-17:56) block above.
            
            return response
            
        finally:
            # 8. Cleanup
            reset_context(token)