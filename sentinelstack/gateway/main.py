from fastapi import FastAPI
from contextlib import asynccontextmanager
from sentinelstack.config import settings
from sentinelstack.auth.router import router as auth_router
from sentinelstack.gateway.middleware import RequestContextMiddleware
from sentinelstack.gateway.context import get_context



@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup: Log configuration (sanitize secrets in real usage)
    print(f"INFO:    Starting {settings.APP_NAME} in {settings.ENV} mode")
    print(f"INFO:    Database: {settings.DATABASE_URL}")
    print(f"INFO:    Redis: {settings.REDIS_URL}")
    yield
    # Shutdown logic (close connections) goes here
    print(f"INFO:    Shutting down {settings.APP_NAME}")

app = FastAPI(
    title=settings.APP_NAME,
    lifespan=lifespan
)

app.include_router(auth_router)
app.add_middleware(RequestContextMiddleware)


@app.get("/health")
async def health_check():
    """
    Returns system status and current request context.
    """
    ctx = get_context()
    return {
        "status": "active",
        "env": settings.ENV,
        "request_id": ctx.request_id if ctx else "unknown",
        "your_ip": ctx.client_ip if ctx else "unknown"
    }