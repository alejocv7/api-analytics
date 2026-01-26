from collections import defaultdict
from dataclasses import dataclass
from http import HTTPMethod

from pydantic import AwareDatetime
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from app import models, schemas
from app.core.config import settings
from app.core.security import hash_ip


@dataclass
class MetricAggregator:
    request_count: int = 0
    total_response_time_ms: float = 0.0
    error_count: int = 0
    _slowest_request_ms: float = float("-inf")
    _fastest_request_ms: float = float("inf")

    def add(self, metric: models.Metric) -> None:
        self.request_count += 1
        self.total_response_time_ms += metric.response_time_ms
        self.error_count += metric.response_status_code >= 400
        self._slowest_request_ms = max(
            self._slowest_request_ms, metric.response_time_ms
        )
        self._fastest_request_ms = min(
            self._fastest_request_ms, metric.response_time_ms
        )

    @property
    def avg_response_time_ms(self) -> float:
        if self.request_count == 0:
            return 0.0
        return round(self.total_response_time_ms / self.request_count, 2)

    @property
    def error_rate(self) -> float:
        if self.request_count == 0:
            return 0.0
        return round(self.error_count / self.request_count * 100, 2)

    @property
    def slowest_request_ms(self) -> float:
        if self._slowest_request_ms == float("-inf"):
            return 0.0
        return round(self._slowest_request_ms, 2)

    @property
    def fastest_request_ms(self) -> float:
        if self._fastest_request_ms == float("inf"):
            return 0.0
        return round(self._fastest_request_ms, 2)


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

    aggregator = MetricAggregator()
    for metric in metrics:
        aggregator.add(metric)

    duration_in_minutes = (params.end_date - params.start_date).total_seconds() / 60

    return schemas.MetricSummaryResponse(
        request_count=aggregator.request_count,
        avg_response_time_ms=aggregator.avg_response_time_ms,
        requests_per_minute=round(
            aggregator.request_count / duration_in_minutes
            if duration_in_minutes > 0
            else 0,
            2,
        ),
        error_count=aggregator.error_count,
        error_rate=aggregator.error_rate,
        slowest_request_ms=aggregator.slowest_request_ms,
        fastest_request_ms=aggregator.fastest_request_ms,
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
    buckets: dict[AwareDatetime, MetricAggregator] = defaultdict(MetricAggregator)
    for metric in metrics:
        timestamp = metric.timestamp.replace(second=0, microsecond=0)
        buckets[timestamp].add(metric)

    metrics_time_series = [
        schemas.MetricTimeSeriesPointResponse(
            timestamp=timestamp,
            request_count=bucket.request_count,
            avg_response_time_ms=bucket.avg_response_time_ms,
            error_count=bucket.error_count,
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
    buckets: dict[tuple[HTTPMethod, str], MetricAggregator] = defaultdict(
        MetricAggregator
    )

    for metric in metrics:
        endpoint = (metric.method, metric.url_path)
        buckets[endpoint].add(metric)

    metrics_endpoint_stats = [
        schemas.MetricEndpointStatsResponse(
            url_path=url_path,
            method=method,
            request_count=bucket.request_count,
            avg_response_time_ms=bucket.avg_response_time_ms,
            error_count=bucket.error_count,
            error_rate=bucket.error_rate,
            slowest_request_ms=bucket.slowest_request_ms,
            fastest_request_ms=bucket.fastest_request_ms,
        )
        for (method, url_path), bucket in sorted(buckets.items())
    ]

    return metrics_endpoint_stats
