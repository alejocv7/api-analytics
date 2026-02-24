import pytest
import pytest_asyncio
import redis.asyncio as async_redis

from app.core.config import settings


@pytest.fixture(scope="session")
def redis_url(redis_container) -> str:
    settings.REDIS_HOST = redis_container.get_container_host_ip()
    settings.REDIS_PORT = redis_container.get_exposed_port(6379)
    settings.model_rebuild()

    return settings.REDIS_URL


@pytest_asyncio.fixture(scope="session")
async def async_redis_client(redis_url: str):
    client = async_redis.Redis.from_url(redis_url, decode_responses=True)
    try:
        yield client
    finally:
        await client.aclose()


@pytest_asyncio.fixture(autouse=True)
async def reset_rate_limiter(redis_url: str, async_redis_client: async_redis.Redis):
    """Reset limiter and Redis state for integration tests."""
    from app.core.rate_limiter import limiter
    from tests.support.rate_limiter import configure_test_limiter_storage

    configure_test_limiter_storage(redis_url)

    await async_redis_client.flushdb()
    limiter.reset()
    yield
