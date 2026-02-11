"""Replace card fields with tcgdex fields

Revision ID: c3a1f2d4e5b6
Revises: ba576db9eaf0
Create Date: 2026-02-11 22:00:00.000000

"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = "c3a1f2d4e5b6"
down_revision: str | None = "ba576db9eaf0"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    with op.batch_alter_table("cards") as batch_op:
        batch_op.drop_column("description")
        batch_op.drop_column("attack")
        batch_op.drop_column("defense")
        batch_op.drop_column("cost")
        batch_op.add_column(sa.Column("tcgdex_id", sa.String(50), nullable=False))
        batch_op.add_column(sa.Column("image_url", sa.String(500), nullable=True))
        batch_op.create_unique_constraint("uq_cards_tcgdex_id", ["tcgdex_id"])


def downgrade() -> None:
    with op.batch_alter_table("cards") as batch_op:
        batch_op.drop_constraint("uq_cards_tcgdex_id", type_="unique")
        batch_op.drop_column("image_url")
        batch_op.drop_column("tcgdex_id")
        batch_op.add_column(sa.Column("description", sa.Text, nullable=False, server_default=""))
        batch_op.add_column(sa.Column("attack", sa.Integer, nullable=False, server_default="0"))
        batch_op.add_column(sa.Column("defense", sa.Integer, nullable=False, server_default="0"))
        batch_op.add_column(sa.Column("cost", sa.Integer, nullable=False, server_default="0"))
