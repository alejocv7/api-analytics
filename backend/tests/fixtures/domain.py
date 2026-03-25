import pytest_asyncio
from sqlalchemy.ext.asyncio import AsyncSession


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
async def auth_cookies(test_user, db_session: AsyncSession):
    """Get auth cookies for the test user."""
    from tests.factories import create_web_auth_cookies

    return await create_web_auth_cookies(db_session, user=test_user)
