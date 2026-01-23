import hashlib
from datetime import timezone
from http import HTTPMethod, HTTPStatus

from sqlalchemy import DateTime, Float, Index, Integer, String, TypeDecorator, func
from sqlalchemy.ext.hybrid import hybrid_property
from sqlalchemy.orm import Mapped, mapped_column

from app.core.db import Base


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


class Metric(Base):
    """
    Database model for storing API request metrics.
    """

    __tablename__ = "api_metrics"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    project_id: Mapped[str] = mapped_column(String, index=True, nullable=False)
    url_path: Mapped[str] = mapped_column(String, index=True, nullable=False)
    method: Mapped[HTTPMethod] = mapped_column(String, nullable=False)
    response_status_code: Mapped[HTTPStatus] = mapped_column(
        Integer, index=True, nullable=False
    )
    response_time_ms: Mapped[float] = mapped_column(Float, nullable=False)
    timestamp: Mapped[UTCDateTime] = mapped_column(
        UTCDateTime,
        index=True,
        server_default=func.now(),
        nullable=False,
    )
    user_agent: Mapped[str | None] = mapped_column(String, nullable=True)
    # Store hashed IP for privacy
    _ip_hash: Mapped[str | None] = mapped_column("ip_hash", String, nullable=True)

    __table_args__ = (
        Index("idx_project_timestamp", "project_id", "timestamp"),
        Index("idx_project_url_path", "project_id", "url_path"),
        Index("idx_status_timestamp", "response_status_code", "timestamp"),
    )

    def __repr__(self):
        return f"<Metric {self.method} {self.url_path} - {self.response_status_code}>"

    @hybrid_property
    def ip_hash(self):
        return self._ip_hash

    @ip_hash.setter  # type: ignore[no-redef]
    def ip_hash(self, host: str):
        if host is not None:
            self._ip_hash = hashlib.sha256(host.encode()).hexdigest()[:16]
        else:
            self._ip_hash = None
