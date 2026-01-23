from http import HTTPMethod, HTTPStatus
from typing import Annotated

from pydantic import (
    AfterValidator,
    AwareDatetime,
    BaseModel,
    ConfigDict,
    Field,
    StringConstraints,
)


def normalize_url_path(url_path: str) -> str:
    if not url_path.startswith("/"):
        raise ValueError("url_path must start with '/'")
    return url_path.rstrip("/") or "/"


class MetricBase(BaseModel):
    project_id: Annotated[
        str,
        StringConstraints(
            min_length=3,
            max_length=50,
            pattern=r"^[a-zA-Z0-9_-]+$",
        ),
    ] = Field(..., description="Unique identifier for the project/app")

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
