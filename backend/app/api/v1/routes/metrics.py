from fastapi import APIRouter

import app.crud as crud
from app import schemas
from app.dependencies import SessionDep
from app.schemas import MetricQuery

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
    params: MetricQuery,
):
    """
    Retrieve API metrics summary.
    """
    return crud.get_metrics_summary(session, params)


@router.get("/time-series", response_model=list[schemas.MetricTimeSeriesPointResponse])
async def read_metrics_time_series(
    session: SessionDep,
    params: MetricQuery,
):
    """
    Retrieve API metrics time series.
    """
    return crud.get_metrics_time_series(session, params)


@router.get("/endpoints", response_model=list[schemas.MetricEndpointStatsResponse])
async def read_metrics_endpoints_stats(
    session: SessionDep,
    params: MetricQuery,
):
    """
    Retrieve API metrics endpoints.
    """
    return crud.get_metrics_endpoints_stats(session, params)
