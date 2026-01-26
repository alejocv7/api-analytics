from datetime import datetime, timedelta, timezone
from http import HTTPMethod, HTTPStatus
from typing import Annotated, Self

from fastapi import Query
from pydantic import (
    AfterValidator,
    AwareDatetime,
    BaseModel,
    ConfigDict,
    Field,
    model_validator,
)


def normalize_url_path(url_path: str) -> str:
    if not url_path.startswith("/"):
        raise ValueError("url_path must start with '/'")
    return url_path.rstrip("/") or "/"


def get_default_start_date() -> AwareDatetime:
    return datetime.now(timezone.utc).replace(hour=0, minute=0, second=0, microsecond=0)


def get_default_end_date() -> AwareDatetime:
    return datetime.now(timezone.utc).replace(
        hour=23, minute=59, second=59, microsecond=999999
    )


class MetricBase(BaseModel):
    url_path: Annotated[str, AfterValidator(normalize_url_path)] = Field(
        ..., description="API endpoint path"
    )

    method: HTTPMethod = Field(..., description="HTTP method")
    response_status_code: HTTPStatus = Field(..., description="HTTP status code")
    response_time_ms: float = Field(
        ..., ge=0, le=120_000, description="Response time in milliseconds"
    )
    user_agent: str | None = Field(None, description="User agent string")


class MetricCreate(MetricBase):
    ip: str | None = Field(
        None, description="Raw IP address (will be hashed by server)"
    )


class MetricResponse(MetricBase):
    id: int
    timestamp: AwareDatetime
    ip_hash: str | None = Field(None, description="Hashed IP address")
    model_config = ConfigDict(from_attributes=True)


class MetricSummaryResponse(BaseModel):
    """Schema for summary statistics."""

    request_count: int = Field(..., description="Number of requests")
    avg_response_time_ms: float = Field(
        ..., description="Average response time in milliseconds"
    )
    requests_per_minute: float = Field(..., description="Requests per minute")
    error_count: int = Field(..., description="Number of errors")
    error_rate: float = Field(
        ..., description="Percentage of requests with status >= 400"
    )
    slowest_request_ms: float = Field(
        ..., description="Slowest request in milliseconds"
    )
    fastest_request_ms: float = Field(
        ..., description="Fastest request in milliseconds"
    )


class MetricTimeSeriesPointResponse(BaseModel):
    timestamp: AwareDatetime = Field(..., description="Timestamp")
    request_count: int = Field(..., description="Number of requests")
    avg_response_time_ms: float = Field(
        ..., description="Average response time in milliseconds"
    )
    error_count: int = Field(..., description="Number of errors")


class MetricEndpointStatsResponse(BaseModel):
    url_path: str = Field(..., description="API endpoint path")
    method: HTTPMethod = Field(..., description="HTTP method")
    request_count: int = Field(..., description="Number of requests")
    avg_response_time_ms: float = Field(
        ..., description="Average response time in milliseconds"
    )
    error_count: int = Field(..., description="Number of errors")
    error_rate: float = Field(
        ..., description="Percentage of requests with status >= 400"
    )
    slowest_request_ms: float = Field(
        ..., description="Slowest request in milliseconds"
    )
    fastest_request_ms: float = Field(
        ..., description="Fastest request in milliseconds"
    )


class MetricParams(BaseModel):
    start_date: AwareDatetime = Field(
        default_factory=get_default_start_date,
        description="Start date (defaults to beginning of today)",
    )
    end_date: AwareDatetime = Field(
        default_factory=get_default_end_date,
        description="End date (defaults to end of today)",
    )

    @model_validator(mode="after")
    def validate_dates(self) -> Self:
        self.start_date = self.start_date.astimezone(timezone.utc)
        self.end_date = self.end_date.astimezone(timezone.utc)

        if self.end_date < self.start_date:
            raise ValueError("end_date cannot be before start_date")

        if self.end_date - self.start_date > timedelta(days=60):
            raise ValueError("Date range must be 60 days or less")

        if self.end_date - self.start_date < timedelta(minutes=1):
            raise ValueError("Date range must be at least 1 minute")

        # Truncate to the minute
        self.start_date = self.start_date.replace(second=0, microsecond=0)
        self.end_date = self.end_date.replace(second=59, microsecond=999999)

        return self


MetricQuery = Annotated[MetricParams, Query()]
