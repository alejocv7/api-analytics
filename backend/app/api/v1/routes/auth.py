from fastapi import APIRouter, status

from app import schemas
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
    
    Upon successful registration, you can use the credentials to login and obtain a JWT token.
    """,
)
async def register(user: schemas.UserCreate, session: SessionDep):
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
async def login(user_login: schemas.LoginRequest, session: SessionDep):
    user = await auth_service.authenticate_user(
        user_login.email, user_login.password, session
    )
    return auth_service.create_user_token(user)
