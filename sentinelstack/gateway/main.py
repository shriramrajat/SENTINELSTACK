import asyncio
from fastapi import FastAPI
from contextlib import asynccontextmanager
from sentinelstack.config import settings
from sentinelstack.auth.router import router as auth_router
from sentinelstack.gateway.middleware import RequestContextMiddleware
from sentinelstack.gateway.context import get_context
from sentinelstack.logging.service import log_service
from sentinelstack.stats.router import router as stats_router


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    print(f"INFO:    Starting {settings.APP_NAME}")
    
    # Start Log Worker Task
    task = asyncio.create_task(log_service.worker())
    
    yield
    
    # Shutdown
    print(f"INFO:    Shutting down {settings.APP_NAME}")
    log_service.is_running = False
    await task 
app = FastAPI(
    title=settings.APP_NAME,
    lifespan=lifespan
)
app.add_middleware(RequestContextMiddleware)
app.include_router(auth_router)


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

app.include_router(stats_router)