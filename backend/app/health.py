from datetime import datetime, timezone
from importlib.metadata import version

from fastapi import APIRouter

from app.core.config import settings
from app.core.db import is_db_connected

router = APIRouter()

try:
    API_VERSION = version("api-analytics-service")
except Exception:
    API_VERSION = "unknown"


@router.get("/health")
async def health():
    db_connected = await is_db_connected()
    return {
        "status": "online" if db_connected else "offline",
        "database_status": "healthy" if db_connected else "unhealthy",
        "environment": settings.ENVIRONMENT,
        "version": API_VERSION,
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }
