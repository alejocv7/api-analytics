from datetime import datetime

from fastapi import APIRouter
from sqlalchemy import text

from app.core import db
from app.core.config import settings

router = APIRouter()


@router.get("/health")
async def health():
    try:
        with db.get_db() as db_session:
            db_session.execute(text("SELECT 1"))
        db_status = "healthy"
    except Exception as e:
        db_status = f"unhealthy: {e}"

    return {
        "status": "online" if db_status == "healthy" else "offline",
        "database_status": db_status,
        "environment": settings.ENVIRONMENT,
        "timestamp": datetime.now().isoformat(),
    }
