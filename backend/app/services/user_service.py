from sqlalchemy import select

from app import models
from app.dependencies import SessionDep


async def get_user_by_email(email: str, session: SessionDep) -> models.User | None:
    stmt = select(models.User).where(models.User.email == email)
    result = await session.execute(stmt)
    return result.scalar_one_or_none()
