"""
Database models package.
Exports all models for easy importing.
"""

from datetime import timezone

from sqlalchemy import DateTime, TypeDecorator

from .api_key import ApiKey
from .base import Base
from .metric import Metric
from .project import Project
from .user import User

__all__ = [
    "Base",
    "Metric",
    "Project",
    "User",
    "ApiKey",
]


class UTCDateTime(TypeDecorator):
    impl = DateTime(timezone=True)
    cache_ok = True

    def process_bind_param(self, value, dialect):
        if value is None:
            return value
        if value.tzinfo is None:
            raise ValueError("Naive datetime not allowed")
        return value.astimezone(timezone.utc)

    def process_result_value(self, value, dialect):
        if value is None:
            return value
        if value.tzinfo is None:
            return value.replace(tzinfo=timezone.utc)
        return value.astimezone(timezone.utc)
