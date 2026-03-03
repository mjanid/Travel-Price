"""Make all created_at and updated_at columns timezone-aware.

Converts TIMESTAMP WITHOUT TIME ZONE columns to TIMESTAMP WITH TIME ZONE
across all tables. Existing naive UTC values are preserved — PostgreSQL
treats them as UTC when converting to TIMESTAMPTZ.

Revision ID: 003_tz_aware_timestamps
Revises: 002_pw_last_alerted_at
Create Date: 2026-03-03
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = "003_tz_aware_timestamps"
down_revision: Union[str, None] = "002_pw_last_alerted_at"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

# All (table, column) pairs that need to be converted
_COLUMNS = [
    ("users", "created_at"),
    ("users", "updated_at"),
    ("trips", "created_at"),
    ("trips", "updated_at"),
    ("price_watches", "created_at"),
    ("price_watches", "updated_at"),
    ("price_snapshots", "created_at"),
    ("alerts", "created_at"),
]


def upgrade() -> None:
    for table, column in _COLUMNS:
        op.alter_column(
            table,
            column,
            type_=sa.DateTime(timezone=True),
            existing_type=sa.DateTime(),
            existing_nullable=False if column == "created_at" else True,
        )


def downgrade() -> None:
    for table, column in _COLUMNS:
        op.alter_column(
            table,
            column,
            type_=sa.DateTime(),
            existing_type=sa.DateTime(timezone=True),
            existing_nullable=False if column == "created_at" else True,
        )
