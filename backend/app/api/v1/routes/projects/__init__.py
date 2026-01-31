from fastapi import APIRouter

from app.api.v1.routes.projects import api_keys, metrics, projects

router = APIRouter()
router.include_router(projects.router, tags=["projects"])
router.include_router(metrics.router, prefix="/{project_key}/metrics", tags=["metrics"])
router.include_router(
    api_keys.router, prefix="/{project_key}/api-keys", tags=["api-keys"]
)
