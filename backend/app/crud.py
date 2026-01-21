from sqlalchemy.orm import Session

from app import models, schemas


def create_metric(
    session: Session, *, api_metric_in: schemas.APIMetricCreate
) -> models.APIMetric:
    """Create a new metric entry."""

    metric = models.APIMetric(**api_metric_in.model_dump())
    session.add(metric)
    session.commit()
    session.refresh(metric)
    return metric


def get_metrics(
    session: Session, skip: int = 0, limit: int = 100
) -> list[models.APIMetric]:
    return session.query(models.APIMetric).offset(skip).limit(limit).all()
