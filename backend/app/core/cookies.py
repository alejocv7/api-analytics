from fastapi import Response

from app.core.config import settings

SESSION_COOKIE = "session"


def set_session_cookie(response: Response, session_secret: str, max_age: int) -> None:
    response.set_cookie(
        key=SESSION_COOKIE,
        value=session_secret,
        httponly=True,
        secure=settings.cookie_secure,
        samesite="lax",
        max_age=max_age,
    )


def clear_session_cookie(response: Response) -> None:
    response.delete_cookie(
        key=SESSION_COOKIE,
        samesite="lax",
        secure=settings.cookie_secure,
        httponly=True,
    )
