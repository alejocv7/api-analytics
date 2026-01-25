from collections import defaultdict
from http import HTTPMethod

from pydantic import AwareDatetime
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from app import models, schemas
from app.core.config import settings
from app.core.security import hash_ip


def add_metric(session: Session, metric_in: schemas.MetricCreate) -> models.Metric:
    """Create a new metric entry."""

    data = metric_in.model_dump()
    if ip := data.pop("ip", None):
        data["ip_hash"] = hash_ip(ip, settings.HASH_SALT)

    metric = models.Metric(**data)

    session.add(metric)
    try:
        session.commit()
    except SQLAlchemyError:
        session.rollback()
        raise
    session.refresh(metric)

    return metric


def get_metrics(
    session: Session, skip: int = 0, limit: int = 100
) -> list[models.Metric]:
    return session.query(models.Metric).offset(skip).limit(limit).all()


def get_metrics_summary(
    session: Session, params: schemas.MetricQuery
) -> schemas.MetricSummaryResponse:
    metrics = (
        session.query(models.Metric)
        .filter(
            models.Metric.project_id == params.project_id,
            models.Metric.timestamp >= params.start_date,
            models.Metric.timestamp <= params.end_date,
        )
        .all()
    )

    if not metrics:
        return schemas.MetricSummaryResponse(
            request_count=0,
            error_count=0,
            avg_response_time_ms=0,
            requests_per_minute=0,
            error_rate=0,
            slowest_request_ms=0,
            fastest_request_ms=0,
        )

    error_count = 0
    total_response_time_ms = 0.0
    slowest_request_ms = float("-inf")
    fastest_request_ms = float("inf")

    for metric in metrics:
        total_response_time_ms += metric.response_time_ms
        error_count += metric.response_status_code >= 400
        slowest_request_ms = max(slowest_request_ms, metric.response_time_ms)
        fastest_request_ms = min(fastest_request_ms, metric.response_time_ms)

    duration_in_minutes = (params.end_date - params.start_date).total_seconds() / 60

    return schemas.MetricSummaryResponse(
        request_count=len(metrics),
        avg_response_time_ms=round(total_response_time_ms / len(metrics), 2),
        requests_per_minute=round(
            len(metrics) / duration_in_minutes if duration_in_minutes > 0 else 0, 2
        ),
        error_count=error_count,
        error_rate=round(error_count / len(metrics) * 100, 2),
        slowest_request_ms=round(slowest_request_ms, 2),
        fastest_request_ms=round(fastest_request_ms, 2),
    )


def get_metrics_time_series(
    session: Session, params: schemas.MetricQuery
) -> list[schemas.MetricTimeSeriesPointResponse]:
    metrics = (
        session.query(models.Metric)
        .filter(
            models.Metric.project_id == params.project_id,
            models.Metric.timestamp >= params.start_date,
            models.Metric.timestamp <= params.end_date,
        )
        .order_by(models.Metric.timestamp.asc())
        .all()
    )

    # Group metrics by timestamp and calculate metrics_time_series
    buckets: dict[AwareDatetime, dict[str, int | float]] = defaultdict(
        lambda: {"request_count": 0, "total_response_time_ms": 0.0, "error_count": 0}
    )

    for metric in metrics:
        timestamp = metric.timestamp.replace(second=0, microsecond=0)
        buckets[timestamp]["request_count"] += 1
        buckets[timestamp]["total_response_time_ms"] += metric.response_time_ms
        buckets[timestamp]["error_count"] += metric.response_status_code >= 400

    metrics_time_series = [
        schemas.MetricTimeSeriesPointResponse(
            timestamp=timestamp,
            request_count=bucket["request_count"],
            avg_response_time_ms=round(
                bucket["total_response_time_ms"] / bucket["request_count"]
                if bucket["request_count"] > 0
                else 0,
                2,
            ),
            error_count=bucket["error_count"],
        )
        for timestamp, bucket in sorted(buckets.items())
    ]

    return metrics_time_series


def get_metrics_endpoints_stats(
    session: Session, params: schemas.MetricQuery
) -> list[schemas.MetricEndpointStatsResponse]:
    metrics = (
        session.query(models.Metric)
        .filter(
            models.Metric.project_id == params.project_id,
            models.Metric.timestamp >= params.start_date,
            models.Metric.timestamp <= params.end_date,
        )
        .all()
    )

    # Group metrics by endpoint and calculate metrics_endpoint_stats
    buckets: dict[tuple[HTTPMethod, str], dict[str, int | float]] = defaultdict(
        lambda: {
            "request_count": 0,
            "total_response_time_ms": 0.0,
            "error_count": 0,
            "slowest_request_ms": float("-inf"),
            "fastest_request_ms": float("inf"),
        }
    )

    for metric in metrics:
        endpoint = (metric.method, metric.url_path)
        buckets[endpoint]["request_count"] += 1
        buckets[endpoint]["total_response_time_ms"] += metric.response_time_ms
        buckets[endpoint]["error_count"] += metric.response_status_code >= 400
        buckets[endpoint]["slowest_request_ms"] = max(
            buckets[endpoint]["slowest_request_ms"], metric.response_time_ms
        )
        buckets[endpoint]["fastest_request_ms"] = min(
            buckets[endpoint]["fastest_request_ms"], metric.response_time_ms
        )

    metrics_endpoint_stats = [
        schemas.MetricEndpointStatsResponse(
            url_path=url_path,
            method=method,
            request_count=bucket["request_count"],
            avg_response_time_ms=round(
                bucket["total_response_time_ms"] / bucket["request_count"]
                if bucket["request_count"] > 0
                else 0,
                2,
            ),
            error_count=bucket["error_count"],
            error_rate=round(
                bucket["error_count"] / bucket["request_count"] * 100
                if bucket["request_count"] > 0
                else 0,
                2,
            ),
            slowest_request_ms=round(bucket["slowest_request_ms"], 2),
            fastest_request_ms=round(bucket["fastest_request_ms"], 2),
        )
        for (method, url_path), bucket in sorted(buckets.items())
    ]

    return metrics_endpoint_stats
