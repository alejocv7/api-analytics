from fastapi import APIRouter

from app import schemas
from app.dependencies import ProjectDep, SessionDep
from app.schemas import MetricQuery
from app.services import metric_service

router = APIRouter()


@router.get("/", response_model=list[schemas.MetricResponse])
async def read_metrics(
    project: ProjectDep, session: SessionDep, skip: int = 0, limit: int = 100
):
    """
    Retrieve API metrics.
    """
    return metric_service.get_metrics(session, project.id, skip=skip, limit=limit)


@router.get("/summary", response_model=schemas.MetricSummaryResponse)
async def read_metrics_summary(
    project: ProjectDep, session: SessionDep, params: MetricQuery
):
    """
    Retrieve API metrics summary.
    """
    return metric_service.get_metrics_summary(session, project.id, params)


@router.get("/time-series", response_model=list[schemas.MetricTimeSeriesPointResponse])
async def read_metrics_time_series(
    project: ProjectDep, session: SessionDep, params: MetricQuery
):
    """
    Retrieve API metrics time series.
    """
    return metric_service.get_metrics_time_series(session, project.id, params)


@router.get("/endpoints", response_model=list[schemas.MetricEndpointStatsResponse])
async def read_metrics_endpoints_stats(
    project: ProjectDep, session: SessionDep, params: MetricQuery
):
    """
    Retrieve API metrics endpoints.
    """
    return metric_service.get_metrics_endpoints_stats(session, project.id, params)
