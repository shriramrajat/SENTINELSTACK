import pytest
import asyncio
from httpx import AsyncClient, ASGITransport
from sentinelstack.gateway.main import app
from sentinelstack.config import settings

# Force test environment config
settings.ENV = "test"

# Make sure we use a session-scoped event loop for async tests
@pytest.fixture(scope="session")
def event_loop():
    try:
        loop = asyncio.get_running_loop()
    except RuntimeError:
        loop = asyncio.new_event_loop()
    yield loop
    loop.close()

@pytest.fixture(scope="module")
async def client():
    """
    Setup an async client to test the API.
    """
    # Create transport for direct app testing (no network)
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac