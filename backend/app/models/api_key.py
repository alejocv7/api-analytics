from datetime import datetime, timedelta, timezone

from sqlalchemy import ForeignKey, Index, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core import security
from app.core.config import settings
from app.models.base import Base, TimestampMixin
from app.models.project import Project


class APIKey(Base, TimestampMixin):
    """
    API Key model.

    API keys are used to authenticate applications sending metrics.
    Each project can have multiple API keys (e.g., production, staging).
    """

    __tablename__ = "api_keys"

    id: Mapped[int] = mapped_column(primary_key=True)

    key_hash: Mapped[str] = mapped_column(unique=True, index=True)
    name: Mapped[str] = mapped_column(String(255))

    project_id: Mapped[int] = mapped_column(ForeignKey("projects.id"), index=True)
    project: Mapped["Project"] = relationship(back_populates="api_keys")

    expires_at: Mapped[datetime] = mapped_column(
        default=lambda: datetime.now(timezone.utc)
        + timedelta(days=settings.API_KEY_DEFAULT_EXPIRY_DAYS)
    )

    last_used_at: Mapped[datetime | None]

    is_active: Mapped[bool] = mapped_column(default=True)

    total_requests: Mapped[int] = mapped_column(default=0)

    __table_args__ = (
        Index("idx_apikey_project_active", "project_id", "is_active"),
        Index("idx_apikey_hash", "key_hash"),
    )

    def __repr__(self):
        return f"ApiKey(id={self.id}, name={self.name}, project_id={self.project_id})"

    @classmethod
    def new_key(
        cls, name: str, project_id: int, expires_at: datetime | None = None
    ) -> tuple["APIKey", str]:
        """
        Create a new API key.

        Args:
            name: Name of the API key
            project_id: ID of the project
            expires_at: Expiration date of the API key

        Returns:
            Tuple of (API key, full key)
        """

        plain_key, key_hash = security.generate_api_key()
        api_key = cls(
            key_hash=key_hash, name=name, project_id=project_id, expires_at=expires_at
        )

        return api_key, plain_key

    @property
    def is_expired(self) -> bool:
        if not self.expires_at:
            return False
        return self.expires_at < datetime.now(tz=timezone.utc)

    @property
    def is_valid(self) -> bool:
        return self.is_active and not self.is_expired

    def record_usage(self):
        self.total_requests += 1
        self.last_used_at = datetime.now(tz=timezone.utc)

    @staticmethod
    def verify_key(plain_key: str, hashed_key: str) -> bool:
        """
        Verify a plain API key against a hashed key.

        Args:
            plain_key: The plain text API key
            hashed_key: The hashed key from database

        Returns:
            True if keys match
        """
        return security.compare_api_key(plain_key, hashed_key)
