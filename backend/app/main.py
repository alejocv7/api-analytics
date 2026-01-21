from contextlib import asynccontextmanager

from fastapi import FastAPI
from sqlalchemy import text

from app.api.v1.router import router as v1_router
from app.core import db
from app.core.config import settings
from app.health import router as health_router
from app.middleware import APIMetricMiddleware


@asynccontextmanager
async def lifespan(app: FastAPI):
    try:
        with db.get_db() as db_session:
            db_session.execute(text("SELECT 1"))
        print(f"Successfully connected to database: {settings.SQLALCHEMY_DATABASE_URI}")
    except Exception as e:
        print(f"Error connecting to database: {e}")

    yield


app = FastAPI(
    title=settings.PROJECT_NAME,
    description=settings.PROJECT_DESCRIPTION,
    lifespan=lifespan,
)


@app.get("/", tags=["root"])
async def root():
    return {
        "message": settings.PROJECT_NAME,
        "description": settings.PROJECT_DESCRIPTION,
        "docs": "/docs",
    }


# Routers
app.include_router(health_router, tags=["health"])
app.include_router(v1_router, prefix=settings.API_V1_STR)

# Middleware
app.add_middleware(APIMetricMiddleware)
