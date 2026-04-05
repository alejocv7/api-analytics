from fastapi import APIRouter

from app.api.v1.routes import auth, projects, track, users

router = APIRouter()
router.include_router(auth.router)
router.include_router(users.router)
router.include_router(projects.router)
router.include_router(track.router)
