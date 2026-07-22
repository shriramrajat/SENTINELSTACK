import time
from typing import Tuple
from sentinelstack.rate_limit.backend import limiter_backend
from sentinelstack.gateway.context import RequestCtx

# Configuration (Could be moved to settings later)
ANON_LIMIT = 10      # requests per minute
ANON_RATE = 10 / 60  # refill rate per second

TIER_LIMITS = {
    "free": 60,       # 60 / min
    "pro": 600,       # 600 / min
    "enterprise": 6000 # 6000 / min
}

class RateLimitService:
    async def check_request(self, ctx: RequestCtx) -> Tuple[bool, dict]:
        """
        Determines the limit key and capacity based on context.
        Returns (is_allowed, headers)
        """
        # 1. Determine Identity & Policy
        if ctx.user_id:
            key = f"rl:user:{ctx.user_id}"
            tier = ctx.tier if ctx.tier else "free"
            capacity = TIER_LIMITS.get(tier, 60)
            rate = capacity / 60
        else:
            key = f"rl:ip:{ctx.client_ip}"
            capacity = ANON_LIMIT
            rate = ANON_RATE

        # 2. Check against Redis Backend
        allowed, remaining, retry_after = await limiter_backend.check_limit(
            key=key,
            capacity=capacity,
            rate=rate,
            cost=1
        )

        # 3. Construct Standard Headers
        headers = {
            "X-RateLimit-Limit": str(capacity),
            "X-RateLimit-Remaining": str(int(remaining)),
            "X-RateLimit-Reset": str(int(time.time() + retry_after)) if not allowed else "0"
        }
        
        return allowed, headers

# Global Instance
rate_limiter = RateLimitService()