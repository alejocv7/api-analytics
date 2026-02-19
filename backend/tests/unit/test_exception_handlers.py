"""Unit tests for exception handler responses (request_id, Retry-After)."""

import json
from typing import Any, cast
from unittest.mock import MagicMock

import pytest
from fastapi import status
from fastapi.exceptions import HTTPException
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from pydantic import ValidationError as PydanticValidationError

from app.core.config import settings
from app.core.exceptions import (
    BadRequestError,
    BearerAuthenticationError,
    NotFoundError,
    api_exception_handler,
    generic_exception_handler,
    http_exception_handler,
    rate_limit_handler,
    validation_exception_handler,
)


def make_request(
    request_id: str = "", headers: dict[str, str] | None = None
) -> MagicMock:
    """Build a minimal mock Request with controllable headers."""
    all_headers: dict[str, str] = dict(headers or {})
    if request_id:
        all_headers[settings.REQUEST_ID_HEADER] = request_id

    mock = MagicMock()
    mock.headers = all_headers
    mock.method = "GET"
    mock.url.path = "/test"
    return mock


def make_rate_limit_exceeded(expiry_seconds: int = 60) -> MagicMock:
    """Build a mock RateLimitExceeded with controllable expiry."""
    limit_item = MagicMock()
    limit_item.get_expiry.return_value = expiry_seconds

    limit_wrapper = MagicMock()
    limit_wrapper.limit = limit_item

    exc: MagicMock = MagicMock()
    exc.limit = limit_wrapper
    return exc


def parse_body(response: JSONResponse) -> dict[str, Any]:
    """Extract JSON body from JSONResponse for assertions."""
    # JSONResponse.body is bytes | memoryview; convert to bytes if needed
    body = response.body
    if isinstance(body, memoryview):
        body = bytes(body)
    return cast(dict[str, Any], json.loads(body.decode()))


# ---------------------------------------------------------------------------
# generic_exception_handler
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_generic_exception_handler_includes_request_id() -> None:
    request = make_request(request_id="req-generic")
    response = await generic_exception_handler(request, RuntimeError("boom"))

    assert response.status_code == status.HTTP_500_INTERNAL_SERVER_ERROR
    data = parse_body(response)
    assert data["request_id"] == "req-generic"
    assert data["error"] == "Internal Server Error"


@pytest.mark.asyncio
async def test_generic_exception_handler_empty_request_id() -> None:
    request = make_request()
    response = await generic_exception_handler(request, RuntimeError("boom"))

    data = parse_body(response)
    assert data["request_id"] is None


# ---------------------------------------------------------------------------
# http_exception_handler
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_http_exception_handler_includes_request_id() -> None:
    request = make_request(request_id="req-http")
    exc = HTTPException(status_code=404, detail="Not found")
    response = await http_exception_handler(request, exc)

    data = parse_body(response)
    assert response.status_code == 404
    assert data["request_id"] == "req-http"
    assert data["error"] == "Not found"


@pytest.mark.asyncio
async def test_http_exception_handler_dict_detail() -> None:
    request = make_request(request_id="req-dict")
    exc = HTTPException(status_code=400, detail={"code": "invalid"})
    response = await http_exception_handler(request, exc)

    data = parse_body(response)
    assert data["error"] == "Request Error"
    assert data["details"] == {"code": "invalid"}
    assert data["request_id"] == "req-dict"


# ---------------------------------------------------------------------------
# api_exception_handler
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_api_exception_handler_includes_request_id() -> None:
    request = make_request(request_id="req-api")
    exc = NotFoundError("Project not found")
    response = await api_exception_handler(request, exc)

    data = parse_body(response)
    assert response.status_code == 404
    assert data["error"] == "Project not found"
    assert data["request_id"] == "req-api"


@pytest.mark.asyncio
async def test_api_exception_handler_bearer_sets_www_authenticate_header() -> None:
    request = make_request(request_id="req-bearer")
    exc = BearerAuthenticationError()
    response = await api_exception_handler(request, exc)

    assert response.status_code == 401
    assert response.headers.get("www-authenticate") == "Bearer"
    data = parse_body(response)
    assert data["request_id"] == "req-bearer"


@pytest.mark.asyncio
async def test_api_exception_handler_no_request_id() -> None:
    request = make_request()
    exc = BadRequestError("bad input")
    response = await api_exception_handler(request, exc)

    data = parse_body(response)
    assert data["request_id"] is None


# ---------------------------------------------------------------------------
# validation_exception_handler
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_validation_exception_handler_includes_request_id() -> None:
    class M(BaseModel):
        x: int

    request = make_request(request_id="req-val")
    pydantic_exc: PydanticValidationError | None = None
    try:
        M(x="not_an_int")
    except PydanticValidationError as e:
        pydantic_exc = e

    assert pydantic_exc is not None
    response = await validation_exception_handler(request, pydantic_exc)

    data = parse_body(response)
    assert response.status_code == status.HTTP_422_UNPROCESSABLE_CONTENT
    assert data["request_id"] == "req-val"
    assert data["error"] == "Validation Error"
    assert isinstance(data["details"], list)


# ---------------------------------------------------------------------------
# rate_limit_handler
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_rate_limit_handler_uses_dynamic_retry_after() -> None:
    request = make_request(request_id="req-rl")
    exc = make_rate_limit_exceeded(expiry_seconds=120)
    response = await rate_limit_handler(request, exc)

    assert response.status_code == status.HTTP_429_TOO_MANY_REQUESTS
    assert response.headers["retry-after"] == "120"
    data = parse_body(response)
    assert data["error"] == "Rate limit exceeded"
    assert data["request_id"] == "req-rl"


@pytest.mark.asyncio
async def test_rate_limit_handler_one_minute_window() -> None:
    request = make_request()
    exc = make_rate_limit_exceeded(expiry_seconds=60)
    response = await rate_limit_handler(request, exc)

    assert response.headers["retry-after"] == "60"


@pytest.mark.asyncio
async def test_rate_limit_handler_one_hour_window() -> None:
    request = make_request()
    exc = make_rate_limit_exceeded(expiry_seconds=3600)
    response = await rate_limit_handler(request, exc)

    assert response.headers["retry-after"] == "3600"


@pytest.mark.asyncio
async def test_rate_limit_handler_null_limit_falls_back_to_60() -> None:
    """If exc.limit is None (edge case), Retry-After should default to 60."""
    request = make_request()
    exc = make_rate_limit_exceeded()
    exc.limit = None
    response = await rate_limit_handler(request, exc)

    assert response.headers["retry-after"] == "60"
