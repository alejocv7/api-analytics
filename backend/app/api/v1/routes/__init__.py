from fastapi import APIRouter

from app.api.v1.routes import auth, projects, track, users

router = APIRouter()
router.include_router(track.router, prefix="/track", tags=["track"])
router.include_router(auth.router, prefix="/auth", tags=["auth"])
router.include_router(users.router, prefix="/users", tags=["users"])
router.include_router(projects.router, prefix="/projects", tags=["projects"])
