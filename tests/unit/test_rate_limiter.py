import pytest
from unittest.mock import AsyncMock, patch, MagicMock
from sentinelstack.rate_limit.service import RateLimitService, ANON_LIMIT, USER_LIMIT
from sentinelstack.gateway.context import RequestCtx

# ---------------------------------------------------------
# Test Suite for Logic Layer (No Real Redis)
# ---------------------------------------------------------

@pytest.mark.asyncio
class TestRateLimitService:
    
    def setup_method(self):
        """
        Runs before each test. We mock the 'limiter_backend' 
        so we don't need a real Redis connection.
        NOTE: Must be synchronous for standard pytest x/unit usage.
        """
        self.mock_backend = AsyncMock()
        
        # Patch the global instance of the backend used in service.py
        self.patcher = patch(
            "sentinelstack.rate_limit.service.limiter_backend", 
            self.mock_backend
        )
        self.mock_limiter = self.patcher.start()
        self.service = RateLimitService()

    def teardown_method(self):
        """Runs after each test."""
        self.patcher.stop()

    # -----------------------------------------------------
    # SCENARIO 1: Anonymous User
    # -----------------------------------------------------
    async def test_enforces_anon_limit_by_ip(self):
        # 1. Setup Context (No User ID, just IP)
        ctx = MagicMock(spec=RequestCtx)
        ctx.user_id = None
        ctx.client_ip = "192.168.1.5"

        # 2. Mock Backend Response (Allowed)
        # Return format: (allowed, remaining, retry_after)
        self.mock_limiter.check_limit.return_value = (True, 9, 0)

        # 3. Execute
        allowed, headers = await self.service.check_request(ctx)

        # 4. Assert Logic
        assert allowed is True
        
        # Verify we called backend with Correct Key (rl:ip:...) and Correct Limit (ANON)
        self.mock_limiter.check_limit.assert_called_once_with(
            key="rl:ip:192.168.1.5",
            capacity=ANON_LIMIT, # Should be 10
            rate=pytest.approx(ANON_LIMIT / 60),
            cost=1
        )

    # -----------------------------------------------------
    # SCENARIO 2: Authenticated User
    # -----------------------------------------------------
    async def test_enforces_user_limit_by_id(self):
        # 1. Setup Context (Has User ID)
        ctx = MagicMock(spec=RequestCtx)
        ctx.user_id = "user_123"
        ctx.client_ip = "192.168.1.5" # IP should be ignored for logic

        # 2. Mock Backend Response (Allowed)
        self.mock_limiter.check_limit.return_value = (True, 55, 0)

        # 3. Execute
        await self.service.check_request(ctx)

        # 4. Assert Logic
        # Verify we used the User Key (rl:user:...) and User Limit (USER)
        self.mock_limiter.check_limit.assert_called_once_with(
            key="rl:user:user_123",
            capacity=USER_LIMIT, # Should be 60
            rate=pytest.approx(USER_LIMIT / 60),
            cost=1
        )

    # -----------------------------------------------------
    # SCENARIO 3: Rate Limit Exceeded
    # -----------------------------------------------------
    async def test_handles_rejection_gracefully(self):
        ctx = MagicMock(spec=RequestCtx)
        ctx.user_id = None
        ctx.client_ip = "10.0.0.1"

        # 1. Mock Backend to say "Rejected, retry in 5s"
        self.mock_limiter.check_limit.return_value = (False, 0, 5.0)

        # 2. Execute
        allowed, headers = await self.service.check_request(ctx)

        # 3. Assert Headers
        assert allowed is False
        assert headers["X-RateLimit-Remaining"] == "0"
        
        # Ensure 'Reset' header is a future timestamp 
        # We can't check exact time, but it should be > 0
        assert int(headers["X-RateLimit-Reset"]) > 0