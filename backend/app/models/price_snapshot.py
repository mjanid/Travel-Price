"""PriceSnapshot ORM model for storing immutable scraped price records."""

import uuid
from datetime import datetime, timezone

from sqlalchemy import DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base


class PriceSnapshot(Base):
    """An immutable record of a scraped price from a travel provider.

    Attributes:
        id: Unique identifier (UUID).
        trip_id: The trip this price relates to (FK to trips).
        user_id: The user who owns this snapshot (FK to users).
        provider: Scraper provider name (e.g. 'google_flights').
        price: Price in cents to avoid floating-point issues.
        currency: ISO 4217 currency code (e.g. 'USD').
        cabin_class: Cabin class (economy, business, first) or None.
        airline: Airline name or None.
        outbound_departure: Outbound flight departure time or None.
        outbound_arrival: Outbound flight arrival time or None.
        return_departure: Return flight departure time or None.
        return_arrival: Return flight arrival time or None.
        stops: Number of stops or None.
        raw_data: Raw provider response as text (JSON) for debugging.
        scraped_at: When the price was scraped (UTC).
        created_at: Record creation timestamp (UTC).
    """

    __tablename__ = "price_snapshots"

    id: Mapped[uuid.UUID] = mapped_column(
        primary_key=True, default=uuid.uuid4
    )
    trip_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("trips.id", ondelete="CASCADE"), nullable=False, index=True
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )
    provider: Mapped[str] = mapped_column(String(50), nullable=False, index=True)
    price: Mapped[int] = mapped_column(Integer, nullable=False)
    currency: Mapped[str] = mapped_column(String(3), nullable=False, default="USD")
    cabin_class: Mapped[str | None] = mapped_column(String(20), nullable=True)
    airline: Mapped[str | None] = mapped_column(String(100), nullable=True)
    outbound_departure: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    outbound_arrival: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    return_departure: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    return_arrival: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    stops: Mapped[int | None] = mapped_column(Integer, nullable=True)
    raw_data: Mapped[str | None] = mapped_column(Text, nullable=True)
    scraped_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
    )
    created_at: Mapped[datetime] = mapped_column(
        default=lambda: datetime.now(timezone.utc).replace(tzinfo=None)
    )

    trip = relationship("Trip", backref="price_snapshots")
    user = relationship("User", backref="price_snapshots")
