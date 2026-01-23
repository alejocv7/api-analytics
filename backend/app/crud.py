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
    session: Session, params: schemas.MetricSummaryParams
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
