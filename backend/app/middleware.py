import re
import time
from http import HTTPMethod

from fastapi import Request
from starlette.background import BackgroundTasks
from starlette.middleware.base import BaseHTTPMiddleware

from app import schemas
from app.core import db
from app.core.config import settings
from app.services.metric import add_metric


def log_metric(
    project_id: int,
    metric: schemas.MetricCreate,
):
    """
    Background task to log API metrics to the database.
    """
    try:
        with db.Session() as session:
            add_metric(session, project_id, metric)
    except Exception as e:
        print(f"Error logging metric in background: {e}")


class MetricMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        if not re.match(r"/api/v\d+/(?!track)", request.url.path):
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
