import logging
from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager

from asgi_correlation_id import CorrelationIdMiddleware
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from starlette.middleware.trustedhost import TrustedHostMiddleware

from app.api.v1.routes import router as v1_router
from app.core import db
from app.core.config import settings
from app.core.exceptions import register_exceptions
from app.core.logging_config import setup_logging
from app.core.rate_limiter import limiter
from app.health import router as health_router
from app.middleware import (
    LoggingMiddleware,
    MetricMiddleware,
    SecurityHeadersMiddleware,
)

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(_: FastAPI) -> AsyncGenerator[None]:
    setup_logging()

    await db.init_db()
    if not await db.is_db_connected():
        raise RuntimeError("Database connection failed during startup")
    logger.info("Application started successfully!")

    yield

    await db.async_engine.dispose()
    logger.info("Application shutting down!")


app = FastAPI(
    title=settings.PROJECT_NAME,
    description=settings.PROJECT_DESCRIPTION,
    lifespan=lifespan,
    docs_url=None if settings.IS_PRODUCTION else "/docs",
    redoc_url=None if settings.IS_PRODUCTION else "/redoc",
    openapi_url=None if settings.IS_PRODUCTION else "/openapi.json",
)

# Exception handlers
register_exceptions(app)

# State
app.state.limiter = limiter

# Routers
app.include_router(health_router, tags=["health"])
app.include_router(v1_router, prefix=settings.API_V1_STR)

# Middleware (Executed in reverse order)
app.add_middleware(MetricMiddleware)
app.add_middleware(LoggingMiddleware)
app.add_middleware(CorrelationIdMiddleware, header_name="X-Request-ID")

# Security Middlewares
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PATCH", "DELETE"],
    allow_headers=["*"],
)

app.add_middleware(
    TrustedHostMiddleware,
    allowed_hosts=settings.TRUSTED_HOSTS,
)

app.add_middleware(SecurityHeadersMiddleware)


@app.get("/", tags=["root"])
async def root() -> dict[str, str]:
    return {
        "message": settings.PROJECT_NAME,
        "description": settings.PROJECT_DESCRIPTION,
        "docs": "/docs",
    }
