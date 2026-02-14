from collections.abc import Sequence
from datetime import UTC, datetime, timedelta
from typing import Any

from sqlalchemy import Select, case, delete, func, select
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncSession
from tenacity import retry, stop_after_attempt, wait_exponential

from app import models, schemas
from app.core.config import settings
from app.core.security import hash_ip


@retry(
    stop=stop_after_attempt(3), wait=wait_exponential(multiplier=0.1, min=0.1, max=2)
)
async def add_metric(
    metric_in: schemas.MetricCreate, project_id: int, session: AsyncSession
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
    params: schemas.MetricParams, project_id: int, session: AsyncSession
) -> Sequence[models.Metric]:
    query = select(models.Metric).order_by(models.Metric.timestamp.desc())
    query = _apply_time_range_filter(query, project_id, params)
    query = _apply_pagination(query, params)
    return (await session.scalars(query)).all()


async def count_metrics(
    params: schemas.MetricParams, project_id: int, session: AsyncSession
) -> int:
    """Count raw metrics matching params."""
    query = select(func.count(models.Metric.id))
    query = _apply_time_range_filter(query, project_id, params)
    return (await session.scalar(query)) or 0


async def get_metrics_summary(
    params: schemas.MetricParams, project_id: int, session: AsyncSession
) -> schemas.MetricSummaryResponse:
    query = select(
        func.count(models.Metric.id).label("request_count"),
        func.avg(models.Metric.response_time_ms).label("avg_response_time_ms"),
        _error_count_expr().label("error_count"),
        func.max(models.Metric.response_time_ms).label("slowest_request_ms"),
        func.min(models.Metric.response_time_ms).label("fastest_request_ms"),
    )
    result = (
        await session.execute(_apply_time_range_filter(query, project_id, params))
    ).first()

    if not result or result.request_count == 0:
        return schemas.MetricSummaryResponse(
            request_count=0,
            avg_response_time_ms=0,
            error_count=0,
            error_rate=0,
            slowest_request_ms=0,
            fastest_request_ms=0,
            requests_per_minute=0,
        )

    duration_in_minutes = (params.end_date - params.start_date).total_seconds() / 60
    duration_in_minutes = max(duration_in_minutes, 1)
    error_count = int(result.error_count or 0)

    return schemas.MetricSummaryResponse(
        request_count=result.request_count,
        avg_response_time_ms=round(result.avg_response_time_ms or 0, 2),
        requests_per_minute=round(
            result.request_count / duration_in_minutes
            if duration_in_minutes > 0
            else 0,
            2,
        ),
        error_count=error_count,
        error_rate=round(error_count / result.request_count * 100, 2),
        slowest_request_ms=round(result.slowest_request_ms or 0, 2),
        fastest_request_ms=round(result.fastest_request_ms or 0, 2),
    )


async def get_metrics_time_series(
    params: schemas.MetricTimeSeriesQuery,
    project_id: int,
    session: AsyncSession,
) -> list[schemas.MetricTimeSeriesPointResponse]:
    # Group by granularity. Handling different dialects.

    timestamp: Any = func.date_trunc(params.granularity.value, models.Metric.timestamp)
    query = select(
        timestamp.label("timestamp"),
        func.count(models.Metric.id).label("request_count"),
        func.avg(models.Metric.response_time_ms).label("avg_response_time_ms"),
        _error_count_expr().label("error_count"),
    )
    query = _apply_time_range_filter(query, project_id, params)
    query = query.group_by(timestamp).order_by(timestamp)
    query = _apply_pagination(query, params)

    results = (await session.execute(query)).all()

    metrics_time_series = []
    for row in results:
        ts = row.timestamp
        if isinstance(ts, str):
            ts = datetime.fromisoformat(ts)
        if ts.tzinfo is None:
            ts = ts.replace(UTC)

        metrics_time_series.append(
            schemas.MetricTimeSeriesPointResponse(
                timestamp=ts,
                request_count=row.request_count,
                avg_response_time_ms=round(row.avg_response_time_ms or 0, 2),
                error_count=int(row.error_count or 0),
            )
        )

    return metrics_time_series


