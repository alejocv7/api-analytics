from app import models
from app.dependencies import SessionDep
from sqlalchemy import select


def get_user_by_email(email: str, session: SessionDep) -> models.User | None:
    stmt = select(models.User).where(models.User.email == email)
    return session.execute(stmt).scalar_one_or_none()
