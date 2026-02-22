"""add refresh token version to users

Revision ID: c2d9a91f74ab
Revises: f3a9b2c1d8e4
Create Date: 2026-02-22 00:00:00.000000

"""

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "c2d9a91f74ab"
down_revision: str | Sequence[str] | None = "61855b6d7550"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Upgrade schema."""
    op.add_column(
        "users",
        sa.Column(
            "refresh_token_version",
            sa.Integer(),
            nullable=False,
            server_default="0",
        ),
    )


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_column("users", "refresh_token_version")
