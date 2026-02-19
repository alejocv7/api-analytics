import secrets
from typing import TYPE_CHECKING, Any

from slugify import slugify
from sqlalchemy import ForeignKey, Index, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship, validates

from app.core.config import settings
from app.models.base import Base, TimestampMixin

if TYPE_CHECKING:
    from app.models.api_key import APIKey
    from app.models.metric import Metric
    from app.models.user import User
    from app.models.user_project import UserProject


class Project(Base, TimestampMixin):
    """Projects belong to users. Each project represents an app being tracked.

    The canonical owner is stored in `user_id`. All user-project relationships
    (including ownership) are also reflected in the `user_projects` junction table.
    """

    __tablename__ = "projects"

    id: Mapped[int] = mapped_column(primary_key=True)

    name: Mapped[str] = mapped_column(String(100), nullable=False)
    project_key: Mapped[str] = mapped_column(
        String(100 + 1 + settings.PROJECT_SUFFIX_LENGTH), unique=True, index=True
    )
    description: Mapped[str | None] = mapped_column(String(1000))

    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"),
        index=True,
    )
    owner: Mapped[User] = relationship(back_populates="owned_projects")

    members: Mapped[list[UserProject]] = relationship(
        back_populates="project", cascade="all, delete-orphan"
    )

    api_keys: Mapped[list[APIKey]] = relationship(
        back_populates="project", cascade="all, delete-orphan"
    )

    metrics: Mapped[list[Metric]] = relationship(
        back_populates="project", cascade="all, delete-orphan"
    )

    is_active: Mapped[bool] = mapped_column(default=True)

    __table_args__ = (
        UniqueConstraint("user_id", "name", name="uq_user_project_name"),
        Index("idx_project_user_active", "user_id", "is_active"),
    )

    def __init__(self, name: str, **kwargs: Any):
        if "project_key" not in kwargs:
            kwargs["project_key"] = (
                f"{slugify(name)}"
                f"-{secrets.token_hex(settings.PROJECT_SUFFIX_LENGTH // 2)}"
            )
        super().__init__(name=name, **kwargs)

    @validates("project_key")
    def protect_project_key(self, key: str, value: str) -> str:
        if self.project_key is not None:
            raise ValueError("project_key cannot be changed after it is set.")
        return value
