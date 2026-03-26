import uuid
from datetime import UTC, datetime, timedelta
from typing import TYPE_CHECKING

from sqlalchemy import CheckConstraint, ColumnElement, ForeignKey, and_, func, text
from sqlalchemy.ext.hybrid import hybrid_property
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.config import settings
from app.core.enums import AuthSessionClientType
from app.models.base import Base, TimestampMixin

if TYPE_CHECKING:
    from app.models.user import User


class AuthSession(Base, TimestampMixin):
    __tablename__ = "auth_sessions"
    __table_args__ = (
        CheckConstraint(
            "(client_type = 'web' AND refresh_token_hash IS NULL"
            " AND (session_secret_hash IS NOT NULL OR revoked_at IS NOT NULL))"
            " OR (client_type = 'token' AND session_secret_hash IS NULL"
            " AND (refresh_token_hash IS NOT NULL OR revoked_at IS NOT NULL))",
            name="ck_auth_sessions_hash_per_client_type",
        ),
    )

    id: Mapped[uuid.UUID] = mapped_column(
        primary_key=True, server_default=text("gen_random_uuid()"), index=True
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), index=True
    )
    client_type: Mapped[AuthSessionClientType]
    session_secret_hash: Mapped[str | None] = mapped_column(unique=True)
    refresh_token_hash: Mapped[str | None] = mapped_column(unique=True)
    last_used_at: Mapped[datetime] = mapped_column(default=lambda: datetime.now(UTC))
    expires_at: Mapped[datetime] = mapped_column(
        default=lambda: (
            datetime.now(UTC)
            + timedelta(days=settings.SECURITY_REFRESH_TOKEN_EXPIRE_DAYS)
        )
    )
    revoked_at: Mapped[datetime | None]
    user_agent: Mapped[str | None]
    ip_hash: Mapped[str | None]

    user: Mapped[User] = relationship(back_populates="auth_sessions")

    @classmethod
    def create_web(
        cls,
        *,
        user_id: uuid.UUID,
        session_secret_hash: str,
        user_agent: str | None = None,
        ip_hash: str | None = None,
    ) -> AuthSession:
        return cls(
            user_id=user_id,
            client_type=AuthSessionClientType.web,
            session_secret_hash=session_secret_hash,
            user_agent=user_agent,
            ip_hash=ip_hash,
        )

    @classmethod
    def create_token(
        cls,
        *,
        user_id: uuid.UUID,
        refresh_token_hash: str,
        user_agent: str | None = None,
        ip_hash: str | None = None,
    ) -> AuthSession:
        return cls(
            user_id=user_id,
            client_type=AuthSessionClientType.token,
            refresh_token_hash=refresh_token_hash,
            user_agent=user_agent,
            ip_hash=ip_hash,
        )

    @hybrid_property
    def is_active(self) -> bool:
        return self.revoked_at is None and self.expires_at > datetime.now(UTC)

    @is_active.inplace.expression
    @classmethod
    def _is_active_expression(cls) -> ColumnElement[bool]:
        return and_(cls.revoked_at.is_(None), cls.expires_at > func.now())

    def revoke(self) -> None:
        self.revoked_at = datetime.now(UTC)
        self.session_secret_hash = None
        self.refresh_token_hash = None
        self.last_used_at = self.revoked_at

    def record_usage(self) -> None:
        self.last_used_at = datetime.now(UTC)
