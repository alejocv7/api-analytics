import logging
from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager

from asgi_correlation_id import CorrelationIdMiddleware
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from slowapi.middleware import SlowAPIMiddleware
from starlette.middleware.trustedhost import TrustedHostMiddleware

from app.api.v1.routes import router as v1_router
from app.core import db
from app.core.config import settings
from app.core.exceptions import register_exceptions
from app.core.logging_config import setup_logging
from app.core.rate_limiter import limiter
from app.core.scheduler import MetricCleanupScheduler
from app.health import router as health_router
from app.middleware import (
    LoggingMiddleware,
    MetricMiddleware,
    SecurityHeadersMiddleware,
)

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None]:
    setup_logging()

    if not await db.is_db_connected():
        raise RuntimeError("Database connection failed during startup")

    cleanup_scheduler = MetricCleanupScheduler()
    cleanup_scheduler.start()

    logger.info("Application started successfully!")

    yield

    logger.info("Application shutting down!")

    logger.info("Shutdown: stopping metric cleanup scheduler")
    await cleanup_scheduler.stop(
        timeout_seconds=settings.SHUTDOWN_TASKS_CANCEL_TIMEOUT_SECONDS
    )

    if metric_middleware := getattr(app.state, "metric_middleware", None):
        logger.info("Shutdown: draining in-flight metric background tasks")
        await metric_middleware.drain_background_tasks(
            timeout_seconds=settings.SHUTDOWN_TASKS_CANCEL_TIMEOUT_SECONDS
        )

    logger.info("Shutdown: disposing database engine")
    await db.async_engine.dispose()


app = FastAPI(
    title=settings.PROJECT_NAME,
    description=settings.PROJECT_DESCRIPTION,
    lifespan=lifespan,
    docs_url="/docs" if settings.SHOW_DOCS else None,
    redoc_url="/redoc" if settings.SHOW_DOCS else None,
    openapi_url="/openapi.json" if settings.SHOW_DOCS else None,
)

# Exception handlers
register_exceptions(app)

# State
app.state.limiter = limiter

# Routers
app.include_router(health_router, tags=["health"])
app.include_router(v1_router, prefix=settings.API_V1_STR)

# Middleware (Executed in reverse order)
app.add_middleware(SlowAPIMiddleware)
app.add_middleware(LoggingMiddleware)
app.add_middleware(MetricMiddleware, app_state=app.state)
app.add_middleware(CorrelationIdMiddleware, header_name=settings.REQUEST_ID_HEADER)

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
async def root() -> dict[str, str | None]:
    return {
        "service": settings.PROJECT_NAME,
        "description": settings.PROJECT_DESCRIPTION,
        "version": settings.VERSION,
        "docs": "/docs" if settings.SHOW_DOCS else None,
        "redoc": "/redoc" if settings.SHOW_DOCS else None,
        "openapi": "/openapi.json" if settings.SHOW_DOCS else None,
    }
