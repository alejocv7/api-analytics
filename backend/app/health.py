from importlib.metadata import version

from fastapi import APIRouter

from app import schemas
from app.core.config import settings
from app.core.db import is_db_connected

router = APIRouter()

try:
    API_VERSION = version("api-analytics-service")
except Exception:
    API_VERSION = "unknown"


@router.get("/health", response_model=schemas.HealthResponse)
async def health() -> schemas.HealthResponse:
    db_connected = await is_db_connected()

    return schemas.HealthResponse(
        status="online" if db_connected else "offline",
        components={
            "database": "healthy" if db_connected else "unhealthy",
        },
        environment=settings.ENVIRONMENT,
        version=API_VERSION,
    )
