import uuid
from datetime import UTC, datetime, timedelta
from typing import Any

from sqlalchemy import (
    ColumnElement,
    Select,
    asc,
    case,
    delete,
    desc,
    func,
    select,
    tuple_,
)
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncSession
from tenacity import retry, stop_after_attempt, wait_exponential

from app import models, schemas
from app.core.config import settings
from app.core.security import hash_ip


@retry(
    stop=stop_after_attempt(3),
    wait=wait_exponential(multiplier=0.1, min=0.1, max=2),
    reraise=True,
)
async def add_metric(
    metric_in: schemas.MetricCreate, project_id: uuid.UUID, session: AsyncSession
) -> models.Metric:
    """Create a new metric entry."""

    data = metric_in.model_dump()
    data["project_id"] = project_id

    if ip := data.pop("ip", None):
        data["ip_hash"] = hash_ip(ip, settings.SECURITY_KEY)

    metric = models.Metric(**data)

    session.add(metric)
    try:
        await session.commit()
    except SQLAlchemyError:
        await session.rollback()
        raise
    await session.refresh(metric)

    return metric


async def get_metrics(
    params: schemas.MetricParams, project_id: uuid.UUID, session: AsyncSession
) -> schemas.PaginatedResult[models.Metric]:
    """Get raw metrics with total count."""

    # Count query
    count_query = _with_time_filter(
        select(func.count(models.Metric.id)), project_id, params
    )
    total = await session.scalar(count_query)

    # Items query
    items_query = (
        _with_time_filter(select(models.Metric), project_id, params)
        .order_by(models.Metric.timestamp.desc())
        .offset(params.offset)
        .limit(params.page_size)
    )

    items = (await session.scalars(items_query)).all()

    return schemas.PaginatedResult(items=items, total=total, pagination=params)


async def get_metrics_summary(
    params: schemas.MetricParams, project_id: uuid.UUID, session: AsyncSession
) -> schemas.MetricSummaryResponse:
    query = _with_time_filter(
        select(
            func.count(models.Metric.id).label("request_count"),
            func.avg(models.Metric.response_time_ms).label("avg_response_time_ms"),
            func.max(models.Metric.response_time_ms).label("slowest_request_ms"),
            func.min(models.Metric.response_time_ms).label("fastest_request_ms"),
            _error_count_expr().label("error_count"),
        ),
        project_id,
        params,
    )

    result = await session.execute(query)
    return schemas.MetricSummaryResponse.from_raw(result.first(), params)


async def get_metrics_time_series(
    params: schemas.MetricTimeSeriesQuery,
    project_id: uuid.UUID,
    session: AsyncSession,
) -> schemas.PaginatedResult[schemas.MetricTimeSeriesPointResponse]:
    """Get metric time series with total count."""
    timestamp: ColumnElement[datetime] = func.date_trunc(
        params.granularity.value, models.Metric.timestamp
    ).label("timestamp")

    # Count distinct time buckets
    count_query = _with_time_filter(
        select(func.count(func.distinct(timestamp))),
        project_id,
        params,
    )
    total = await session.scalar(count_query)

    # Items query
    items_query = (
        _with_time_filter(
            select(
                timestamp,
                func.count(models.Metric.id).label("request_count"),
                func.avg(models.Metric.response_time_ms).label("avg_response_time_ms"),
                _error_count_expr().label("error_count"),
            ),
            project_id,
            params,
        )
        .group_by(timestamp)
        .order_by(timestamp)
        .offset(params.offset)
        .limit(params.page_size)
    )

    results = (await session.execute(items_query)).all()
    items = [
        schemas.MetricTimeSeriesPointResponse.model_validate(row) for row in results
    ]

    return schemas.PaginatedResult(items=items, total=total, pagination=params)


async def get_metrics_endpoints_stats(
    params: schemas.MetricEndpointStatsParams,
    project_id: uuid.UUID,
    session: AsyncSession,
) -> schemas.PaginatedResult[schemas.MetricEndpointStatsResponse]:
    """Get metrics grouped by endpoint with total count."""

    # ---- Aggregates ----
    M = models.Metric

    stats: dict[str, Any] = {
        "request_count": func.count(M.id),
        "avg_response_time_ms": func.avg(M.response_time_ms),
        "slowest_request_ms": func.max(M.response_time_ms),
        "fastest_request_ms": func.min(M.response_time_ms),
        "error_count": _error_count_expr(),
    }

    safe_request_count = func.nullif(stats["request_count"] * 1.0, 0)
    stats["error_rate"] = stats["error_count"] / safe_request_count * 100
    stats = {k: v.label(k) for k, v in stats.items()}

    # ---- Sort ----
    sort_col = stats.get(params.sort_by.value, stats["request_count"])
    order_by = desc(sort_col) if params.sort_order == "desc" else asc(sort_col)

    # Count distinct endpoints
    count_query = _with_time_filter(
        select(func.count(func.distinct(tuple_(M.url_path, M.method)))),
        project_id,
        params,
    )
    total = await session.scalar(count_query)

    # Items query
    items_query = (
        _with_time_filter(
            select(M.url_path, M.method, *stats.values()),
            project_id,
            params,
        )
        .group_by(M.url_path, M.method)
        .order_by(order_by.nulls_last())
        .offset(params.offset)
        .limit(params.page_size)
    )

    results = (await session.execute(items_query)).all()
    items = [schemas.MetricEndpointStatsResponse.model_validate(row) for row in results]

    return schemas.PaginatedResult(items=items, total=total, pagination=params)


async def cleanup_old_metrics(session: AsyncSession, retention_days: int = 90) -> int:
    """Delete metrics older than a certain number of days."""
    cutoff = datetime.now(UTC) - timedelta(days=retention_days)
    stmt = delete(models.Metric).where(models.Metric.timestamp < cutoff)
    result = await session.execute(stmt)
    await session.commit()
    return result.rowcount  # type: ignore


def _with_time_filter[T: tuple[Any, ...]](
    query: Select[T], project_id: uuid.UUID, params: schemas.MetricParams
) -> Select[T]:
    """Apply common project_id and time range filters."""
    return query.where(
        models.Metric.project_id == project_id,
        models.Metric.timestamp >= params.start_date,
        models.Metric.timestamp <= params.end_date,
    )


def _error_count_expr() -> ColumnElement[int]:
    """Common expression for counting errors (status >= 400)."""
    return func.sum(case((models.Metric.response_status_code >= 400, 1), else_=0))
