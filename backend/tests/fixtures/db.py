import asyncio
from pathlib import Path

import pytest
import pytest_asyncio
from alembic.config import Config
from sqlalchemy import event, pool
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine

from alembic import command
from app.core.config import settings


@pytest.fixture(scope="session")
def async_db_url(postgres_container) -> str:
    settings.POSTGRES_SERVER = postgres_container.get_container_host_ip()
    settings.POSTGRES_PORT = postgres_container.get_exposed_port(5432)
    settings.POSTGRES_DB = postgres_container.dbname
    settings.POSTGRES_USER = postgres_container.username
    settings.POSTGRES_PASSWORD = postgres_container.password
    settings.model_rebuild()

    return settings.SQLALCHEMY_DATABASE_URI


@pytest_asyncio.fixture(scope="session", autouse=True)
async def apply_migrations(async_db_url: str):
    project_root = Path(__file__).resolve().parent.parent.parent
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
