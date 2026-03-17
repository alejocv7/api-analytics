from typing import Annotated

from fastapi import APIRouter, Depends, Request, status
from fastapi.security import OAuth2PasswordRequestForm

from app import models, schemas
from app.core import rate_limits
from app.core.exceptions import BearerAuthenticationError
from app.core.rate_limiter import limiter
from app.dependencies import RedisDep, SessionDep
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
    response_model=schemas.TokenResponse,
    summary="User login",
    description="""
    Authenticates a user with email and password and returns a JWT access token
    and a refresh token.

    The access token must be included in the `Authorization: Bearer <token>` header
    for all authenticated requests. Use the refresh token at `/auth/refresh` to
    obtain a new token pair when the access token expires.
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
    request: Request,  # noqa: ARG001
    form_data: Annotated[OAuth2PasswordRequestForm, Depends()],
    session: SessionDep,
    redis: RedisDep,
) -> schemas.TokenResponse:
    await auth_service.check_login_locked(form_data.username, redis)
    try:
        user = await auth_service.authenticate_user(
            form_data.username, form_data.password, session
        )
    except BearerAuthenticationError:
        await auth_service.record_failed_login(form_data.username, redis)
        raise

    await auth_service.reset_login_attempts(form_data.username, redis)
    return auth_service.create_user_token(user)


@router.post(
    "/refresh",
    response_model=schemas.TokenResponse,
    summary="Refresh access token",
    description="""
    Exchanges a valid refresh token for a new access token and refresh token pair.

    Both tokens are rotated on every call. The client should replace both stored tokens
    with the newly issued pair.
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
    request: Request,  # noqa: ARG001
    body: schemas.RefreshTokenRequest,
    session: SessionDep,
) -> schemas.TokenResponse:
    return await auth_service.refresh_user_token(body.refresh_token, session)
