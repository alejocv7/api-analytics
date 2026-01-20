from datetime import datetime

from fastapi import FastAPI
from sqlalchemy import text

from app.api.v1.router import v1_router
from app.core import db
from app.core.config import settings
from app.middleware import APIMetricMiddleware

app = FastAPI(
    title=settings.PROJECT_NAME,
    description=settings.PROJECT_DESCRIPTION,
)

app.include_router(v1_router, prefix=settings.API_V1_STR)
app.add_middleware(APIMetricMiddleware)


@app.on_event("startup")
async def startup_event():
    try:
        db_session = next(db.get_db())
        db_session.execute(text("SELECT 1"))
        db_session.close()
        print(f"Successfully connected to database: {settings.SQLALCHEMY_DATABASE_URI}")
    except Exception as e:
        print(f"Error connecting to database: {e}")


@app.get("/")
async def root():
    return {
        "message": settings.PROJECT_NAME,
        "description": settings.PROJECT_DESCRIPTION,
        "docs": "/docs",
    }


@app.get("/health")
async def health():
    try:
        db_session = next(db.get_db())
        db_session.execute(text("SELECT 1"))
        db_session.close()
        db_status = "healthy"
    except Exception as e:
        db_status = f"unhealthy: {e}"

    return {
        "status": "online",
        "database_status": db_status,
        "environment": settings.ENVIRONMENT,
        "timestamp": datetime.now().isoformat(),
    }
