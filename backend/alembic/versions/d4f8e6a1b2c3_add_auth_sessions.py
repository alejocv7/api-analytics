"""add auth_sessions

Revision ID: d4f8e6a1b2c3
Revises: b1e2f3a4c5d6
Create Date: 2026-03-24 00:00:00.000000

"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

import app.models

# revision identifiers, used by Alembic.
revision: str = "d4f8e6a1b2c3"
down_revision: Union[str, Sequence[str], None] = "b1e2f3a4c5d6"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "auth_sessions",
        sa.Column("id", sa.Uuid(), server_default=sa.text("gen_random_uuid()"), nullable=False),
        sa.Column("user_id", sa.Uuid(), nullable=False),
        sa.Column(
            "client_type",
            sa.Enum("web", "token", name="authsessionclienttype"),
            nullable=False,
        ),
        sa.Column("session_secret_hash", sa.String(), nullable=True),
        sa.Column("refresh_token_hash", sa.String(), nullable=True),
        sa.Column("last_used_at", app.models.base.UTCDateTime(timezone=True), nullable=True),
        sa.Column("expires_at", app.models.base.UTCDateTime(timezone=True), nullable=False),
        sa.Column("revoked_at", app.models.base.UTCDateTime(timezone=True), nullable=True),
        sa.Column("user_agent", sa.String(), nullable=True),
        sa.Column("ip_hash", sa.String(), nullable=True),
        sa.Column(
            "created_at",
            app.models.base.UTCDateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column("updated_at", app.models.base.UTCDateTime(timezone=True), nullable=True),
        sa.CheckConstraint(
            "(client_type = 'web' AND refresh_token_hash IS NULL"
            " AND (session_secret_hash IS NOT NULL OR revoked_at IS NOT NULL))"
            " OR (client_type = 'token' AND session_secret_hash IS NULL"
            " AND (refresh_token_hash IS NOT NULL OR revoked_at IS NOT NULL))",
            name="ck_auth_sessions_hash_per_client_type",
        ),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_auth_sessions_created_at"), "auth_sessions", ["created_at"], unique=False)
    op.create_index(op.f("ix_auth_sessions_id"), "auth_sessions", ["id"], unique=False)
    op.create_index(op.f("ix_auth_sessions_user_id"), "auth_sessions", ["user_id"], unique=False)
    op.create_unique_constraint(
        "uq_auth_sessions_session_secret_hash",
        "auth_sessions",
        ["session_secret_hash"],
    )
    op.create_unique_constraint(
        "uq_auth_sessions_refresh_token_hash",
        "auth_sessions",
        ["refresh_token_hash"],
    )
    op.drop_column("users", "refresh_token_version")


def downgrade() -> None:
    op.add_column(
        "users",
        sa.Column("refresh_token_version", sa.Integer(), server_default="0", nullable=False),
    )
    op.drop_constraint("uq_auth_sessions_refresh_token_hash", "auth_sessions", type_="unique")
    op.drop_constraint("uq_auth_sessions_session_secret_hash", "auth_sessions", type_="unique")
    op.drop_index(op.f("ix_auth_sessions_user_id"), table_name="auth_sessions")
    op.drop_index(op.f("ix_auth_sessions_id"), table_name="auth_sessions")
    op.drop_index(op.f("ix_auth_sessions_created_at"), table_name="auth_sessions")
    op.drop_table("auth_sessions")
    op.execute("DROP TYPE authsessionclienttype")
