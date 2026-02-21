from typing import Annotated

from fastapi import APIRouter, Depends, Request, status
from fastapi.security import OAuth2PasswordRequestForm

from app import models, schemas
from app.core import rate_limits
from app.core.rate_limiter import limiter
from app.dependencies import SessionDep
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
            "description": "Email already registered",
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
    Authenticates a user with email and password and returns a JWT access token.

    The returned token must be included in the `Authorization: Bearer <token>` header
    for all authenticated requests.
    """,
    responses={
        401: {"model": schemas.ErrorResponse, "description": "Invalid credentials"},
        429: {"model": schemas.ErrorResponse, "description": "Rate limit exceeded"},
    },
)
@limiter.limit(rate_limits.AUTH_LOGIN)
async def login(
    request: Request,  # noqa: ARG001
    form_data: Annotated[OAuth2PasswordRequestForm, Depends()],
    session: SessionDep,
) -> schemas.TokenResponse:
    user = await auth_service.authenticate_user(
        form_data.username, form_data.password, session
    )
    return auth_service.create_user_token(user)
