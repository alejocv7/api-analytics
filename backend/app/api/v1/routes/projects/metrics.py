from fastapi import APIRouter, Request

from app import schemas
from app.core import rate_limits
from app.core.rate_limiter import get_user_key, limiter
from app.dependencies import ProjectDep, SessionDep
from app.services import metric_service

router = APIRouter(prefix="/metrics", tags=["metrics"])


@router.get(
    "",
    response_model=schemas.MetricListResponse,
    summary="List raw metrics",
    description="Retrieves a list of individual metrics recorded for the project.",
    responses={
        401: {"model": schemas.ErrorResponse, "description": "Not authenticated"},
        403: {"model": schemas.ErrorResponse, "description": "Not enough permissions"},
        404: {"model": schemas.ErrorResponse, "description": "Project not found"},
        429: {"model": schemas.ErrorResponse, "description": "Rate limit exceeded"},
    },
)
@limiter.limit(rate_limits.DATA_READ, key_func=get_user_key)
async def get_metrics(
    params: schemas.MetricQuery,
    project: ProjectDep,
    session: SessionDep,
    request: Request,  # noqa: ARG001
) -> schemas.MetricListResponse:
    """Get raw metrics for a project."""
    result = await metric_service.get_metrics(params, project.id, session)
    return schemas.MetricListResponse.from_result(result)


@router.get(
    "/summary",
    response_model=schemas.MetricSummaryResponse,
    summary="Get metrics summary",
    description="""
    Calculates overall performance statistics for the project.
    """,
    responses={
        401: {"model": schemas.ErrorResponse, "description": "Not authenticated"},
        403: {"model": schemas.ErrorResponse, "description": "Not enough permissions"},
        404: {"model": schemas.ErrorResponse, "description": "Project not found"},
        429: {"model": schemas.ErrorResponse, "description": "Rate limit exceeded"},
    },
)
@limiter.limit(rate_limits.DATA_READ, key_func=get_user_key)
async def read_metrics_summary(
    params: schemas.MetricQuery,
    project: ProjectDep,
    session: SessionDep,
    request: Request,  # noqa: ARG001
) -> schemas.MetricSummaryResponse:
    return await metric_service.get_metrics_summary(params, project.id, session)


@router.get(
    "/time-series",
    response_model=schemas.MetricTimeSeriesListResponse,
    responses={
        401: {"model": schemas.ErrorResponse, "description": "Not authenticated"},
        403: {"model": schemas.ErrorResponse, "description": "Not enough permissions"},
        404: {"model": schemas.ErrorResponse, "description": "Project not found"},
        429: {"model": schemas.ErrorResponse, "description": "Rate limit exceeded"},
    },
)
@limiter.limit(rate_limits.DATA_READ, key_func=get_user_key)
async def get_metrics_time_series(
    params: schemas.MetricTimeSeriesQuery,
    project: ProjectDep,
    session: SessionDep,
    request: Request,  # noqa: ARG001
) -> schemas.MetricTimeSeriesListResponse:
    """Get metric time series (aggregated requests by granularity)."""
    result = await metric_service.get_metrics_time_series(params, project.id, session)
    return schemas.MetricTimeSeriesListResponse.from_result(result)


@router.get(
    "/endpoints",
    response_model=schemas.MetricEndpointStatsListResponse,
    responses={
        401: {"model": schemas.ErrorResponse, "description": "Not authenticated"},
        403: {"model": schemas.ErrorResponse, "description": "Not enough permissions"},
        404: {"model": schemas.ErrorResponse, "description": "Project not found"},
        429: {"model": schemas.ErrorResponse, "description": "Rate limit exceeded"},
    },
)
@limiter.limit(rate_limits.DATA_READ, key_func=get_user_key)
async def get_metrics_endpoints_stats(
    params: schemas.MetricEndpointStatsQuery,
    project: ProjectDep,
    session: SessionDep,
    request: Request,  # noqa: ARG001
) -> schemas.MetricEndpointStatsListResponse:
    """Get metrics grouped by endpoint (path and method)."""
    result = await metric_service.get_metrics_endpoints_stats(
        params, project.id, session
    )
    return schemas.MetricEndpointStatsListResponse.from_result(result)
