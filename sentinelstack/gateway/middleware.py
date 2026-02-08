import uuid
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response
from sentinelstack.gateway.context import RequestCtx, set_context, reset_context

class RequestContextMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        # 1. Generate Request ID
        request_id = str(uuid.uuid4())
        
        # 2. Determine Client IP (Handle Proxy Headers)
        # In production, trust specific proxies only. For v1, we check headers aggressively.
        client_ip = request.client.host if request.client else "127.0.0.1"
        if "x-forwarded-for" in request.headers:
            # X-Forwarded-For: <client>, <proxy1>, <proxy2>
            client_ip = request.headers["x-forwarded-for"].split(",")[0].strip()
        elif "x-real-ip" in request.headers:
            client_ip = request.headers["x-real-ip"]
            
        # 3. Create Context Object
        ctx = RequestCtx(
            request_id=request_id,
            client_ip=client_ip,
            user_id=None, # Will be populated by Auth Middleware later
            path=request.url.path,
            method=request.method
        )
        
        # 4. Set ContextVar
        token = set_context(ctx)
        
        try:
            # 5. Process Request
            response = await call_next(request)
            
            # 6. Attach Request ID to Response Header (Visibility)
            response.headers["X-Request-ID"] = request_id
            return response
            
        finally:
            # 7. Cleanup Context (Crucial!)
            reset_context(token)