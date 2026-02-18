"""
Exception handling for the API Analytics service.

Exception conventions:
- **APIError subclasses**: Use in services/dependencies for any error that should
  return an HTTP error response to the client (4xx/5xx). Always include a descriptive
  `message` and the appropriate subclass sets the `status_code` automatically.

  Available subclasses:
  - NotFoundError (404): Resource not found
  - ConflictError (409): Resource conflict (duplicate, constraint violation)
  - AuthenticationError (401): Authentication failed
  - BearerAuthenticationError (401): Authentication failed with Bearer header
  - BadRequestError (400): Invalid request data or business logic violation
  - RateLimitError (429): Rate limit exceeded
    (rarely used directly, slowapi handles this)

- **ValueError**: Only use inside Pydantic validators, model validators, and
  type coercion functions. Pydantic catches these and converts them to 422
  validation errors automatically.

- **RuntimeError**: Use for startup/infrastructure failures that should crash
  the application (e.g., database connection failure during lifespan).

- Never raise bare `Exception`. Never let SQLAlchemy exceptions
  (NoResultFound, IntegrityError) propagate unhandled.
"""

import logging
from typing import Any, ClassVar

from fastapi import FastAPI, Request, status
from fastapi.exceptions import HTTPException, RequestValidationError
from fastapi.responses import JSONResponse
from pydantic_core import ValidationError
from slowapi.errors import RateLimitExceeded

logger = logging.getLogger(__name__)


class APIError(Exception):
    """Base class for all API errors."""

    STATUS_CODE: ClassVar[int] = 500
    MESSAGE: ClassVar[str] = "Internal Server Error"
    HEADERS: ClassVar[dict[str, str] | None] = None

    def __init__(
        self,
        message: str | None = None,
        details: dict[str, Any] | None = None,
        headers: dict[str, str] | None = None,
    ):
        self.status_code = self.STATUS_CODE
        self.message = message or self.MESSAGE
        self.details = details or {}

        base_headers = headers or self.HEADERS
        self.headers = dict(base_headers) if base_headers else None

        super().__init__(self.message)


class NotFoundError(APIError):
    """Resource not found (404)."""

    STATUS_CODE = status.HTTP_404_NOT_FOUND
    MESSAGE = "Resource not found"


class ConflictError(APIError):
    """Resource conflict - duplicate or constraint violation (409)."""

    STATUS_CODE = status.HTTP_409_CONFLICT
    MESSAGE = "Resource conflict"


class AuthenticationError(APIError):
    """Authentication failed (401)."""

    STATUS_CODE = status.HTTP_401_UNAUTHORIZED
    MESSAGE = "Authentication failed"


class BearerAuthenticationError(AuthenticationError):
    """Authentication failed (401) with Bearer header."""

    HEADERS: ClassVar[dict[str, str] | None] = {"WWW-Authenticate": "Bearer"}


class ForbiddenError(APIError):
    """Forbidden (403)."""

    STATUS_CODE = status.HTTP_403_FORBIDDEN
    MESSAGE = "Forbidden"


class BadRequestError(APIError):
    """Invalid request data or business logic violation (400)."""

    STATUS_CODE = status.HTTP_400_BAD_REQUEST
    MESSAGE = "Bad request"


class RateLimitError(APIError):
    """Rate limit exceeded (429)."""

    STATUS_CODE = status.HTTP_429_TOO_MANY_REQUESTS
    MESSAGE = "Rate limit exceeded"


def register_exceptions(app: FastAPI) -> None:
    app.exception_handler(RateLimitExceeded)(rate_limit_handler)
    app.exception_handler(HTTPException)(http_exception_handler)
    app.exception_handler(APIError)(api_exception_handler)
    app.exception_handler(RequestValidationError)(validation_exception_handler)
    app.exception_handler(ValidationError)(validation_exception_handler)
    app.exception_handler(Exception)(generic_exception_handler)


async def generic_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    logger.exception(
        "Unhandled exception on %s %s: %s",
        request.method,
        request.url.path,
        exc,
    )
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={"error": "Internal Server Error", "details": {}},
    )


async def http_exception_handler(_: Request, exc: HTTPException) -> JSONResponse:
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "error": exc.detail if isinstance(exc.detail, str) else "Request Error",
            "details": {} if isinstance(exc.detail, str) else exc.detail,
        },
        headers=exc.headers,
    )


async def api_exception_handler(_: Request, exc: APIError) -> JSONResponse:
    return JSONResponse(
        status_code=exc.status_code,
        content={"error": exc.message, "details": exc.details},
        headers=exc.headers,
    )


async def validation_exception_handler(
    _: Request, exc: RequestValidationError | ValidationError
) -> JSONResponse:
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
        content={
            "error": "Validation Error",
            "details": [
                {"field": error["loc"], "message": error["msg"]}
                for error in exc.errors()
            ],
        },
    )


async def rate_limit_handler(_: Request, exc: RateLimitExceeded) -> JSONResponse:
    return JSONResponse(
        status_code=status.HTTP_429_TOO_MANY_REQUESTS,
        content={"error": "Rate limit exceeded", "details": str(exc)},
        headers={"Retry-After": "60"},
    )
