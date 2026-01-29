from datetime import datetime
from http import HTTPMethod, HTTPStatus

from sqlalchemy import Enum, ForeignKey, Index, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models import Base, Project


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
        Enum(HTTPMethod, name="http_method_enum"), index=True
    )
    response_status_code: Mapped[HTTPStatus] = mapped_column(
        Enum(HTTPStatus, name="http_status_enum"), index=True
    )

    response_time_ms: Mapped[float]
    timestamp: Mapped[datetime] = mapped_column(server_default=func.now(), index=True)

    user_agent: Mapped[str | None]
    ip_hash: Mapped[str | None]

    __table_args__ = (
        Index("idx_project_timestamp", "project_id", "timestamp"),
        Index("idx_project_url_path", "project_id", "url_path"),
        Index("idx_project_method", "project_id", "method"),
        Index("idx_project_status_code", "project_id", "response_status_code"),
        Index("idx_status_timestamp", "response_status_code", "timestamp"),
    )

    def __repr__(self):
        return f"<Metric {self.method} {self.url_path} - {self.response_status_code}>"
