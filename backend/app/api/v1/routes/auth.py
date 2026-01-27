from fastapi import APIRouter, status

from app import schemas
from app.crud import auth
from app.dependencies import SessionDep

router = APIRouter()


@router.post(
    "/register",
    response_model=schemas.UserResponse,
    status_code=status.HTTP_201_CREATED,
)
async def register(user: schemas.UserCreate, session: SessionDep):
    return auth.register(user, session)


@router.post("/login", response_model=schemas.Token)
async def login(user_login: schemas.UserLogin, session: SessionDep):
    return auth.login(user_login, session)
