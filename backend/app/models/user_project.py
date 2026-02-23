import uuid
from typing import TYPE_CHECKING

from sqlalchemy import Enum as SAEnum
from sqlalchemy import ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.enums import ProjectRole as ProjectRole
from app.models.base import Base, TimestampMixin

if TYPE_CHECKING:
    from app.models.project import Project
    from app.models.user import User


class UserProject(Base, TimestampMixin):
    """Junction table for user-project membership. Every user-project relationship
    (including ownership) is recorded here."""

    __tablename__ = "user_projects"

    user_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), primary_key=True
    )
    project_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("projects.id", ondelete="CASCADE"), primary_key=True
    )
    role: Mapped[ProjectRole] = mapped_column(
        SAEnum(ProjectRole, name="projectrole"), nullable=False
    )

    user: Mapped[User] = relationship(back_populates="shared_projects")
    project: Mapped[Project] = relationship(back_populates="members")
