from fastapi import APIRouter

from app import schemas
from app.core.config import settings
from app.core.db import is_db_connected
from app.core.redis import redis_manager

router = APIRouter()


@router.get("/health", response_model=schemas.HealthResponse)
async def health() -> schemas.HealthResponse:
    db_healthy = await is_db_connected()
    redis_healthy = await redis_manager.is_connected()

    if db_healthy and redis_healthy:
        status = "online"
    elif not db_healthy and not redis_healthy:
        status = "offline"
    else:
        status = "degraded"

    return schemas.HealthResponse(
        status=status,
        components={
            "database": "healthy" if db_healthy else "unhealthy",
            "redis": "healthy" if redis_healthy else "unhealthy",
        },
        environment=settings.ENVIRONMENT,
        version=settings.VERSION,
    )
