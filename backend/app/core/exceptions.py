import logging
from typing import Any

from fastapi import FastAPI, Request, Response, status
from fastapi.exceptions import HTTPException, RequestValidationError
from fastapi.responses import JSONResponse
from pydantic_core import ValidationError
from slowapi.errors import RateLimitExceeded

logger = logging.getLogger(__name__)


class APIError(Exception):
    def __init__(
        self,
        message: str,
        status_code: int = 500,
        details: dict[str, Any] | None = None,
    ):
        super().__init__(message)
        self.message = message
        self.status_code = status_code
        self.details = details or {}


def register_exceptions(app: FastAPI) -> None:
    app.exception_handler(RateLimitExceeded)(rate_limit_handler)
    app.exception_handler(HTTPException)(http_exception_handler)
    app.exception_handler(APIError)(api_exception_handler)
    app.exception_handler(RequestValidationError)(validation_exception_handler)
    app.exception_handler(ValidationError)(validation_exception_handler)
    app.exception_handler(Exception)(generic_exception_handler)


async def generic_exception_handler(_: Request, exc: Exception) -> Response:
    logger.exception("Unhandled exception", exc_info=exc)
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
    )


async def api_exception_handler(_: Request, exc: APIError) -> JSONResponse:
    return JSONResponse(
        status_code=exc.status_code,
        content={"error": exc.message, "details": exc.details},
    )


async def validation_exception_handler(
    _: Request, exc: RequestValidationError
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
    )
