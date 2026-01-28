from datetime import datetime, timezone

from pydantic import AwareDatetime

from .api_key import APIKeyCreate, APIKeyListResponse, APIKeyResponse
from .auth import LoginRequest, TokenResponse
from .metric import (
    MetricEndpointStatsResponse,
    MetricParams,
    MetricQuery,
    MetricResponse,
    MetricSummaryResponse,
    MetricTimeSeriesPointResponse,
)
from .project import ProjectCreate, ProjectResponse
from .user import UserCreate, UserResponse

__all__ = [
    # Auth
    "LoginRequest",
    "TokenResponse",
    # Project
    "ProjectCreate",
    "ProjectResponse",
    # User
    "UserCreate",
    "UserResponse",
    # API Key
    "APIKeyCreate",
    "APIKeyResponse",
    "APIKeyListResponse",
    # Metrics
    "MetricResponse",
    "MetricSummaryResponse",
    "MetricTimeSeriesPointResponse",
    "MetricEndpointStatsResponse",
    "MetricParams",
    "MetricQuery",
]


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
