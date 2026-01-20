import datetime
import hashlib
import re
import time

from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware

from app.core import db
from app.core.config import settings
from app.models import APIMetric


class APIMetricMiddleware(BaseHTTPMiddleware):
    def __init__(self, app):
        super().__init__(app)

    async def dispatch(self, request: Request, call_next):
        if re.match(r"/api/v\d+/track", request.url.path):
            return await call_next(request)

        start_time = time.perf_counter()
        response = await call_next(request)
        response_time_ms = time.perf_counter() - start_time

        ip_hash = None
        if request.client and request.client.host:
            ip_hash = hashlib.sha256(request.client.host.encode()).hexdigest()[:16]

        try:
            db_session = next(db.get_db())
            db_session.add(
                APIMetric(
                    project_id=settings.PROJECT_NAME,
                    url_path=request.url.path,
                    method=request.method,
                    response_status_code=response.status_code,
                    response_time_ms=response_time_ms,
                    timestamp=datetime.datetime.now(),
                    user_agent=request.headers.get("user-agent"),
                    ip_hash=ip_hash,
                )
            )
            db_session.commit()
        except Exception as e:
            print(f"Error processing metric request: {e}")
            db_session.rollback()
        finally:
            db_session.close()

        return response
