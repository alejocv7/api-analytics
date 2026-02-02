import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException
from fastapi.exceptions import RequestValidationError
from slowapi.errors import RateLimitExceeded

from app.api.v1.routes import router as v1_router
from app.core import db
from app.core.config import settings
from app.core.exceptions import (
    APIError,
    api_exception_handler,
    generic_exception_handler,
    http_exception_handler,
    rate_limit_handler,
    validation_exception_handler,
)
from app.core.logging_config import setup_logging
from app.core.rate_limiter import limiter
from app.health import router as health_router
from app.middleware import MetricMiddleware, RequestIDMiddleware

# Set up structured logging first
setup_logging()

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    db.init_db()
    if not await db.is_db_connected():
        raise Exception("Database connection failed")
    logger.info("Application started successfully!")
    yield
    logger.info("Application shutting down!")


app = FastAPI(
    title=settings.PROJECT_NAME,
    description=settings.PROJECT_DESCRIPTION,
    lifespan=lifespan,
)

app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, rate_limit_handler)  # type: ignore
app.add_exception_handler(HTTPException, http_exception_handler)  # type: ignore
app.add_exception_handler(APIError, api_exception_handler)  # type: ignore
app.add_exception_handler(RequestValidationError, validation_exception_handler)  # type: ignore
app.add_exception_handler(Exception, generic_exception_handler)  # type: ignore


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
app.add_middleware(RequestIDMiddleware)
app.add_middleware(MetricMiddleware)
