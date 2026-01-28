from datetime import datetime, timedelta, timezone
from http import HTTPMethod, HTTPStatus
from typing import Annotated, Self

from fastapi import Query
from fastapi.openapi.models import EmailStr
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


def sanitize_project_name(name: str) -> str:
    return name.strip().lower().replace(" ", "-")


# ==================== Metric Schemas ====================
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


# ==================== User Schemas ====================
class UserCreate(BaseModel):
    """Schema for user registration."""

    email: EmailStr
    password: str = Field(..., min_length=8)
    full_name: str | None = None


class UserLogin(BaseModel):
    """Schema for user login."""

    email: EmailStr
    password: str


class UserResponse(BaseModel):
    """Schema for user data in responses."""

    email: str
    full_name: str | None
    is_active: bool
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class Token(BaseModel):
    """JWT token."""

    access_token: str
    token_type: str = "bearer"


class TokenData(BaseModel):
    """Data stored in JWT token."""

    user_id: int
    email: str


# ==================== Project Schemas ====================
class ProjectBase(BaseModel):
    """Base project schema."""

    name: str = Field(..., min_length=1, max_length=100)
    description: str | None = Field(None, max_length=1000)

    model_config = ConfigDict(from_attributes=True, str_strip_whitespace=True)


class ProjectCreate(ProjectBase):
    """Schema for creating a project."""

    model_config = ConfigDict(
        json_schema_extra={
            "examples": [
                {
                    "name": "Production API",
                    "description": "Main production API for e-commerce platform",
                }
            ]
        }
    )


class ProjectUpdate(BaseModel):
    """Schema for updating a project."""

    name: str | None = Field(None, min_length=1, max_length=100)
    description: str | None = Field(None, max_length=1000)
    is_active: bool | None = None

    model_config = ConfigDict(
        str_strip_whitespace=True,
        json_schema_extra={
            "examples": [
                {
                    "name": "Updated Project Name",
                    "description": "Updated description",
                    "is_active": True,
                }
            ]
        },
    )


class ProjectResponse(ProjectBase):
    """Schema for project in responses."""

    id: int
    slug: str
    user_id: int
    is_active: bool
    created_at: datetime
    updated_at: datetime | None

    model_config = ConfigDict(from_attributes=True)


class ProjectDetailResponse(ProjectResponse):
    """Detailed project response with statistics."""

    total_api_keys: int = 0
    active_api_keys: int = 0
    total_metrics: int = 0
    metrics_last_24h: int = 0
    avg_response_time_ms: float = 0.0
    error_rate_percent: float = 0.0

    model_config = ConfigDict(from_attributes=True)


class ProjectListResponse(BaseModel):
    """Response for list of projects."""

    items: list[ProjectResponse]
    total: int
    page: int
    page_size: int

    model_config = ConfigDict(
        json_schema_extra={
            "examples": [{"items": [], "total": 0, "page": 1, "page_size": 20}]
        }
    )


# ==================== API Key Schemas ====================
class APIKeyBase(BaseModel):
    """Base API key schema."""

    name: str | None = Field(None, max_length=255)


class APIKeyCreate(APIKeyBase):
    """Schema for creating an API key."""

    expires_at: datetime | None = None

    model_config = ConfigDict(
        json_schema_extra={
            "examples": [
                {"name": "Production Key", "expires_at": None},
                {"name": "Temporary Testing Key", "expires_at": "2026-12-31T23:59:59Z"},
            ]
        }
    )


class APIKeyUpdate(BaseModel):
    """Schema for updating an API key."""

    name: str | None = Field(None, max_length=255)
    is_active: bool | None = None


class APIKeyResponse(APIKeyBase):
    """Schema for API key in responses (without the actual key)."""

    id: int
    project_id: int
    is_active: bool
    created_at: datetime
    last_used_at: datetime | None
    expires_at: datetime | None
    total_requests: int

    model_config = ConfigDict(from_attributes=True)


class APIKeyCreateResponse(APIKeyResponse):
    """
    Response when creating a new API key.
    IMPORTANT: This is the ONLY time the full key is shown!
    """

    key: str  # Full API key - shown only once!
    warning: str = "Save this key securely! You won't be able to see it again."

    model_config = ConfigDict(
        json_schema_extra={
            "examples": [
                {
                    "id": 1,
                    "key": "sk_live_abc123",
                    "name": "Production Key",
                    "project_id": 1,
                    "is_active": True,
                    "created_at": "2026-01-27T10:00:00Z",
                    "last_used_at": None,
                    "expires_at": None,
                    "total_requests": 0,
                    "warning": "Save this key securely! You won't be able to see it again.",
                }
            ]
        }
    )


class APIKeyListResponse(BaseModel):
    """Response for list of API keys."""

    items: list[APIKeyResponse]
    total: int

    model_config = ConfigDict(
        json_schema_extra={"examples": [{"items": [], "total": 0}]}
    )
