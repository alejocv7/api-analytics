from datetime import datetime, timezone
from http import HTTPMethod, HTTPStatus

from sqlalchemy import DateTime, Enum, ForeignKey, Index, TypeDecorator, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

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


class Project(Base):
    """Projects belong to users. Each project represents an app being tracked."""

    __tablename__ = "projects"

    id: Mapped[int] = mapped_column(primary_key=True)

    name: Mapped[str]
    slug: Mapped[str] = mapped_column(unique=True, index=True)
    description: Mapped[str | None]

    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"))
    owner: Mapped["User"] = relationship(back_populates="projects")

    api_keys: Mapped[list["ApiKey"]] = relationship(
        back_populates="project", cascade="all, delete-orphan"
    )

    metrics: Mapped[list["Metric"]] = relationship(
        back_populates="project", cascade="all, delete-orphan"
    )

    created_at: Mapped[datetime] = mapped_column(
        UTCDateTime(), server_default=func.now()
    )

    updated_at: Mapped[datetime] = mapped_column(
        UTCDateTime(), server_onupdate=func.now()
    )

    is_active: Mapped[bool] = mapped_column(default=True)


class User(Base):
    """User accounts - people who sign up for the analytics service."""

    __tablename__ = "users"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)

    email: Mapped[str] = mapped_column(unique=True, index=True)

    hashed_password: Mapped[str]

    full_name: Mapped[str | None]

    is_active: Mapped[bool] = mapped_column(default=True)

    created_at: Mapped[datetime] = mapped_column(
        UTCDateTime(), server_default=func.now()
    )

    projects: Mapped[list["Project"]] = relationship(
        back_populates="owner", cascade="all, delete-orphan"
    )


class ApiKey(Base):
    """
    API keys for authentication. One key can access multiple projects.
    """

    __tablename__ = "api_keys"

    id: Mapped[int] = mapped_column(primary_key=True)

    key_hash: Mapped[str] = mapped_column(unique=True, index=True)
    name: Mapped[str]

    project_id: Mapped[int] = mapped_column(ForeignKey("projects.id"))
    project: Mapped["Project"] = relationship(back_populates="api_keys")

    created_at: Mapped[datetime] = mapped_column(
        UTCDateTime(), server_default=func.now()
    )

    last_used_at: Mapped[datetime | None] = mapped_column(UTCDateTime())

    is_active: Mapped[bool] = mapped_column(default=True)


class Metric(Base):
    """
    Database model for storing API request metrics.
    """

    __tablename__ = "metrics"

    id: Mapped[int] = mapped_column(primary_key=True)

    project_id: Mapped[int] = mapped_column(ForeignKey("projects.id"), index=True)
    project: Mapped["Project"] = relationship(back_populates="metrics")

    url_path: Mapped[str] = mapped_column(index=True)
    method: Mapped[HTTPMethod] = mapped_column(
        Enum(HTTPMethod, name="http_method_enum")
    )
    response_status_code: Mapped[HTTPStatus] = mapped_column(
        Enum(HTTPStatus, name="http_status_enum"), index=True
    )

    response_time_ms: Mapped[float]
    timestamp: Mapped[datetime] = mapped_column(
        UTCDateTime(), server_default=func.now(), index=True
    )

    user_agent: Mapped[str | None]
    ip_hash: Mapped[str | None]

    __table_args__ = (
        Index("idx_project_timestamp", "project_id", "timestamp"),
        Index("idx_project_url_path", "project_id", "url_path"),
        Index("idx_status_timestamp", "response_status_code", "timestamp"),
    )

    def __repr__(self):
        return f"<Metric {self.method} {self.url_path} - {self.response_status_code}>"
