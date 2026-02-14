from slowapi import Limiter
from slowapi.util import get_remote_address
from starlette.requests import Request

from app.core import rate_limits
from app.core.config import settings


def _get_user_key(request: Request) -> str:
    """Rate limit key using authenticated user ID with IP fallback."""
    user = getattr(request.state, "user", None)
    if user and hasattr(user, "id"):
        return f"user:{user.id}"
    return get_remote_address(request)


def _get_project_key(request: Request) -> str:
    """Rate limit key using project ID with IP fallback."""
    project_id = getattr(request.state, "project_id", None)
    if project_id:
        return f"project:{project_id}"
    return get_remote_address(request)


limiter = Limiter(
    key_func=get_remote_address,
    default_limits=[rate_limits.GLOBAL],
    storage_uri=settings.REDIS_URL,
)
