
"""Add last_alerted_at to price_watches.

Revision ID: 002_pw_last_alerted_at
Revises: 001_initial
Create Date: 2026-02-09
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = "002_pw_last_alerted_at"
down_revision: Union[str, None] = "001_initial"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

def upgrade() -> None:
    op.add_column(
        "price_watches",
        sa.Column("last_alerted_at", sa.DateTime(timezone=True), nullable=True),
    )

def downgrade() -> None:
    op.drop_column("price_watches", "last_alerted_at")
