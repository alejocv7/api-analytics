import asyncio
from collections.abc import AsyncGenerator
from pathlib import Path

import pytest
import pytest_asyncio
import redis.asyncio as async_redis
from alembic.config import Config
from httpx import ASGITransport, AsyncClient
from sqlalchemy import event, pool
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from testcontainers.postgres import PostgresContainer
from testcontainers.redis import RedisContainer

from alembic import command
from app.core.config import settings


@pytest.fixture(scope="session")
def postgres_container():
    with PostgresContainer("postgres:16-alpine") as pg:
        yield pg


@pytest.fixture(scope="session")
def async_db_url(postgres_container) -> str:
    settings.POSTGRES_SERVER = postgres_container.get_container_host_ip()
    settings.POSTGRES_PORT = postgres_container.get_exposed_port(5432)
    settings.POSTGRES_DB = postgres_container.dbname
    settings.POSTGRES_USER = postgres_container.username
    settings.POSTGRES_PASSWORD = postgres_container.password
    settings.model_rebuild()

    return settings.SQLALCHEMY_DATABASE_URI


@pytest.fixture(scope="session")
def redis_container():
    with RedisContainer("redis:7-alpine") as redis_tc:
        yield redis_tc


@pytest.fixture(scope="session")
def redis_url(redis_container) -> str:
    settings.REDIS_HOST = redis_container.get_container_host_ip()
    settings.REDIS_PORT = redis_container.get_exposed_port(6379)
    settings.model_rebuild()

    return settings.REDIS_URL


@pytest_asyncio.fixture(scope="session", autouse=True)
async def apply_migrations(async_db_url: str):
    project_root = Path(__file__).resolve().parent.parent
    alembic_cfg = Config(project_root / "alembic.ini")
    alembic_cfg.set_main_option("sqlalchemy.url", async_db_url)
    await asyncio.to_thread(command.upgrade, alembic_cfg, "head")


@pytest_asyncio.fixture(scope="session")
async def engine(async_db_url: str):
    engine = create_async_engine(async_db_url, poolclass=pool.NullPool)
    yield engine
    await engine.dispose()


@pytest_asyncio.fixture
async def db_session(engine):
    async with engine.connect() as conn:
        transaction = await conn.begin()
        session = AsyncSession(bind=conn, expire_on_commit=False)
        await session.begin_nested()

        @event.listens_for(session.sync_session, "after_transaction_end")
        def _restart_savepoint(sync_session, trans):  # pragma: no cover - SQLA hook
            if trans.nested and not trans._parent.nested:
                sync_session.begin_nested()

        try:
            yield session
        finally:
            await session.close()
            await transaction.rollback()


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


@pytest_asyncio.fixture
async def test_user(db_session: AsyncSession):
    """Create a test user."""
    from tests.factories import create_user

    return await create_user(db_session)


@pytest_asyncio.fixture
async def project(db_session: AsyncSession, test_user):
    """Create a test project."""
    from tests.factories import create_project

    return await create_project(db_session, user=test_user)


@pytest_asyncio.fixture
async def auth_headers(test_user):
    """Get auth headers for the test user."""
    from app.services import auth_service

    token_resp = auth_service.create_user_token(test_user)
    return {"Authorization": f"Bearer {token_resp.access_token}"}
