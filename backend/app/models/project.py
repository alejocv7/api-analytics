from datetime import datetime

from sqlalchemy import ForeignKey, Index, String, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models import ApiKey, Base, Metric, User, UTCDateTime


class Project(Base):
    """Projects belong to users. Each project represents an app being tracked."""

    __tablename__ = "projects"

    id: Mapped[int] = mapped_column(primary_key=True)

    name: Mapped[str] = mapped_column(String(255))
    slug: Mapped[str] = mapped_column(String(255), unique=True, index=True)
    description: Mapped[str | None] = mapped_column(String(1000))

    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), index=True)
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

    __table_args__ = (
        Index("idx_project_slug", "slug"),
        Index("idx_project_user_active", "user_id", "is_active"),
    )
