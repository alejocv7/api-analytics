from fastapi import APIRouter, status

from app import schemas
from app.dependencies import SessionDep
from app.services import auth

router = APIRouter()


@router.post(
    "/register",
    response_model=schemas.UserResponse,
    status_code=status.HTTP_201_CREATED,
)
async def register(user: schemas.UserCreate, session: SessionDep):
    return auth.register(user, session)


@router.post("/login", response_model=schemas.TokenResponse)
async def login(user_login: schemas.LoginRequest, session: SessionDep):
    return auth.login(user_login, session)
