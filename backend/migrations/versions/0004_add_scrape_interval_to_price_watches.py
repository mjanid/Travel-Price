"""Add scrape_interval_minutes and next_scrape_at to price_watches.

Enables per-watch dynamic scrape intervals instead of a single global
SCRAPE_INTERVAL_MINUTES setting.  Each watch can now specify how often
it should be scraped (15-1440 minutes, default 60).

Revision ID: 004_scrape_interval
Revises: 003_tz_aware_timestamps
Create Date: 2026-03-03
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = "004_scrape_interval"
down_revision: Union[str, None] = "003_tz_aware_timestamps"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "price_watches",
        sa.Column(
            "scrape_interval_minutes",
            sa.Integer(),
            nullable=False,
            server_default=sa.text("60"),
        ),
    )
    op.add_column(
        "price_watches",
        sa.Column("next_scrape_at", sa.DateTime(timezone=True), nullable=True),
    )
    op.create_index(
        "ix_price_watches_next_scrape_at",
        "price_watches",
        ["next_scrape_at"],
    )


def downgrade() -> None:
    op.drop_index("ix_price_watches_next_scrape_at", table_name="price_watches")
    op.drop_column("price_watches", "next_scrape_at")
    op.drop_column("price_watches", "scrape_interval_minutes")
