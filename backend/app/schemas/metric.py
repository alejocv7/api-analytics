from datetime import timedelta, timezone
from enum import StrEnum
from http import HTTPMethod, HTTPStatus
from typing import Annotated, Self

from fastapi import Query
from pydantic import (
    AwareDatetime,
    BaseModel,
    ConfigDict,
    Field,
    model_validator,
)

from app.core.types import (
    NormalizedUrlPath,
    get_default_end_date,
    get_default_start_date,
)


class MetricBase(BaseModel):
    url_path: NormalizedUrlPath = Field(..., description="API endpoint path")

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

    model_config = ConfigDict(
        json_schema_extra={
            "examples": [
                {
                    "url_path": "/v1/users",
                    "method": "GET",
                    "status_code": 200,
                    "response_time_ms": 45.3,
                    "user_agent": "Mozilla/5.0...",
                }
            ]
        }
    )


class MetricResponse(MetricBase):
    id: int
    timestamp: AwareDatetime
    ip_hash: str | None = Field(None, description="Hashed IP address")
    model_config = ConfigDict(
        from_attributes=True,
        json_schema_extra={
            "examples": [
                {
                    "url_path": "/v1/users",
                    "method": "GET",
                    "response_status_code": 200,
                    "response_time_ms": 45.3,
                    "user_agent": "Mozilla/5.0...",
                    "id": 123,
                    "timestamp": "2026-01-31T10:00:00Z",
                    "ip_hash": "a1b2c3d4e5f6...",
                }
            ]
        },
    )


class MetricTimeSeriesPointResponse(BaseModel):
    timestamp: AwareDatetime = Field(..., description="Timestamp")
    request_count: int = Field(..., description="Number of requests")
    avg_response_time_ms: float = Field(
        ..., description="Average response time in milliseconds"
    )
    error_count: int = Field(..., description="Number of errors")

    model_config = ConfigDict(
        json_schema_extra={
            "examples": [
                {
                    "timestamp": "2026-01-31T10:00:00Z",
                    "request_count": 150,
                    "avg_response_time_ms": 124.5,
                    "error_count": 2,
                }
            ]
        }
    )


class PerformanceStatsMixin(BaseModel):
    """Common performance statistics fields."""

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


class MetricSummaryResponse(PerformanceStatsMixin):
    """Schema for summary statistics."""

    requests_per_minute: float = Field(..., description="Requests per minute")

    model_config = ConfigDict(
        json_schema_extra={
            "examples": [
                {
                    "request_count": 10542,
                    "avg_response_time_ms": 145.32,
                    "requests_per_minute": 7.3,
                    "error_count": 42,
                    "error_rate": 0.4,
                    "slowest_request_ms": 2341.5,
                    "fastest_request_ms": 12.1,
                }
            ]
        }
    )


class MetricEndpointStatsResponse(PerformanceStatsMixin):
    url_path: str = Field(..., description="API endpoint path")
    method: HTTPMethod = Field(..., description="HTTP method")

    model_config = ConfigDict(
        json_schema_extra={
            "examples": [
                {
                    "url_path": "/api/v1/users",
                    "method": "GET",
                    "request_count": 520,
                    "avg_response_time_ms": 112.4,
                    "error_count": 5,
                    "error_rate": 0.96,
                    "slowest_request_ms": 890.0,
                    "fastest_request_ms": 45.2,
                }
            ]
        }
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
    page: int = Field(default=1, ge=1, description="Page number")
    page_size: int = Field(default=1000, ge=1, le=10000, description="Items per page")

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


class TimeGranularity(StrEnum):
    MINUTE = "minute"
    HOUR = "hour"
    DAY = "day"
