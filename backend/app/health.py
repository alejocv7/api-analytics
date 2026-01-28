from datetime import datetime

from fastapi import APIRouter

from app.core.config import settings
from app.core.db import is_db_connected

router = APIRouter()


@router.get("/health")
async def health():
    db_connected = is_db_connected()
    return {
        "status": "online" if db_connected else "offline",
        "database_status": "healthy" if db_connected else "unhealthy",
        "environment": settings.ENVIRONMENT,
        "timestamp": datetime.now().isoformat(),
    }
