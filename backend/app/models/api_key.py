from datetime import datetime, timezone

from sqlalchemy import ForeignKey, Index, String, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core import security
from app.models import Base, Project, UTCDateTime


class ApiKey(Base):
    """
    API keys for authentication. One key can access multiple projects.
    """

    __tablename__ = "api_keys"

    id: Mapped[int] = mapped_column(primary_key=True)

    key_hash: Mapped[str] = mapped_column(unique=True, index=True)
    name: Mapped[str] = mapped_column(String(255))

    project_id: Mapped[int] = mapped_column(ForeignKey("projects.id"), index=True)
    project: Mapped["Project"] = relationship(back_populates="api_keys")

    created_at: Mapped[datetime] = mapped_column(
        UTCDateTime(), server_default=func.now()
    )
    expires_at: Mapped[datetime | None] = mapped_column(UTCDateTime())

    last_used_at: Mapped[datetime | None] = mapped_column(UTCDateTime())

    is_active: Mapped[bool] = mapped_column(default=True)

    total_requests: Mapped[int] = mapped_column(default=0)

    __table_args__ = (
        Index("idx_apikey_project_active", "project_id", "is_active"),
        Index("idx_apikey_hash", "key_hash"),
    )

    def __repr__(self):
        return f"ApiKey(id={self.id}, name={self.name}, project_id={self.project_id})"

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
        return security.hash_api_key(plain_key) == hashed_key
