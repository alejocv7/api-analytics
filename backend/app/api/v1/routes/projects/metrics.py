from fastapi import APIRouter

from app import schemas
from app.dependencies import ProjectIdDep, SessionDep
from app.schemas import MetricQuery
from app.services import metric

router = APIRouter()


@router.get("/", response_model=list[schemas.MetricResponse])
async def read_metrics(
    session: SessionDep,
    project_id: ProjectIdDep,
    skip: int = 0,
    limit: int = 100,
):
    """
    Retrieve API metrics.
    """
    return metric.get_metrics(session, project_id, skip=skip, limit=limit)


@router.get("/summary", response_model=schemas.MetricSummaryResponse)
async def read_metrics_summary(
    params: MetricQuery, session: SessionDep, project_id: ProjectIdDep
):
    """
    Retrieve API metrics summary.
    """
    return metric.get_metrics_summary(session, project_id, params)


@router.get("/time-series", response_model=list[schemas.MetricTimeSeriesPointResponse])
async def read_metrics_time_series(
    params: MetricQuery, session: SessionDep, project_id: ProjectIdDep
):
    """
    Retrieve API metrics time series.
    """
    return metric.get_metrics_time_series(session, project_id, params)


@router.get("/endpoints", response_model=list[schemas.MetricEndpointStatsResponse])
async def read_metrics_endpoints_stats(
    params: MetricQuery, session: SessionDep, project_id: ProjectIdDep
):
    """
    Retrieve API metrics endpoints.
    """
    return metric.get_metrics_endpoints_stats(session, project_id, params)
