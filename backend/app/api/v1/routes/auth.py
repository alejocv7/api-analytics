from fastapi import APIRouter, Request, status

from app import models, schemas
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
)
@limiter.limit("5/minute")
async def register(
    request: Request, user: schemas.UserCreate, session: SessionDep
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
)
@limiter.limit("10/minute")
async def login(
    request: Request, user_login: schemas.LoginRequest, session: SessionDep
) -> schemas.TokenResponse:
    user = await auth_service.authenticate_user(
        user_login.email, user_login.password.get_secret_value(), session
    )
    return auth_service.create_user_token(user)
