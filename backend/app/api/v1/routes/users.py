from fastapi import APIRouter

from app import models, schemas
from app.dependencies import CurrentUserDep

router = APIRouter()


@router.get(
    "/me",
    response_model=schemas.UserResponse,
    summary="Get current user",
    description="""
    Retrieves the information of the currently authenticated user.
    """,
    responses={
        401: {"model": schemas.ErrorResponse, "description": "Not authenticated"},
    },
)
async def read_user_me(user: CurrentUserDep) -> models.User:
    return user
