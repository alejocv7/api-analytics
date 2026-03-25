from typing import Annotated

from fastapi import APIRouter, Depends, Request, Response, status
from fastapi.security import OAuth2PasswordRequestForm

from app import models, schemas
from app.core import rate_limits
from app.core.config import settings
from app.core.cookies import SESSION_COOKIE
from app.core.enums import AuthSessionClientType
from app.core.exceptions import AuthenticationError
from app.core.rate_limiter import limiter
from app.dependencies import CurrentAuthDep, RedisDep, SessionDep
from app.services import auth_service

router = APIRouter()


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
    summary="Browser login",
    description="""
    Authenticates a browser user with email and password, sets an opaque
    HttpOnly session cookie, and returns the authenticated user.
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
    credentials: schemas.LoginRequest,
    session: SessionDep,
    redis: RedisDep,
) -> schemas.UserResponse:
    client_ip = request.client.host if request.client else "unknown"
    user = await auth_service.authenticate_with_lockout(
        credentials.email, credentials.password, client_ip, redis, session
    )
    _, session_secret = await auth_service.create_web_session(
        user,
        session,
        user_agent=request.headers.get("user-agent"),
        client_ip=client_ip,
    )
    _set_session_cookie(response, session_secret)
    return schemas.UserResponse.model_validate(user)


@router.post(
    "/logout",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Browser logout",
    description="""
    Revokes the current browser session and clears the session cookie.
    """,
    responses={
        401: {"model": schemas.ErrorResponse, "description": "Not authenticated"},
    },
)
async def logout(
    response: Response,
    auth: CurrentAuthDep,
    session: SessionDep,
) -> None:
    if auth.client_type != AuthSessionClientType.web:
        raise AuthenticationError("Not authenticated")
    await auth_service.revoke_session(auth.session_id, session)
    _clear_session_cookie(response)


@router.post(
    "/token/login",
    response_model=schemas.TokenLoginResponse,
    summary="Token client login",
    description="""
    Authenticates a token client and returns the user profile plus an access
    token and opaque refresh token.
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
async def token_login(
    request: Request,
    form_data: Annotated[OAuth2PasswordRequestForm, Depends()],
    session: SessionDep,
    redis: RedisDep,
) -> schemas.TokenLoginResponse:
    client_ip = request.client.host if request.client else "unknown"
    user = await auth_service.authenticate_with_lockout(
        form_data.username, form_data.password, client_ip, redis, session
    )
    return await auth_service.create_token_session(
        user,
        session,
        user_agent=request.headers.get("user-agent"),
        client_ip=client_ip,
    )


@router.post(
    "/token/refresh",
    response_model=schemas.TokenRefreshResponse,
    summary="Token client refresh",
    description="""
    Rotates the refresh token for the current token-client session and returns a
    fresh access token and refresh token.
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
async def token_refresh(
    request: Request,  # noqa: ARG001
    payload: schemas.TokenRefreshRequest,
    session: SessionDep,
) -> schemas.TokenRefreshResponse:
    return await auth_service.refresh_user_token(payload.refresh_token, session)


@router.post(
    "/token/logout",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Token client logout",
    description="""
    Revokes the current token-client session.
    """,
    responses={
        401: {"model": schemas.ErrorResponse, "description": "Not authenticated"},
    },
)
async def token_logout(
    auth: CurrentAuthDep,
    session: SessionDep,
) -> None:
    if auth.client_type != AuthSessionClientType.token:
        raise AuthenticationError("Not authenticated")
    await auth_service.revoke_session(auth.session_id, session)


def _set_session_cookie(response: Response, session_secret: str) -> None:
    response.set_cookie(
        key=SESSION_COOKIE,
        value=session_secret,
        httponly=True,
        secure=settings.cookie_secure,
        samesite="strict",
        max_age=settings.SECURITY_REFRESH_TOKEN_EXPIRE_DAYS * 24 * 60 * 60,
    )


def _clear_session_cookie(response: Response) -> None:
    response.delete_cookie(key=SESSION_COOKIE, samesite="strict")
