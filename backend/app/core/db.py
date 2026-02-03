import logging

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.core.config import settings
from app.models import Base

logger = logging.getLogger(__name__)

async_engine = create_async_engine(
    str(settings.SQLALCHEMY_DATABASE_URI), pool_pre_ping=True
)
AsyncSessionLocal = async_sessionmaker(
    async_engine,
    class_=AsyncSession,
    autoflush=False,
    autocommit=False,
    expire_on_commit=False,
)


async def is_db_connected() -> bool:
    try:
        async with AsyncSessionLocal() as session:
            await session.execute(select(1))
        return True
    except Exception:
        return False


async def init_db() -> None:
    try:
        async with async_engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)
        logger.info("Successfully initialized database")
    except Exception:
        logger.exception("Error initializing database")
        raise
