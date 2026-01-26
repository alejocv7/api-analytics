from contextlib import asynccontextmanager

from fastapi import FastAPI
from slowapi import _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded

from app.api.v1.router import router as v1_router
from app.core import db
from app.core.config import settings
from app.core.rate_limiter import limiter
from app.health import router as health_router
from app.middleware import MetricMiddleware


@asynccontextmanager
async def lifespan(app: FastAPI):
    db.wakeup_db()
    yield


app = FastAPI(
    title=settings.PROJECT_NAME,
    description=settings.PROJECT_DESCRIPTION,
    lifespan=lifespan,
)

app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)


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
app.add_middleware(MetricMiddleware)
