import hashlib
import re
import time

from fastapi import Request
from starlette.background import BackgroundTasks
from starlette.middleware.base import BaseHTTPMiddleware

from app.core import db
from app.core.config import settings
from app.crud import create_metric
from app.schemas import APIMetricCreate


def log_api_metric(
    api_metric_in: APIMetricCreate,
):
    """
    Background task to log API metrics to the database.
    """
    try:
        with db.get_db() as db_session:
            create_metric(db_session, api_metric_in=api_metric_in)
    except Exception as e:
        print(f"Error logging metric in background: {e}")


class APIMetricMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        if not re.match(r"/api/v\d+/(?!track)", request.url.path):
            return await call_next(request)

        print("----------- ALEJANDRO ----------- 2")
        start_time = time.perf_counter()
        response = await call_next(request)
        print("----------- ALEJANDRO ----------- 3")
        process_time = (time.perf_counter() - start_time) * 1000  # Convert to ms

        ip_hash = None
        if request.client and request.client.host:
            ip_hash = hashlib.sha256(request.client.host.encode()).hexdigest()[:16]

        api_metric_in = APIMetricCreate(
            project_id=settings.PROJECT_NAME,
            url_path=request.url.path,
            method=request.method,
            response_status_code=response.status_code,
            response_time_ms=process_time,
            user_agent=request.headers.get("user-agent"),
            ip_hash=ip_hash,
        )

        # Use BackgroundTasks to record the metric without blocking the response
        if response.background:
            response.background.add_task(log_api_metric, api_metric_in)
        else:
            background_tasks = BackgroundTasks()
            background_tasks.add_task(log_api_metric, api_metric_in)
            response.background = background_tasks

        return response
