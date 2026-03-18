import uuid
from typing import TYPE_CHECKING

from slugify import slugify
from sqlalchemy import ForeignKey, Index, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship, validates

from app.models.base import Base, TimestampMixin

if TYPE_CHECKING:
    from app.models.api_key import APIKey
    from app.models.metric import Metric
    from app.models.user import User
    from app.models.user_project import UserProject


class Project(Base, TimestampMixin):
    """Projects belong to users. Each project represents an app being tracked.

    The canonical owner is stored in `user_id`. All user-project relationships
    (including ownership) are also reflected in the `user_projects` junction table
    with roles `owner`/`member`/`viewer`.

    `project_key` is a URL-safe slug derived from the project name. It is unique
    per user and is updated automatically when the project is renamed. It is NOT
    the database primary key — `id` is.
    """

    __tablename__ = "projects"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)

    name: Mapped[str] = mapped_column(String(40), nullable=False)
    project_key: Mapped[str] = mapped_column(String(40), nullable=False)
    description: Mapped[str | None] = mapped_column(String(1000))

    user_id: Mapped[uuid.UUID] = mapped_column(
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
        UniqueConstraint("user_id", "project_key", name="uq_user_project_key"),
        # uq_user_project_name_normalized is a functional unique index on
        # (user_id, lower(name)) managed entirely by migrations. Names are
        # pre-normalized on save (trimmed, whitespace-collapsed) so only
        # lower() is needed. Omitted here to avoid Alembic autogenerate noise.
        Index("idx_project_user_active", "user_id", "is_active"),
    )

    @validates("name")
    def _normalize_name(self, key: str, name: str) -> str:
        normalized = " ".join(name.split())
        self.project_key = slugify(normalized)
        return normalized
