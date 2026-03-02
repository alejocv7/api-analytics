from __future__ import annotations

import uuid
from datetime import UTC, timedelta
from http import HTTPMethod
from typing import Annotated, Any, Literal, Self

from fastapi import Query
from pydantic import (
    AwareDatetime,
    BaseModel,
    ConfigDict,
    Field,
    model_validator,
)

from app.core.enums import StatsFields, TimeGranularity
from app.core.types import NormalizedUrlPath
from app.core.utils import get_default_end_date, get_default_start_date
from app.schemas.pagination import PaginatedResponse, PaginationParams


class MetricBase(BaseModel):
    url_path: NormalizedUrlPath = Field(..., description="API endpoint path")

    method: HTTPMethod = Field(..., description="HTTP method")
    response_status_code: int = Field(
        ..., ge=100, le=599, description="HTTP status code"
    )
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
                    "response_status_code": 200,
                    "response_time_ms": 45.3,
                    "user_agent": "Mozilla/5.0...",
                }
            ]
        }
    )


class MetricResponse(MetricBase):
    id: uuid.UUID
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
        0.0, description="Average response time in milliseconds"
    )
    error_count: int = Field(0, description="Number of errors")

    @model_validator(mode="after")
    def round_stats(self) -> Self:
        self.avg_response_time_ms = round(self.avg_response_time_ms or 0, 2)
        return self

    model_config = ConfigDict(
        from_attributes=True,
        json_schema_extra={
            "examples": [
                {
                    "timestamp": "2026-01-31T10:00:00Z",
                    "request_count": 150,
                    "avg_response_time_ms": 124.5,
                    "error_count": 2,
                }
            ]
        },
    )


class PerformanceStatsMixin(BaseModel):
    """Common performance statistics fields."""

    request_count: int = Field(default=0, description="Number of requests")
    avg_response_time_ms: float = Field(
        default=0.0, description="Average response time in milliseconds"
    )
    error_count: int = Field(default=0, description="Number of errors")
    error_rate: float = Field(
        default=0.0, description="Percentage of requests with status >= 400"
    )
    slowest_request_ms: float = Field(
        default=0.0, description="Slowest request in milliseconds"
    )
    fastest_request_ms: float = Field(
        default=0.0, description="Fastest request in milliseconds"
    )

    @model_validator(mode="after")
    def finalize_stats(self) -> Self:
        self.avg_response_time_ms = round(self.avg_response_time_ms or 0, 2)
        self.slowest_request_ms = round(self.slowest_request_ms or 0, 2)
        self.fastest_request_ms = round(self.fastest_request_ms or 0, 2)
        if self.request_count > 0:
            self.error_rate = round((self.error_count / self.request_count) * 100, 2)
        else:
            self.error_rate = 0.0
        return self

    model_config = ConfigDict(from_attributes=True)


class SortablePerformanceParams(BaseModel):
    """Parameters for sorting performance statistics."""

    sort_by: StatsFields = StatsFields.request_count
    sort_order: Literal["asc", "desc"] = "desc"


class MetricSummaryResponse(PerformanceStatsMixin):
    """Schema for summary statistics."""

    requests_per_minute: float = Field(default=0.0, description="Requests per minute")

    @classmethod
    def from_raw(cls, row: Any, params: MetricParams) -> MetricSummaryResponse:
        if not row or not row.request_count:
            return cls()

        duration_in_seconds = (params.end_date - params.start_date).total_seconds()
        duration_in_minutes = max(duration_in_seconds / 60, 1)
        requests_per_minute = round(row.request_count / duration_in_minutes, 2)

        data = dict(row._mapping, requests_per_minute=requests_per_minute)
        return cls.model_validate(data)

    model_config = ConfigDict(
        from_attributes=True,
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
        },
    )


class MetricEndpointStatsResponse(PerformanceStatsMixin):
    url_path: str = Field(..., description="API endpoint path")
    method: HTTPMethod = Field(..., description="HTTP method")

    model_config = ConfigDict(
        from_attributes=True,
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
        },
    )


class MetricParams(PaginationParams):
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
        self.start_date = self.start_date.astimezone(UTC)
        self.end_date = self.end_date.astimezone(UTC)

        if self.end_date < self.start_date:
            raise ValueError(
                f"end_date ({self.end_date}) cannot be before "
                f"start_date ({self.start_date})"
            )

        date_range = self.end_date - self.start_date
        if date_range > timedelta(days=60):
            raise ValueError(f"Date range ({date_range}) must be 60 days or less")
        if date_range < timedelta(minutes=1):
            raise ValueError(f"Date range ({date_range}) must be at least 1 minute")

        # Truncate to the minute
        self.start_date = self.start_date.replace(second=0, microsecond=0)
        self.end_date = self.end_date.replace(second=59, microsecond=999999)

        return self


MetricQuery = Annotated[MetricParams, Query()]


class MetricTimeSeriesParams(MetricParams):
    granularity: TimeGranularity = TimeGranularity.MINUTE


MetricTimeSeriesQuery = Annotated[MetricTimeSeriesParams, Query()]


class MetricEndpointStatsParams(MetricParams, SortablePerformanceParams):
    pass


MetricEndpointStatsQuery = Annotated[MetricEndpointStatsParams, Query()]

MetricListResponse = PaginatedResponse[MetricResponse]
MetricTimeSeriesListResponse = PaginatedResponse[MetricTimeSeriesPointResponse]
MetricEndpointStatsListResponse = PaginatedResponse[MetricEndpointStatsResponse]
