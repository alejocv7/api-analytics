from fastapi import APIRouter

import app.crud as crud
from app import schemas
from app.dependencies import SessionDep

router = APIRouter()


@router.post("/", response_model=schemas.MetricResponse)
async def track_metric(
    metric: schemas.MetricCreate,
    session: SessionDep,
):
    """
    Track an API metric.
    """
    return crud.add_metric(session, metric)
