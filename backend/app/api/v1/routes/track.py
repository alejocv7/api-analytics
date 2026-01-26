from fastapi import APIRouter, Request

import app.crud.metrics as crud
from app import schemas
from app.core.rate_limiter import limiter
from app.dependencies import ProjectIdDep, SessionDep

router = APIRouter()


@router.post("/", response_model=schemas.MetricResponse)
@limiter.limit("100/minute")
async def track_metric(
    request: Request,
    metric: schemas.MetricCreate,
    session: SessionDep,
    project_id: ProjectIdDep,
):
    """
    Track an API metric.
    """
    return crud.add_metric(session, project_id, metric)
