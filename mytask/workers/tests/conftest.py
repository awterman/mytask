import asyncio
import sys
from unittest.mock import patch

import pytest


class MockRedisCache:
    """A mock Redis cache that does nothing but can be used for tests"""

    async def get(self, key):
        return None

    async def set(self, key, value, ttl=None):
        pass

    async def delete(self, key):
        pass


@pytest.fixture
def event_loop():
    """Create an instance of the default event loop for each test case."""
    if sys.platform == "win32":
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())

    # Create a new loop for each test
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    yield loop
    loop.close()


@pytest.fixture(autouse=True)
def mock_env_vars():
    """Mock environment variables for testing"""
    env_vars = {
        "DATURA_API_KEY": "test_datura_key",
        "CHUTES_API_KEY": "test_chutes_key",
        "REDIS_HOST": "localhost",
        "REDIS_PORT": "6379",
        "REDIS_PASSWORD": "",
        "POSTGRES_DSN": "postgresql://user:pass@localhost:5432/test_db",
    }
    with patch.dict("os.environ", env_vars):
        yield


@pytest.fixture(autouse=True)
def mock_redis_cache():
    """Replace the Redis cache with a mock"""
    mock_cache = MockRedisCache()
    with patch("mytask.services.redis_cache.get_redis_cache", return_value=mock_cache):
        with patch(
            "mytask.services.tao_service.get_redis_cache", return_value=mock_cache
        ):
            yield


@pytest.fixture(autouse=True)
def disable_run_async():
    """Replace the run_async function with a synchronous version for testing"""

    # Mock implementation that just runs the coroutine
    def mock_run_async(coro):
        """Test implementation that runs the coroutine synchronously"""
        if asyncio.iscoroutine(coro):
            # Use the current event loop
            loop = asyncio.get_event_loop()
            return loop.run_until_complete(coro)
        return coro

    # Apply the mock
    with patch("mytask.workers.tasks.run_async", side_effect=mock_run_async):
        yield
