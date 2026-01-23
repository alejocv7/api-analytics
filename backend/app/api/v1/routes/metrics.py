from typing import Annotated

from fastapi import APIRouter, Query

import app.crud as crud
from app import schemas
from app.dependencies import SessionDep

router = APIRouter()


@router.get("/", response_model=list[schemas.MetricResponse])
async def read_metrics(
    session: SessionDep,
    skip: int = 0,
    limit: int = 100,
):
    """
    Retrieve API metrics.
    """
    return crud.get_metrics(session, skip=skip, limit=limit)


@router.get("/summary", response_model=schemas.MetricSummaryResponse)
async def read_metrics_summary(
    session: SessionDep,
    params: Annotated[schemas.MetricSummaryParams, Query()],
):
    """
    Retrieve API metrics summary.
    """
    return crud.get_metrics_summary(session, params)
