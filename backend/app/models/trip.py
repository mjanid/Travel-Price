"""Trip ORM model."""

import enum
import uuid
from datetime import date, datetime, timezone

from sqlalchemy import Date, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base


class TripType(str, enum.Enum):
    """Supported trip categories."""

    FLIGHT = "flight"
    HOTEL = "hotel"
    CAR_RENTAL = "car_rental"


class Trip(Base):
    """A planned trip that a user wants to monitor prices for.

    Attributes:
        id: Unique identifier (UUID).
        user_id: Owner of this trip (FK to users).
        origin: Origin IATA airport code (e.g. 'JFK').
        destination: Destination IATA airport code (e.g. 'LAX').
        departure_date: Planned departure date.
        return_date: Planned return date (None for one-way trips).
        travelers: Number of travelers.
        trip_type: Category of trip (flight, hotel, car_rental).
        notes: Optional free-text notes.
        created_at: Record creation timestamp (UTC).
        updated_at: Last modification timestamp (UTC).
    """

    __tablename__ = "trips"

    id: Mapped[uuid.UUID] = mapped_column(
        primary_key=True, default=uuid.uuid4
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )
    origin: Mapped[str] = mapped_column(String(3), nullable=False)
    destination: Mapped[str] = mapped_column(String(3), nullable=False)
    departure_date: Mapped[date] = mapped_column(Date, nullable=False)
    return_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    travelers: Mapped[int] = mapped_column(Integer, default=1)
    trip_type: Mapped[str] = mapped_column(String(20), nullable=False, default=TripType.FLIGHT.value)
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        default=lambda: datetime.now(timezone.utc)
    )
    updated_at: Mapped[datetime] = mapped_column(
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
    )

    user = relationship("User", backref="trips")
