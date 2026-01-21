import hashlib

from sqlalchemy import Column, DateTime, Float, Index, Integer, String
from sqlalchemy.ext.hybrid import hybrid_property
from sqlalchemy.sql import func

from app.core.db import Base


class Metric(Base):
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
    _ip_hash = Column("ip_hash", String, nullable=True)  # Store hashed IP for privacy

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
