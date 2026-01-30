from datetime import datetime, timezone
from typing import Annotated

from pydantic import AfterValidator, AwareDatetime, BeforeValidator, SecretStr

from app.core import security
from app.schemas.api_key import APIKeyCreate, APIKeyListResponse, APIKeyResponse
from app.schemas.auth import LoginRequest, TokenData, TokenResponse
from app.schemas.metric import (
    MetricCreate,
    MetricEndpointStatsResponse,
    MetricParams,
    MetricQuery,
    MetricResponse,
    MetricSummaryResponse,
    MetricTimeSeriesPointResponse,
)
from app.schemas.project import ProjectCreate, ProjectResponse, ProjectUpdate
from app.schemas.user import UserCreate, UserResponse

__all__ = [
    # Auth
    "LoginRequest",
    "TokenResponse",
    "TokenData",
    # Project
    "ProjectCreate",
    "ProjectResponse",
    "ProjectUpdate",
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
    "MetricCreate",
]


def get_default_start_date() -> AwareDatetime:
    return datetime.now(timezone.utc).replace(hour=0, minute=0, second=0, microsecond=0)


def get_default_end_date() -> AwareDatetime:
    return datetime.now(timezone.utc).replace(
        hour=23, minute=59, second=59, microsecond=999999
    )


def normalize_url_path(url_path: str) -> str:
    if not url_path.startswith("/"):
        raise ValueError("url_path must start with '/'")
    return url_path.rstrip("/") or "/"


NormalizedUrlPath = Annotated[str, BeforeValidator(normalize_url_path)]
SecurePassword = Annotated[SecretStr, AfterValidator(security.validate_password)]
