from contextvars import ContextVar
from typing import Optional
from pydantic import BaseModel

class RequestCtx(BaseModel):
    request_id: str
    client_ip: str
    user_id: Optional[str] = None
    path: str
    method: str

# The ContextVar is a "Magic Global" that is unique per async task (request)
# It is empty by default.
_request_ctx_var: ContextVar[Optional[RequestCtx]] = ContextVar("request_ctx", default=None)

def get_context() -> Optional[RequestCtx]:
    """Retrieve the context for the current request."""
    return _request_ctx_var.get()

def set_context(ctx: RequestCtx):
    """Set the context for the current request."""
    return _request_ctx_var.set(ctx)

def reset_context(token):
    """Clean up context to prevent leaks."""
    _request_ctx_var.reset(token)