"""cascade project owner fk

Revision ID: f3a9b2c1d8e4
Revises: ef32e74f4050
Create Date: 2026-02-18 02:00:00.000000

"""
from typing import Sequence, Union

from alembic import op


# revision identifiers, used by Alembic.
revision: str = 'f3a9b2c1d8e4'
down_revision: Union[str, Sequence[str], None] = 'ef32e74f4050'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.drop_constraint('projects_user_id_fkey', 'projects', type_='foreignkey')
    op.create_foreign_key(None, 'projects', 'users', ['user_id'], ['id'], ondelete='CASCADE')


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_constraint('projects_user_id_fkey', 'projects', type_='foreignkey')
    op.create_foreign_key(None, 'projects', 'users', ['user_id'], ['id'])
