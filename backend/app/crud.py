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
