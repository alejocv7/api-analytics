import asyncio
import logging
import re
import time
import uuid
from http import HTTPMethod
from typing import Any

from starlette.datastructures import Headers, MutableHeaders
from starlette.types import ASGIApp, Message, Receive, Scope, Send

from app import schemas
from app.core import db
from app.core.config import settings
from app.services import metric_service, project_service

logger = logging.getLogger(__name__)


class MetricMiddleware:
    """
    Middleware for tracking API metrics for this project.
    """

    API_TRACKING_PATTERN = re.compile(r"/api/v\d+/(?!track)")

    def __init__(self, app: ASGIApp, app_state: Any = None) -> None:
        self.app = app
        self._background_tasks: set[asyncio.Task[None]] = set()
        self._project_id: uuid.UUID | None = None
        self._project_id_lock: asyncio.Lock = asyncio.Lock()

        if app_state is not None:
            app_state.metric_middleware = self

    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return

        path = scope.get("path", "")
        if (
            settings.ENVIRONMENT == "test"
            or not settings.PROJECT_KEY
            or not self.API_TRACKING_PATTERN.match(path)
        ):
            await self.app(scope, receive, send)
            return

        start_time = time.perf_counter()
        status_code = 500  # Default if we don't see response.start

        async def send_wrapper(message: Message) -> None:
            nonlocal status_code
            if message["type"] == "http.response.start":
                status_code = message["status"]
            await send(message)

        try:
            await self.app(scope, receive, send_wrapper)
        finally:
            try:
                process_time = (time.perf_counter() - start_time) * 1000

                headers = Headers(scope=scope)
                user_agent = headers.get("user-agent", "unknown")

                ip = None
                if "x-forwarded-for" in headers:
                    ip = headers["x-forwarded-for"].split(",")[0].strip()
                elif scope.get("client"):
                    ip = scope["client"][0]

                metric = schemas.MetricCreate(
                    url_path=path,
                    method=HTTPMethod(scope["method"]),
                    response_status_code=status_code,
                    response_time_ms=process_time,
                    user_agent=user_agent,
                    ip=ip,
                )

                task = asyncio.create_task(self.log_metric(metric))
                self._background_tasks.add(task)
                task.add_done_callback(self._background_tasks.discard)
            except Exception:
                logger.exception("Failed to schedule metric background task")

    async def log_metric(self, metric: schemas.MetricCreate) -> None:
        """
        Background task to log API metrics to the database.

        Lazily resolves and caches the self-monitoring project ID using
        double-checked locking to prevent redundant DB lookups under
        concurrent burst traffic on cold start.
        """
        try:
            async with db.AsyncSessionLocal() as session:
                if not self._project_id:
                    async with self._project_id_lock:
                        if not self._project_id:
                            project = await project_service.find_project_by_key(
                                settings.PROJECT_KEY, session
                            )
                            if not project:
                                logger.warning("Self-monitoring project not found")
                                return

                            self._project_id = project.id

                await metric_service.add_metric(metric, self._project_id, session)

        except Exception:
            logger.exception("Failed to log metric in background")

    async def drain_background_tasks(self, timeout_seconds: float) -> None:
        """Wait for in-flight metric tasks and cancel leftovers on timeout."""
        tasks = set(self._background_tasks)
        if not tasks:
            return

        try:
            await asyncio.wait_for(
                asyncio.gather(*tasks, return_exceptions=True),
                timeout=timeout_seconds,
            )
        except TimeoutError:
            logger.warning(
                "Timed out draining %d metric background tasks; "
                "cancelling pending tasks",
                len(tasks),
            )

            for task in tasks:
                if not task.done():
                    task.cancel()
            await asyncio.gather(*tasks, return_exceptions=True)


class LoggingMiddleware:
    """
    Logging middleware to log every request and response.
    """

    def __init__(self, app: ASGIApp) -> None:
        self.app = app

    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return

        start_time = time.perf_counter()
        method, path = scope["method"], scope["path"]

        logger.info(
            "Request started: %s %s",
            method,
            path,
            extra={
                "http_method": method,
                "http_path": path,
            },
        )

        status_code = "unknown"

        async def send_wrapper(message: Message) -> None:
            nonlocal status_code
            if message["type"] == "http.response.start":
                status_code = message["status"]
            await send(message)

        try:
            await self.app(scope, receive, send_wrapper)
            process_time = (time.perf_counter() - start_time) * 1000

            logger.info(
                "Request finished: %s %s - %s (%.2fms)",
                method,
                path,
                status_code,
                process_time,
                extra={
                    "http_method": method,
                    "http_path": path,
                    "status_code": status_code,
                    "process_time_ms": round(process_time, 2),
                },
            )
        except Exception as e:
            process_time = (time.perf_counter() - start_time) * 1000
            logger.exception(
                "Request failed: %s %s",
                method,
                path,
                extra={
                    "http_method": method,
                    "http_path": path,
                    "error": str(e),
                    "process_time_ms": round(process_time, 2),
                },
            )
            raise


class SecurityHeadersMiddleware:
    """
    Adds security headers to the response.
    """

    def __init__(self, app: ASGIApp) -> None:
        self.app = app
        self.headers = settings.security_headers

    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return

        async def send_wrapper(message: Message) -> None:
            if message["type"] == "http.response.start":
                headers = MutableHeaders(scope=message)
                headers.update(self.headers)

            await send(message)

        await self.app(scope, receive, send_wrapper)
