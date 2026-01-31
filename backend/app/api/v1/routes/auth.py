from fastapi import APIRouter, status

from app import schemas
from app.dependencies import SessionDep
from app.services import auth_service

router = APIRouter()


@router.post(
    "/register",
    response_model=schemas.UserResponse,
    status_code=status.HTTP_201_CREATED,
)
async def register(user: schemas.UserCreate, session: SessionDep):
    return auth_service.register(user, session)


@router.post("/login", response_model=schemas.TokenResponse)
async def login(user_login: schemas.LoginRequest, session: SessionDep):
    user = auth_service.authenticate_user(
        user_login.email, user_login.password, session
    )
    return auth_service.create_user_token(user)
