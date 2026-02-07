from fastapi import APIRouter

from app import schemas
from app.dependencies import ProjectDep, SessionDep
from app.services import metric_service

router = APIRouter()


@router.get(
    "/",
    response_model=list[schemas.MetricResponse],
    summary="List raw metrics",
    description="""
    Retrieves a list of individual metrics recorded for the project.
    """,
)
async def read_metrics(
    project: ProjectDep, session: SessionDep, params: schemas.MetricQuery
):
    return await metric_service.get_metrics(session, project.id, params)


@router.get(
    "/summary",
    response_model=schemas.MetricSummaryResponse,
    summary="Get metrics summary",
    description="""
    Calculates overall performance statistics for the project over the specified time range.
    """,
)
async def read_metrics_summary(
    project: ProjectDep, session: SessionDep, params: schemas.MetricQuery
):
    return await metric_service.get_metrics_summary(session, project.id, params)


@router.get(
    "/time-series",
    response_model=list[schemas.MetricTimeSeriesPointResponse],
    summary="Get metrics time series",
    description="""
    Retrieves aggregated metrics grouped by a specified time granularity.
    """,
)
async def read_metrics_time_series(
    project: ProjectDep,
    session: SessionDep,
    params: schemas.MetricQuery,
    granularity: schemas.TimeGranularity = schemas.TimeGranularity.MINUTE,
):
    return await metric_service.get_metrics_time_series(
        session, project.id, params, granularity
    )


@router.get(
    "/endpoints",
    response_model=list[schemas.MetricEndpointStatsResponse],
    summary="Get endpoint statistics",
    description="""
    Retrieves performance statistics grouped by endpoint (URL path and method).
    """,
)
async def read_metrics_endpoints_stats(
    project: ProjectDep, session: SessionDep, params: schemas.MetricQuery
):
    return await metric_service.get_metrics_endpoints_stats(session, project.id, params)
