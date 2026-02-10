import time
from redis.asyncio import Redis
from sentinelstack.cache import redis_client

# --- LUA SCRIPT START ---
TOKEN_BUCKET_SCRIPT = """
local key = KEYS[1]
local capacity = tonumber(ARGV[1])
local rate = tonumber(ARGV[2])
local now = tonumber(ARGV[3])
local requested = tonumber(ARGV[4])

-- Get current state
local last_tokens = tonumber(redis.call("HGET", key, "tokens"))
local last_refill = tonumber(redis.call("HGET", key, "last_refill"))

-- Initialize if missing
if last_tokens == nil then
    last_tokens = capacity
    last_refill = now
end

-- Refill tokens based on time passed
local delta = math.max(0, now - last_refill)
local filled_tokens = math.min(capacity, last_tokens + (delta * rate))

-- Check if we have enough
local allowed = filled_tokens >= requested
local new_tokens = filled_tokens
local retry_after = 0

if allowed then
    new_tokens = filled_tokens - requested
else
    retry_after = (requested - filled_tokens) / rate
end

-- Save new state (expire in 24h to clean up stale keys)
redis.call("HSET", key, "tokens", new_tokens, "last_refill", now)
redis.call("EXPIRE", key, 86400)

return {allowed, new_tokens, retry_after}
"""
# --- LUA SCRIPT END ---

class RateLimitBackend:
    def __init__(self, redis: Redis):
        self.redis = redis
        # Pre-load script for performance
        self.script = self.redis.register_script(TOKEN_BUCKET_SCRIPT)

    async def check_limit(
        self, 
        key: str, 
        capacity: int, 
        rate: float, 
        cost: int = 1
    ) -> tuple[bool, float, float]:
        """
        Returns: (is_allowed, remaining_tokens, retry_after_seconds)
        """
        now = time.time()
        
        # Execute Lua Script
        # Result is [allowed (1/0), new_tokens, retry_after]
        result = await self.script(
            keys=[key],
            args=[capacity, rate, now, cost]
        )
        
        allowed = bool(result[0])
        remaining = float(result[1])
        retry_after = float(result[2])
        
        return allowed, remaining, retry_after

# Global Instance
limiter_backend = RateLimitBackend(redis_client)