from collections.abc import AsyncGenerator

import pytest_asyncio
import redis.asyncio as async_redis
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession


@pytest_asyncio.fixture
async def client(
    db_session: AsyncSession,
    async_redis_client: async_redis.Redis,
) -> AsyncGenerator[AsyncClient]:
    """Create a test client that uses testcontainers database and Redis."""
    from app.dependencies import get_db, get_redis
    from app.main import app

    async def override_get_db():
        yield db_session

    async def override_get_redis():
        yield async_redis_client

    app.dependency_overrides[get_db] = override_get_db
    app.dependency_overrides[get_redis] = override_get_redis

    try:
        async with AsyncClient(
            transport=ASGITransport(app=app, raise_app_exceptions=False),
            base_url="http://test",
        ) as ac:
            yield ac
    finally:
        app.dependency_overrides.clear()
