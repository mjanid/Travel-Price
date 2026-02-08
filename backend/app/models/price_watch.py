"""PriceWatch ORM model."""

import uuid
from datetime import datetime, timezone

from sqlalchemy import Boolean, ForeignKey, Integer, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base


class PriceWatch(Base):
    """A monitoring rule that tracks prices for a trip on a specific provider.

    Attributes:
        id: Unique identifier (UUID).
        trip_id: The trip being monitored (FK to trips).
        provider: Price source identifier (e.g. 'google_flights', 'kayak').
        target_price: Target price threshold in cents.
        currency: ISO 4217 currency code (default 'USD').
        is_active: Whether this watch is actively being monitored.
        alert_cooldown_hours: Minimum hours between alerts for this watch.
        last_alerted_at: Timestamp of the most recent alert sent.
        created_at: Record creation timestamp (UTC).
        updated_at: Last modification timestamp (UTC).
    """

    __tablename__ = "price_watches"

    id: Mapped[uuid.UUID] = mapped_column(
        primary_key=True, default=uuid.uuid4
    )
    trip_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("trips.id", ondelete="CASCADE"), nullable=False, index=True
    )
    provider: Mapped[str] = mapped_column(String(50), nullable=False)
    target_price: Mapped[int] = mapped_column(Integer, nullable=False)
    currency: Mapped[str] = mapped_column(String(3), nullable=False, default="USD")
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    alert_cooldown_hours: Mapped[int] = mapped_column(Integer, default=6)
    last_alerted_at: Mapped[datetime | None] = mapped_column(nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        default=lambda: datetime.now(timezone.utc)
    )
    updated_at: Mapped[datetime] = mapped_column(
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
    )

    trip = relationship("Trip", backref="price_watches")
