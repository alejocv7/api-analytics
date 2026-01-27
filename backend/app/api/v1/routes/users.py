from fastapi import APIRouter

from app import schemas
from app.dependencies import CurrentUserDep

router = APIRouter()


@router.get("/me", response_model=schemas.UserResponse)
async def read_user_me(user: CurrentUserDep):
    return user
