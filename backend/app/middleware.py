import contextvars
import logging
import re
import time
import uuid
from http import HTTPMethod

from fastapi import Request
from starlette.background import BackgroundTasks
from starlette.middleware.base import BaseHTTPMiddleware

from app import schemas
from app.core import db
from app.core.config import settings
from app.services.metric_service import add_metric

logger = logging.getLogger(__name__)

# Context variable to store request ID
request_id_ctx = contextvars.ContextVar("request_id", default="none")


async def log_metric(
    project_id: int,
    metric: schemas.MetricCreate,
):
    """
    Background task to log API metrics to the database.
    """
    try:
        async with db.AsyncSessionLocal() as session:
            await add_metric(session, project_id, metric)
    except Exception:
        logger.exception("Failed to log metric in background")


class MetricMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        if settings.ENVIRONMENT == "testing" or not re.match(
            r"/api/v\d+/(?!track)", request.url.path
        ):
            return await call_next(request)

        start_time = time.perf_counter()
        response = await call_next(request)
        process_time = (time.perf_counter() - start_time) * 1000  # Convert to ms

        ip = request.client.host if request.client else None

        metric = schemas.MetricCreate(
            url_path=request.url.path,
            method=HTTPMethod(request.method),
            response_status_code=response.status_code,
            response_time_ms=process_time,
            user_agent=request.headers.get("user-agent", "unknown"),
            ip=ip,
        )

        # Use BackgroundTasks to record the metric without blocking the response
        project_id = settings.PROJECT_ID
        if response.background:
            response.background.add_task(log_metric, project_id, metric)
        else:
            background_tasks = BackgroundTasks()
            background_tasks.add_task(log_metric, project_id, metric)
            response.background = background_tasks

        return response


class RequestIDMiddleware(BaseHTTPMiddleware):
    """
    Middleware to generate and propagate a correlation ID for each request.
    """

    async def dispatch(self, request: Request, call_next):
        request_id = request.headers.get("X-Request-ID", str(uuid.uuid4()))
        token = request_id_ctx.set(request_id)
        try:
            response = await call_next(request)
            response.headers["X-Request-ID"] = request_id
            return response
        finally:
            request_id_ctx.reset(token)


class LoggingMiddleware(BaseHTTPMiddleware):
    """
    Middleware to log every request and response.
    """

    async def dispatch(self, request: Request, call_next):
        start_time = time.perf_counter()
        method = request.method
        path = request.url.path

        # Log request start
        logger.info(
            f"Request started: {method} {path}",
            extra={
                "http_method": method,
                "http_path": path,
                "client_ip": request.client.host if request.client else "unknown",
            },
        )

        try:
            response = await call_next(request)
            process_time = (time.perf_counter() - start_time) * 1000
            status_code = response.status_code

            # Log response
            logger.info(
                f"Request finished: {method} {path} - {status_code} ({process_time:.2f}ms)",
                extra={
                    "http_method": method,
                    "http_path": path,
                    "status_code": status_code,
                    "process_time_ms": round(process_time, 2),
                },
            )
            return response
        except Exception as e:
            process_time = (time.perf_counter() - start_time) * 1000
            logger.error(
                f"Request failed: {method} {path} - {str(e)}",
                extra={
                    "http_method": method,
                    "http_path": path,
                    "error": str(e),
                    "process_time_ms": round(process_time, 2),
                },
                exc_info=True,
            )
            raise
