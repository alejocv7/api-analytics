from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class MetricBase(BaseModel):
    project_id: str = Field(..., description="Unique identifier for the project/app")
    url_path: str = Field(..., description="API endpoint path")
    method: str = Field(..., description="HTTP method")
    response_status_code: int = Field(
        ..., ge=100, le=599, description="HTTP status code"
    )
    response_time_ms: float = Field(
        ..., ge=0, description="Response time in milliseconds"
    )
    user_agent: str | None = Field(None, description="User agent string")
    ip_hash: str | None = Field(None, description="Hashed IP address")


class MetricCreate(MetricBase):
    pass


class MetricResponse(MetricBase):
    id: int
    timestamp: datetime
    model_config = ConfigDict(from_attributes=True)
