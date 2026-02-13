"""PriceWatch ORM model for monitoring price targets."""

import uuid
from datetime import datetime, timezone

from sqlalchemy import Boolean, ForeignKey, Integer, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base


class PriceWatch(Base):
    """A monitoring rule that triggers alerts when prices drop below a target.

    Attributes:
        id: Unique identifier (UUID).
        user_id: Owner of this watch (FK to users).
        trip_id: Trip being monitored (FK to trips).
        provider: Scraper provider to monitor (e.g. 'google_flights').
        target_price: Alert threshold in cents.
        currency: ISO 4217 currency code.
        is_active: Whether this watch is actively monitoring.
        alert_cooldown_hours: Minimum hours between alerts for this watch.
        created_at: Record creation timestamp (UTC).
        updated_at: Last modification timestamp (UTC).
    """

    __tablename__ = "price_watches"

    id: Mapped[uuid.UUID] = mapped_column(
        primary_key=True, default=uuid.uuid4
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )
    trip_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("trips.id", ondelete="CASCADE"), nullable=False, index=True
    )
    provider: Mapped[str] = mapped_column(
        String(50), nullable=False, default="google_flights"
    )
    target_price: Mapped[int] = mapped_column(Integer, nullable=False)
    currency: Mapped[str] = mapped_column(String(3), nullable=False, default="USD")
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    alert_cooldown_hours: Mapped[int] = mapped_column(Integer, default=6)
    created_at: Mapped[datetime] = mapped_column(
        default=lambda: datetime.now(timezone.utc).replace(tzinfo=None)
    )
    updated_at: Mapped[datetime] = mapped_column(
        default=lambda: datetime.now(timezone.utc).replace(tzinfo=None),
        onupdate=lambda: datetime.now(timezone.utc).replace(tzinfo=None),
    )

    trip = relationship("Trip", backref="price_watches")
    user = relationship("User", backref="price_watches")
