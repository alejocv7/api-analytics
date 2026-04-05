from fastapi import APIRouter

from app.api.v1.routes.projects import api_keys, members, metrics, projects

_project_key_router = APIRouter(prefix="/projects/{project_key}")
_project_key_router.include_router(api_keys.router)
_project_key_router.include_router(members.router)
_project_key_router.include_router(metrics.router)

router = APIRouter()
router.include_router(projects.router)
router.include_router(_project_key_router)
