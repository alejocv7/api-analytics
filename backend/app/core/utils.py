from pydantic import BaseModel
from sqlalchemy.orm import DeclarativeBase


def apply_update(model: DeclarativeBase, update: BaseModel) -> None:
    """
    Apply updates from a Pydantic model to a SQLAlchemy model instance.
    Only fields that were explicitly set in the update model are applied.
    """
    for key, value in update.model_dump(exclude_unset=True).items():
        setattr(model, key, value)


def mask_email(email: str) -> str:
    """Mask email for logging (e.g., a***o@example.com)."""
    try:
        user, domain = email.split("@")
        if len(user) <= 2:
            return f"*@{domain}"
        return f"{user[0]}***{user[-1]}@{domain}"
    except ValueError, IndexError:
        return "***"
