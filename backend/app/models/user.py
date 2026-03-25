import uuid
from typing import TYPE_CHECKING

from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, TimestampMixin

if TYPE_CHECKING:
    from app.models.auth_session import AuthSession
    from app.models.project import Project
    from app.models.user_project import UserProject


class User(Base, TimestampMixin):
    """User accounts - people who sign up for the analytics service."""

    __tablename__ = "users"

    id: Mapped[uuid.UUID] = mapped_column(
        primary_key=True, default=uuid.uuid4, index=True
    )

    email: Mapped[str] = mapped_column(unique=True, index=True)

    hashed_password: Mapped[str]

    full_name: Mapped[str | None]

    is_active: Mapped[bool] = mapped_column(default=True)

    owned_projects: Mapped[list[Project]] = relationship(
        back_populates="owner", cascade="all, delete-orphan"
    )

    shared_projects: Mapped[list[UserProject]] = relationship(
        back_populates="user", cascade="all, delete-orphan"
    )

    auth_sessions: Mapped[list[AuthSession]] = relationship(
        back_populates="user", cascade="all, delete-orphan"
    )
