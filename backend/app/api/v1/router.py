from fastapi import APIRouter

from app.api.v1.routes import metrics, track

router = APIRouter()
router.include_router(metrics.router, prefix="/metrics", tags=["metrics"])
router.include_router(track.router, prefix="/track", tags=["track"])
