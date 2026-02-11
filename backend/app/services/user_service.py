from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app import models


async def get_user_by_email(email: str, session: AsyncSession) -> models.User | None:
    stmt = select(models.User).where(models.User.email == email)
    return (await session.scalars(stmt)).one_or_none()
