from collections.abc import Sequence

from fastapi import APIRouter

from app import models, schemas
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
    params: schemas.MetricQuery, project: ProjectDep, session: SessionDep
) -> Sequence[models.Metric]:
    return await metric_service.get_metrics(params, project.id, session)


@router.get(
    "/summary",
    response_model=schemas.MetricSummaryResponse,
    summary="Get metrics summary",
    description="""
    Calculates overall performance statistics for the project.
    """,
)
async def read_metrics_summary(
    params: schemas.MetricQuery, project: ProjectDep, session: SessionDep
) -> schemas.MetricSummaryResponse:
    return await metric_service.get_metrics_summary(params, project.id, session)


@router.get(
    "/time-series",
    response_model=list[schemas.MetricTimeSeriesPointResponse],
    summary="Get metrics time series",
    description="""
    Retrieves aggregated metrics grouped by a specified time granularity.
    """,
)
async def read_metrics_time_series(
    params: schemas.MetricTimeSeriesQuery,
    project: ProjectDep,
    session: SessionDep,
) -> list[schemas.MetricTimeSeriesPointResponse]:
    return await metric_service.get_metrics_time_series(params, project.id, session)


@router.get(
    "/endpoints",
    response_model=list[schemas.MetricEndpointStatsResponse],
    summary="Get endpoint statistics",
    description="""
    Retrieves performance statistics grouped by endpoint (URL path and method).
    """,
)
async def read_metrics_endpoints_stats(
    params: schemas.MetricQuery, project: ProjectDep, session: SessionDep
) -> list[schemas.MetricEndpointStatsResponse]:
    return await metric_service.get_metrics_endpoints_stats(params, project.id, session)
