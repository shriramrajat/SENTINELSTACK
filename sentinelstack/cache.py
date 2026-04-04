import redis.asyncio as redis
from sentinelstack.config import settings

# Added massive connection pool + aggressive timeouts 
redis_client = redis.from_url(
    settings.REDIS_URL,
    encoding="utf-8",
    decode_responses=True,
    max_connections=1000,         # Keeps 1000 connections open/ready
    socket_timeout=1.0,           # If Redis stalls for 1s, kill request
    socket_connect_timeout=0.5    # Fail fast if Redis is dead
)

async def get_client():
    return redis_client


