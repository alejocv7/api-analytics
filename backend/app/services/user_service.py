from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app import models
from app.core.exceptions import NotFoundError


async def find_user_by_email(email: str, session: AsyncSession) -> models.User | None:
    """Find a user by email. Returns None if not found."""
    result = await session.scalars(
        select(models.User).where(models.User.email == email)
    )
    return result.one_or_none()


async def get_user_by_email(email: str, session: AsyncSession) -> models.User:
    """Get a user by email. Raises NotFoundError if not found."""
    user = await find_user_by_email(email, session)
    if not user:
        raise NotFoundError("User not found")
    return user
