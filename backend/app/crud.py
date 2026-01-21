from sqlalchemy.orm import Session

from app import models, schemas


def create_metric(
    db: Session, *, api_metric_in: schemas.APIMetricCreate
) -> models.APIMetric:
    """Create a new metric entry."""
    db_metric = models.APIMetric(**api_metric_in.model_dump())
    db.add(db_metric)
    db.commit()
    db.refresh(db_metric)
    return db_metric


def get_metrics(db: Session, skip: int = 0, limit: int = 100):
    return db.query(models.APIMetric).offset(skip).limit(limit).all()
