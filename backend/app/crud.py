from sqlalchemy.orm import Session

from app import models, schemas


def add_metric(session: Session, *, metric_in: schemas.MetricCreate) -> models.Metric:
    """Create a new metric entry."""

    metric = models.Metric(**metric_in.model_dump())
    session.add(metric)
    session.commit()
    session.refresh(metric)
    return metric


def get_metrics(
    session: Session, skip: int = 0, limit: int = 100
) -> list[models.Metric]:
    return session.query(models.Metric).offset(skip).limit(limit).all()
