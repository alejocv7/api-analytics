from sqlalchemy import Column, DateTime, Float, Index, Integer, String
from sqlalchemy.sql import func

from app.core.db import Base


class APIMetric(Base):
    """
    Database model for storing API request metrics.
    """

    __tablename__ = "api_metrics"

    id = Column(Integer, primary_key=True, index=True)
    project_id = Column(String, index=True, nullable=False)
    url_path = Column(String, index=True, nullable=False)
    method = Column(String, nullable=False)  # GET, POST, PUT, DELETE, etc.
    response_status_code = Column(Integer, index=True, nullable=False)
    response_time_ms = Column(Float, nullable=False)
    timestamp = Column(
        DateTime(timezone=True), index=True, server_default=func.now(), nullable=False
    )
    user_agent = Column(String, nullable=True)
    ip_hash = Column(String, nullable=True)  # Store hashed IP for privacy

    __table_args__ = (
        Index("idx_project_timestamp", "project_id", "timestamp"),
        Index("idx_project_url_path", "project_id", "url_path"),
        Index("idx_status_timestamp", "response_status_code", "timestamp"),
    )

    def __repr__(self):
        return (
            f"<APIMetric {self.method} {self.url_path} - {self.response_status_code}>"
        )
