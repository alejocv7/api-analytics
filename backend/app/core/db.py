from sqlalchemy import create_engine, select
from sqlalchemy.orm import sessionmaker

from app.core.config import settings
from app.models import Base

# SQLite requires special handling for check_same_thread
connect_args = {}
if settings.SQLALCHEMY_DATABASE_URI.startswith("sqlite"):
    connect_args = {"check_same_thread": False}

engine = create_engine(
    settings.SQLALCHEMY_DATABASE_URI, pool_pre_ping=True, connect_args=connect_args
)
Session = sessionmaker(bind=engine, autoflush=False, autocommit=False)


def is_db_connected() -> bool:
    try:
        with Session() as session:
            session.execute(select(1))
        return True
    except Exception:
        return False


def init_db():
    try:
        Base.metadata.create_all(engine)
        print("Successfully initialized database")
    except Exception as e:
        print(f"Error initializing database: {e}")
        raise
