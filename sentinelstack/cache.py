import redis.asyncio as redis
from sentinelstack.config import settings


redis_client = redis.from_url(
    settings.REDIS_URL,
    encoding="utf-8",
    decode_responses=True,
)

async def get_client():
    return redis_client

