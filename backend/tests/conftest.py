import asyncio
import os
from typing import AsyncGenerator

import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import (
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)

# Set environment variables for tests
os.environ["ENVIRONMENT"] = "testing"
os.environ["HASH_SALT"] = "test_salt_do_not_use_in_production"
os.environ["SECURITY_KEY"] = "test_secret_key_extremely_secret"
os.environ["PROJECT_NAME"] = "Test Analytics"
os.environ["PROJECT_DESCRIPTION"] = "Testing Description"
os.environ["SQLALCHEMY_DATABASE_URI"] = "sqlite:///./test.db"
os.environ["REDIS_URL"] = "redis://localhost:6379/0"
os.environ["API_KEY_LOOKUP_PREFIX_LENGTH"] = "8"
os.environ["BACKEND_CORS_ORIGINS"] = "[*]"
os.environ["TRUSTED_HOSTS"] = "[*]"

from app.core import db
from app.dependencies import get_db
from app.main import app
from app.models.base import Base

# Test database URL
TEST_DATABASE_URL = "sqlite+aiosqlite:///./test.db"


@pytest.fixture(scope="session")
def event_loop():
    """Create an instance of the default event loop for each test case."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest_asyncio.fixture(scope="session", autouse=True)
async def test_engine():
    """Create a test engine and initialize the database schema."""
    engine = create_async_engine(
        TEST_DATABASE_URL, connect_args={"check_same_thread": False}
    )

    # Override global db engine and session local
    db.async_engine = engine
    db.AsyncSessionLocal = async_sessionmaker(
        engine, class_=AsyncSession, expire_on_commit=False
    )

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    yield engine

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)

    await engine.dispose()

    # Clean up test database file
    if os.path.exists("./test.db"):
        os.remove("./test.db")


@pytest_asyncio.fixture
async def db_session(test_engine) -> AsyncGenerator[AsyncSession, None]:
    """Create a new database session for a test with transaction isolation."""
    connection = await test_engine.connect()
    transaction = await connection.begin()

    TestingSessionLocal = async_sessionmaker(
        bind=connection,
        class_=AsyncSession,
        expire_on_commit=False,
    )

    async with TestingSessionLocal() as session:
        yield session

    await transaction.rollback()
    await connection.close()


@pytest_asyncio.fixture
async def client(db_session: AsyncSession) -> AsyncGenerator[AsyncClient, None]:
    """Create a test client that uses the test database."""

    async def override_get_db():
        yield db_session

    app.dependency_overrides[get_db] = override_get_db

    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as ac:
        yield ac

    app.dependency_overrides.clear()


@pytest_asyncio.fixture
async def test_user(db_session: AsyncSession):
    """Create a test user."""
    from app import models
    from app.core import security

    user = models.User(
        email="test@example.com",
        full_name="Test User",
        hashed_password=security.hash_password("Password123!"),
        is_active=True,
    )
    db_session.add(user)
    await db_session.commit()
    await db_session.refresh(user)
    return user


@pytest_asyncio.fixture
async def auth_headers(test_user):
    """Get auth headers for the test user."""
    from app.services import auth_service

    token_resp = auth_service.create_user_token(test_user)
    return {"Authorization": f"Bearer {token_resp.access_token}"}
