from typing import Literal

from fastapi import Response

from app.core.config import settings

SESSION_COOKIE = "session"


def set_session_cookie(response: Response, session_secret: str, max_age: int) -> None:
    # "none" is required when the frontend and backend are on different
    # origins. SameSite=None mandates Secure=True, which cookie_secure
    # enforces in prod. Locally, "lax" is safe because both services share
    # the same hostname (localhost).
    samesite: Literal["none", "lax"] = "none" if settings.cookie_secure else "lax"
    response.set_cookie(
        key=SESSION_COOKIE,
        value=session_secret,
        httponly=True,
        secure=settings.cookie_secure,
        samesite=samesite,
        max_age=max_age,
    )


def clear_session_cookie(response: Response) -> None:
    samesite: Literal["none", "lax"] = "none" if settings.cookie_secure else "lax"
    response.delete_cookie(key=SESSION_COOKIE, samesite=samesite)
