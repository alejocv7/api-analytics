from fastapi import APIRouter, Request

from app import schemas
from app.core import rate_limits
from app.core.rate_limiter import get_user_key, limiter
from app.dependencies import ProjectDep, SessionDep
from app.services import metric_service

router = APIRouter()


@router.get(
    "/",
    response_model=schemas.MetricListResponse,
    summary="List raw metrics",
    description="""
    Retrieves a list of individual metrics recorded for the project.
    """,
)
@limiter.limit(rate_limits.DATA_READ, key_func=get_user_key)
async def read_metrics(
    request: Request,  # noqa: ARG001
    params: schemas.MetricQuery,
    project: ProjectDep,
    session: SessionDep,
) -> schemas.MetricListResponse:
    items = await metric_service.get_metrics(params, project.id, session)
    total = await metric_service.count_metrics(params, project.id, session)
    return schemas.MetricListResponse(
        items=items,
        total=total,
        page=params.page,
        page_size=params.page_size,
    )


@router.get(
    "/summary",
    response_model=schemas.MetricSummaryResponse,
    summary="Get metrics summary",
    description="""
    Calculates overall performance statistics for the project.
    """,
)
@limiter.limit(rate_limits.DATA_READ, key_func=get_user_key)
async def read_metrics_summary(
    request: Request,  # noqa: ARG001
    params: schemas.MetricQuery,
    project: ProjectDep,
    session: SessionDep,
) -> schemas.MetricSummaryResponse:
    return await metric_service.get_metrics_summary(params, project.id, session)


@router.get(
    "/time-series",
    response_model=schemas.MetricTimeSeriesListResponse,
    summary="Get metrics time series",
    description="""
    Retrieves aggregated metrics grouped by a specified time granularity.
    """,
)
@limiter.limit(rate_limits.DATA_READ, key_func=get_user_key)
async def read_metrics_time_series(
    request: Request,  # noqa: ARG001
    params: schemas.MetricTimeSeriesQuery,
    project: ProjectDep,
    session: SessionDep,
) -> schemas.MetricTimeSeriesListResponse:
    items = await metric_service.get_metrics_time_series(params, project.id, session)
    total = await metric_service.count_metrics_time_series(params, project.id, session)
    return schemas.MetricTimeSeriesListResponse(
        items=items,
        total=total,
        page=params.page,
        page_size=params.page_size,
    )


@router.get(
    "/endpoints",
    response_model=schemas.MetricEndpointStatsListResponse,
    summary="Get endpoint statistics",
    description="""
    Retrieves performance statistics grouped by endpoint (URL path and method).
    """,
)
@limiter.limit(rate_limits.DATA_READ, key_func=get_user_key)
async def read_metrics_endpoints_stats(
    request: Request,  # noqa: ARG001
    params: schemas.MetricQuery,
    project: ProjectDep,
    session: SessionDep,
) -> schemas.MetricEndpointStatsListResponse:
    items = await metric_service.get_metrics_endpoints_stats(
        params, project.id, session
    )
    total = await metric_service.count_metrics_endpoints_stats(
        params, project.id, session
    )
    return schemas.MetricEndpointStatsListResponse(
        items=items,
        total=total,
        page=params.page,
        page_size=params.page_size,
    )
