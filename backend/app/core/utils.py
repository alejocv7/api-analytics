from datetime import UTC, datetime
from typing import Any

from pydantic import AwareDatetime, BaseModel
from sqlalchemy import true
from sqlalchemy.orm import DeclarativeBase


def normalize_whitespace(name: str) -> str:
    """Collapse all internal whitespace runs to a single space and strip edges."""
    return " ".join(name.split())


def get_default_start_date() -> AwareDatetime:
    return datetime.now(UTC).replace(hour=0, minute=0, second=0, microsecond=0)


def get_default_end_date() -> AwareDatetime:
    return datetime.now(UTC).replace(hour=23, minute=59, second=59, microsecond=999999)


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


def active_filter(model_attr: Any, active_only: bool) -> Any:
    """
    Filter by is_active if active_only is True, otherwise return a true() expression.
    """
    return model_attr.is_(True) if active_only else true()
