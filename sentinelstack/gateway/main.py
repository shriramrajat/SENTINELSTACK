from fastapi import FastAPI
from contextlib import asynccontextmanager
from sentinelstack.config import settings
from sentinelstack.auth.router import router as auth_router


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

@app.get("/health")
async def health_check():
    """
    Basic health check to verify transparency of configuration.
    """
    return {
        "status": "active",
        "env": settings.ENV,
        "service": "SentinelStack Gateway"
    }