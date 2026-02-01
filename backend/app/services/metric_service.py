from datetime import datetime, timezone
from typing import Sequence

from sqlalchemy import case, func, select
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
    session: AsyncSession, project_id: int, metric_in: schemas.MetricCreate
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
    session: AsyncSession, project_id: int, skip: int = 0, limit: int = 100
) -> Sequence[models.Metric]:
    result = await session.execute(
        select(models.Metric)
        .filter(models.Metric.project_id == project_id)
        .offset(skip)
        .limit(limit)
    )
    return result.scalars().all()


async def get_metrics_summary(
    session: AsyncSession, project_id: int, params: schemas.MetricQuery
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
            error_count=0,
            avg_response_time_ms=0,
            requests_per_minute=0,
            error_rate=0,
            slowest_request_ms=0,
            fastest_request_ms=0,
        )

    duration_in_minutes = (params.end_date - params.start_date).total_seconds() / 60
    duration_in_minutes = max(duration_in_minutes, 1)  # Ensure at least 1 minute
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
    session: AsyncSession,
    project_id: int,
    params: schemas.MetricQuery
) -> list[schemas.MetricTimeSeriesPointResponse]:
    # Group by minute. Handling different dialects.
    dialect = session.get_bind().dialect.name
    if dialect == "sqlite":
        # SQLite: use strftime to group by minute
        timestamp = func.strftime("%Y-%m-%dT%H:%M:00", models.Metric.timestamp)
    else:
        # Default/PostgreSQL: use date_trunc
        timestamp = func.date_trunc("minute", models.Metric.timestamp)

    query = select(
        timestamp.label("timestamp"),
        func.count(models.Metric.id).label("request_count"),
        func.avg(models.Metric.response_time_ms).label("avg_response_time_ms"),
        _error_count_expr().label("error_count"),
    )
    results = (
        await session.execute(
            _apply_pagination(
                _apply_time_range_filter(query, project_id, params), params
            )
            .group_by(timestamp)
            .order_by(timestamp)
        )
    ).all()

    metrics_time_series = []
    for row in results:
        ts = row.timestamp
        if isinstance(ts, str):
            ts = datetime.fromisoformat(ts)
        if ts.tzinfo is None:
            ts = ts.replace(tzinfo=timezone.utc)

        metrics_time_series.append(
            schemas.MetricTimeSeriesPointResponse(
                timestamp=ts,
                request_count=row.request_count,
                avg_response_time_ms=round(row.avg_response_time_ms or 0, 2),
                error_count=int(row.error_count or 0),
            )
        )

    return metrics_time_series


async def get_metrics_endpoints_stats(
    session: AsyncSession, project_id: int, params: schemas.MetricQuery
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
    results = (
        await session.execute(
            _apply_pagination(
                _apply_time_range_filter(query, project_id, params), params
            ).group_by(models.Metric.url_path, models.Metric.method)
        )
    ).all()

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


def _apply_time_range_filter(query, project_id: int, params: schemas.MetricQuery):
    """Apply common project_id and time range filters."""
    return query.filter(
        models.Metric.project_id == project_id,
        models.Metric.timestamp >= params.start_date,
        models.Metric.timestamp <= params.end_date,
    )


def _apply_pagination(query, params: schemas.MetricParams):
    """Apply common pagination (offset/limit) filters."""
    offset = (params.page - 1) * params.page_size
    return query.offset(offset).limit(params.page_size)


def _error_count_expr():
    """Common expression for counting errors (status >= 400)."""
    return func.sum(case((models.Metric.response_status_code >= 400, 1), else_=0))
