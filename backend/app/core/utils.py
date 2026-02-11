from pydantic import BaseModel
from sqlalchemy.orm import DeclarativeBase


def apply_update(model: DeclarativeBase, update: BaseModel) -> None:
    """
    Apply updates from a Pydantic model to a SQLAlchemy model instance.
    Only fields that were explicitly set in the update model are applied.
    """
    for key, value in update.model_dump(exclude_unset=True).items():
        setattr(model, key, value)
