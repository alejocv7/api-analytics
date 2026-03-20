from typing import Annotated

from fastapi import APIRouter, Depends, Request, Response, status
from fastapi.security import OAuth2PasswordRequestForm

from app import models, schemas
from app.core import rate_limits
from app.core.config import settings
from app.core.cookies import ACCESS_TOKEN_COOKIE, REFRESH_TOKEN_COOKIE
from app.core.exceptions import BearerAuthenticationError
from app.core.rate_limiter import limiter
from app.dependencies import CurrentUserDep, RedisDep, SessionDep
from app.services import auth_service

router = APIRouter()

_REFRESH_COOKIE_PATH = f"{settings.API_PREFIX}/auth/refresh"


def _set_auth_cookies(
    response: Response, access_token: str, refresh_token: str
) -> None:
    response.set_cookie(
        key=ACCESS_TOKEN_COOKIE,
        value=access_token,
        httponly=True,
        secure=settings.cookie_secure,
        samesite="strict",
        max_age=settings.SECURITY_ACCESS_TOKEN_EXPIRE_MINUTES * 60,
    )
    # Scope the refresh token cookie to the refresh endpoint only so the
    # browser never sends it to any other API path.
    response.set_cookie(
        key=REFRESH_TOKEN_COOKIE,
        value=refresh_token,
        httponly=True,
        secure=settings.cookie_secure,
        samesite="strict",
        path=_REFRESH_COOKIE_PATH,
        max_age=settings.SECURITY_REFRESH_TOKEN_EXPIRE_DAYS * 24 * 60 * 60,
    )


def _clear_auth_cookies(response: Response) -> None:
    response.delete_cookie(key=ACCESS_TOKEN_COOKIE, samesite="strict")
    response.delete_cookie(
        key=REFRESH_TOKEN_COOKIE,
        path=_REFRESH_COOKIE_PATH,
        samesite="strict",
    )


@router.post(
    "/register",
    response_model=schemas.UserResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Register a new user",
    description="""
    Creates a new user account with the provided email, password, and full name.

    Upon successful registration, use the credentials to login and obtain a JWT token.
    """,
    responses={
        400: {
            "model": schemas.ErrorResponse,
            "description": "Registration failed",
        },
        422: {
            "model": schemas.ErrorResponse,
            "description": "Validation error (weak password, invalid email)",
        },
        429: {"model": schemas.ErrorResponse, "description": "Rate limit exceeded"},
    },
)
@limiter.limit(rate_limits.AUTH_REGISTER)
async def register(
    request: Request,  # noqa: ARG001
    user: schemas.UserCreate,
    session: SessionDep,
) -> models.User:
    return await auth_service.register(user, session)


@router.post(
    "/login",
    response_model=schemas.UserResponse,
    summary="User login",
    description="""
    Authenticates a user with email and password. Sets `access_token` and
    `refresh_token` as HttpOnly cookies and returns the authenticated user.

    The access token cookie is sent automatically by the browser for all
    subsequent requests. Use `/auth/refresh` to rotate tokens when the
    access token expires.
    """,
    responses={
        401: {"model": schemas.ErrorResponse, "description": "Invalid credentials"},
        429: {
            "model": schemas.ErrorResponse,
            "description": "Rate limit exceeded or account locked",
        },
    },
)
@limiter.limit(rate_limits.AUTH_LOGIN)
async def login(
    request: Request,
    response: Response,
    form_data: Annotated[OAuth2PasswordRequestForm, Depends()],
    session: SessionDep,
    redis: RedisDep,
) -> models.User:
    client_ip = request.client.host if request.client else "unknown"
    await auth_service.check_login_locked(client_ip, form_data.username, redis)
    try:
        user = await auth_service.authenticate_user(
            form_data.username, form_data.password, session
        )
    except BearerAuthenticationError:
        await auth_service.record_failed_login(client_ip, form_data.username, redis)
        raise

    await auth_service.reset_login_attempts(form_data.username, client_ip, redis)
    tokens = auth_service.create_user_token(user)
    _set_auth_cookies(response, tokens.access_token, tokens.refresh_token)
    return user


@router.post(
    "/refresh",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Refresh access token",
    description="""
    Reads the `refresh_token` cookie, issues a new access + refresh token pair,
    and sets both as fresh HttpOnly cookies. The old refresh token is invalidated.
    """,
    responses={
        401: {
            "model": schemas.ErrorResponse,
            "description": "Invalid or expired refresh token",
        },
        429: {"model": schemas.ErrorResponse, "description": "Rate limit exceeded"},
    },
)
@limiter.limit(rate_limits.AUTH_REFRESH)
async def refresh_token(
    request: Request,
    response: Response,
    session: SessionDep,
) -> None:
    token = request.cookies.get(REFRESH_TOKEN_COOKIE)
    if not token:
        raise BearerAuthenticationError("Refresh token not found")
    tokens = await auth_service.refresh_user_token(token, session)
    _set_auth_cookies(response, tokens.access_token, tokens.refresh_token)


@router.post(
    "/logout",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Logout user",
    description="""
    Revokes all currently issued refresh tokens and clears auth cookies.
    """,
    responses={
        401: {"model": schemas.ErrorResponse, "description": "Not authenticated"},
    },
)
async def logout(
    response: Response,
    user: CurrentUserDep,
    session: SessionDep,
) -> None:
    await auth_service.logout(user.id, session)
    _clear_auth_cookies(response)
