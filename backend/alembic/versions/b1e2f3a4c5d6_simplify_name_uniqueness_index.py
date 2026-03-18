"""simplify name uniqueness index to lower(name)

Revision ID: b1e2f3a4c5d6
Revises: a7e3f2b8c1d5
Create Date: 2026-03-18 00:00:00.000000

"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = "b1e2f3a4c5d6"
down_revision: Union[str, Sequence[str], None] = "a7e3f2b8c1d5"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Simplify the name uniqueness index.

    Project names are now pre-normalized on save (trimmed, internal whitespace
    collapsed to a single space) by the model's @validates handler. The
    functional index no longer needs regexp_replace/trim — lower(name) is
    sufficient.

    No data migration is required (no deployed data exists).
    """
    op.execute(sa.text("DROP INDEX uq_user_project_name_normalized"))
    op.execute(
        sa.text(
            "CREATE UNIQUE INDEX uq_user_project_name_normalized"
            " ON projects (user_id, lower(name))"
        )
    )


def downgrade() -> None:
    """Restore the full normalization expression index."""
    op.execute(sa.text("DROP INDEX uq_user_project_name_normalized"))
    op.execute(
        sa.text(
            """
            CREATE UNIQUE INDEX uq_user_project_name_normalized
            ON projects (
                user_id,
                lower(regexp_replace(trim(name), '\\s+', ' ', 'g'))
            )
            """
        )
    )
