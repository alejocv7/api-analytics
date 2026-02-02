import logging

from sqlalchemy import create_engine, select
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.orm import sessionmaker

from app.core.config import settings
from app.models import Base

logger = logging.getLogger(__name__)

# SQLite requires special handling for check_same_thread
connect_args = {}
if settings.SQLALCHEMY_DATABASE_URI.startswith("sqlite"):
    connect_args = {"check_same_thread": False}

engine = create_engine(
    settings.SQLALCHEMY_DATABASE_URI, pool_pre_ping=True, connect_args=connect_args
)
Session = sessionmaker(bind=engine, autoflush=False, autocommit=False)

async_engine = create_async_engine(
    settings.ASYNC_SQLALCHEMY_DATABASE_URI, pool_pre_ping=True
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


def init_db():
    try:
        Base.metadata.create_all(engine)
        logger.info("Successfully initialized database")
    except Exception as e:
        logger.error(f"Error initializing database: {e}")
        raise