async def count_metrics_time_series(
    params: schemas.MetricTimeSeriesQuery,
    project_id: int,
    session: AsyncSession,
) -> int:
    """Count time-series points matching params."""
    timestamp: Any = func.date_trunc(params.granularity.value, models.Metric.timestamp)
    query = select(timestamp)
    query = _apply_time_range_filter(query, project_id, params)
    query = query.group_by(timestamp)

    # Count the number of distinct time buckets
    count_stmt = select(func.count()).select_from(query.subquery())
    return (await session.scalar(count_stmt)) or 0


async def get_metrics_endpoints_stats(
    params: schemas.MetricParams, project_id: int, session: AsyncSession
) -> list[schemas.MetricEndpointStatsResponse]:
    query = select(
        models.Metric.url_path,
        models.Metric.method,
        func.count(models.Metric.id).label("request_count"),
        func.avg(models.Metric.response_time_ms).label("avg_response_time_ms"),
        _error_count_expr().label("error_count"),
        func.max(models.Metric.response_time_ms).label("slowest_request_ms"),
        func.min(models.Metric.response_time_ms).label("fastest_request_ms"),
    )
    query = _apply_time_range_filter(query, project_id, params)
    query = query.group_by(models.Metric.url_path, models.Metric.method)
    query = _apply_pagination(query, params)

    results = (await session.execute(query)).all()

    metrics_endpoint_stats = []
    for row in results:
        error_count = int(row.error_count or 0)
        metrics_endpoint_stats.append(
            schemas.MetricEndpointStatsResponse(
                url_path=row.url_path,
                method=row.method,
                request_count=row.request_count,
                avg_response_time_ms=round(row.avg_response_time_ms or 0, 2),
                error_count=error_count,
                error_rate=round(error_count / row.request_count * 100, 2)
                if row.request_count > 0
                else 0,
                slowest_request_ms=round(row.slowest_request_ms or 0, 2),
                fastest_request_ms=round(row.fastest_request_ms or 0, 2),
            )
        )

    return metrics_endpoint_stats


async def count_metrics_endpoints_stats(
    params: schemas.MetricParams, project_id: int, session: AsyncSession
) -> int:
    """Count distinct endpoints matching params."""
    query = select(models.Metric.url_path, models.Metric.method)
    query = _apply_time_range_filter(query, project_id, params)
    query = query.group_by(models.Metric.url_path, models.Metric.method)

    count_stmt = select(func.count()).select_from(query.subquery())
    return (await session.scalar(count_stmt)) or 0


async def cleanup_old_metrics(session: AsyncSession, retention_days: int = 90) -> int:
    """Delete metrics older than a certain number of days."""
    cutoff = datetime.now(UTC) - timedelta(days=retention_days)
    stmt = delete(models.Metric).where(models.Metric.timestamp < cutoff)
    result = await session.execute(stmt)
    await session.commit()
    return result.rowcount  # type: ignore


def _apply_time_range_filter[T: tuple[Any, ...]](
    query: Select[T], project_id: int, params: schemas.MetricParams
) -> Select[T]:
    """Apply common project_id and time range filters."""
    return query.where(
        models.Metric.project_id == project_id,
        models.Metric.timestamp >= params.start_date,
        models.Metric.timestamp <= params.end_date,
    )


def _apply_pagination[T: tuple[Any, ...]](
    query: Select[T], params: schemas.MetricParams
) -> Select[T]:
    """Apply common pagination (offset/limit) filters."""
    offset = (params.page - 1) * params.page_size
    return query.offset(offset).limit(params.page_size)


def _error_count_expr() -> Any:
    """Common expression for counting errors (status >= 400)."""
    return func.sum(case((models.Metric.response_status_code >= 400, 1), else_=0))
