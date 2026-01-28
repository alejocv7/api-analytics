from sqlalchemy import create_engine, select
from sqlalchemy.orm import sessionmaker

from app.core.config import settings

# SQLite requires special handling for check_same_thread
connect_args = {}
if settings.SQLALCHEMY_DATABASE_URI.startswith("sqlite"):
    connect_args = {"check_same_thread": False}

engine = create_engine(
    settings.SQLALCHEMY_DATABASE_URI, pool_pre_ping=True, connect_args=connect_args
)
Session = sessionmaker(bind=engine, autoflush=False, autocommit=False)


def wakeup_db():
    try:
        with Session() as session:
            session.execute(select(1))
        print(f"Successfully connected to database: {settings.SQLALCHEMY_DATABASE_URI}")
    except Exception as e:
        print(f"Error connecting to database: {e}")
