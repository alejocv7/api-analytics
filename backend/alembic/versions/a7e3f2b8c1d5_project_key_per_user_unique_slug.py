"""project_key: per-user unique slug, normalized name uniqueness

Revision ID: a7e3f2b8c1d5
Revises: 4cad5c74dd8c
Create Date: 2026-03-18 00:00:00.000000

"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = "a7e3f2b8c1d5"
down_revision: Union[str, Sequence[str], None] = "4cad5c74dd8c"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema.

    project_key changes:
      - Drop the globally-unique index; add a per-user unique constraint on
        (user_id, project_key).  Lookups are always user-scoped so global
        uniqueness was never required.
      - Shrink column from String(45) to String(40) to match the max name length.

    project name uniqueness changes:
      - Drop the exact-match case-sensitive constraint uq_user_project_name.
      - Add a functional unique index that normalises the name to lowercase with
        whitespace collapsed to a single space before comparing, matching GitHub's
        repository-name uniqueness behaviour.  "My API", "my api", and "MY  API"
        all conflict under this rule.

    No data migration is required (no deployed data exists).
    """
    # --- project_key ---
    op.drop_index(op.f("ix_projects_project_key"), table_name="projects")
    op.create_unique_constraint(
        "uq_user_project_key", "projects", ["user_id", "project_key"]
    )
    op.alter_column(
        "projects",
        "project_key",
        existing_type=sa.String(length=45),
        type_=sa.String(length=40),
        existing_nullable=False,
    )

    # --- project name: case-insensitive + whitespace-collapsed uniqueness ---
    op.drop_constraint("uq_user_project_name", "projects", type_="unique")
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


def downgrade() -> None:
    """Downgrade schema.

    Reverses all constraint and column-type changes.  project_key values are
    not restored to their original "slug-suffix" format.
    """
    op.execute(
        sa.text("DROP INDEX IF EXISTS uq_user_project_name_normalized")
    )
    op.create_unique_constraint(
        "uq_user_project_name", "projects", ["user_id", "name"]
    )

    op.alter_column(
        "projects",
        "project_key",
        existing_type=sa.String(length=40),
        type_=sa.String(length=45),
        existing_nullable=False,
    )
    op.drop_constraint("uq_user_project_key", "projects", type_="unique")
    op.create_index(
        op.f("ix_projects_project_key"), "projects", ["project_key"], unique=True
    )
