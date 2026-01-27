from fastapi import APIRouter

from app.api.v1.routes import auth, metrics, track, users

router = APIRouter()
router.include_router(metrics.router, prefix="/metrics", tags=["metrics"])
router.include_router(track.router, prefix="/track", tags=["track"])
router.include_router(auth.router, prefix="/auth", tags=["auth"])
router.include_router(users.router, prefix="/users", tags=["users"])
