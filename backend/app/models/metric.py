import uuid
from datetime import datetime
from http import HTTPMethod
from typing import TYPE_CHECKING

from sqlalchemy import Enum, ForeignKey, Index, String, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base

if TYPE_CHECKING:
    from app.models.project import Project


class Metric(Base):
    """
    Database model for storing API request metrics.
    """

    __tablename__ = "metrics"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)

    project_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("projects.id", ondelete="CASCADE")
    )
    project: Mapped[Project] = relationship(back_populates="metrics")

    url_path: Mapped[str] = mapped_column(String(2048))
    method: Mapped[HTTPMethod] = mapped_column(
        Enum(HTTPMethod, name="http_method_enum")
    )

    response_status_code: Mapped[int] = mapped_column()

    response_time_ms: Mapped[float]
    timestamp: Mapped[datetime] = mapped_column(server_default=func.now(), index=True)

    user_agent: Mapped[str | None] = mapped_column(String(512))
    ip_hash: Mapped[str | None]

    __table_args__ = (
        Index("idx_project_timestamp", "project_id", "timestamp"),
        Index("idx_project_url_method", "project_id", "url_path", "method"),
    )

    def __repr__(self) -> str:
        return f"<Metric {self.method} {self.url_path} - {self.response_status_code}>"
