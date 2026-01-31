from fastapi import APIRouter

from app import schemas
from app.dependencies import CurrentUserDep, SessionDep
from app.schemas import MetricQuery
from app.services import metric_service, project_service

router = APIRouter()


@router.get("/", response_model=list[schemas.MetricResponse])
async def read_metrics(
    project_key: str,
    user: CurrentUserDep,
    session: SessionDep,
    skip: int = 0,
    limit: int = 100,
):
    """
    Retrieve API metrics.
    """
    project = project_service.get_user_project_by_key(user.id, project_key, session)
    return metric_service.get_metrics(session, project.id, skip=skip, limit=limit)


@router.get("/summary", response_model=schemas.MetricSummaryResponse)
async def read_metrics_summary(
    project_key: str,
    user: CurrentUserDep,
    session: SessionDep,
    params: MetricQuery,
):
    """
    Retrieve API metrics summary.
    """
    project = project_service.get_user_project_by_key(user.id, project_key, session)
    return metric_service.get_metrics_summary(session, project.id, params)


@router.get("/time-series", response_model=list[schemas.MetricTimeSeriesPointResponse])
async def read_metrics_time_series(
    project_key: str,
    user: CurrentUserDep,
    session: SessionDep,
    params: MetricQuery,
):
    """
    Retrieve API metrics time series.
    """
    project = project_service.get_user_project_by_key(user.id, project_key, session)
    return metric_service.get_metrics_time_series(session, project.id, params)


@router.get("/endpoints", response_model=list[schemas.MetricEndpointStatsResponse])
async def read_metrics_endpoints_stats(
    project_key: str,
    user: CurrentUserDep,
    session: SessionDep,
    params: MetricQuery,
):
    """
    Retrieve API metrics endpoints.
    """
    project = project_service.get_user_project_by_key(user.id, project_key, session)
    return metric_service.get_metrics_endpoints_stats(session, project.id, params)
