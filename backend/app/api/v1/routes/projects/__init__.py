from fastapi import APIRouter

from app.api.v1.routes.projects import metrics

router = APIRouter()
router.include_router(metrics.router, prefix="/metrics", tags=["metrics"])
