"""initial schema

Revision ID: ba576db9eaf0
Revises:
Create Date: 2026-02-11 19:45:22.768427

"""

from collections.abc import Sequence

# revision identifiers, used by Alembic.
revision: str = "ba576db9eaf0"
down_revision: str | None = None
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    pass


def downgrade() -> None:
    pass
