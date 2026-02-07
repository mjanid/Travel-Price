"""Request and response schemas for trip endpoints."""

import uuid
from datetime import date, datetime

from pydantic import BaseModel, Field, field_validator

from app.models.trip import TripType


class TripCreateRequest(BaseModel):
    """Schema for creating a new trip.

    Attributes:
        origin: Origin IATA airport code (3 uppercase letters).
        destination: Destination IATA airport code (3 uppercase letters).
        departure_date: Planned departure date.
        return_date: Planned return date (optional for one-way).
        travelers: Number of travelers (>= 1).
        trip_type: Category of trip.
        notes: Optional free-text notes.
    """

    origin: str = Field(min_length=3, max_length=3)
    destination: str = Field(min_length=3, max_length=3)
    departure_date: date
    return_date: date | None = None
    travelers: int = Field(default=1, ge=1, le=20)
    trip_type: TripType = TripType.FLIGHT
    notes: str | None = Field(default=None, max_length=2000)

    @field_validator("origin", "destination")
    @classmethod
    def validate_iata_code(cls, v: str) -> str:
        """Ensure IATA codes are uppercase alphabetic."""
        v = v.upper()
        if not v.isalpha():
            raise ValueError("IATA code must contain only letters")
        return v

    @field_validator("return_date")
    @classmethod
    def return_after_departure(cls, v: date | None, info) -> date | None:
        """Ensure return date is after departure date."""
        if v is not None and "departure_date" in info.data:
            if v <= info.data["departure_date"]:
                raise ValueError("return_date must be after departure_date")
        return v


class TripUpdateRequest(BaseModel):
    """Schema for partially updating a trip. All fields optional."""

    origin: str | None = Field(default=None, min_length=3, max_length=3)
    destination: str | None = Field(default=None, min_length=3, max_length=3)
    departure_date: date | None = None
    return_date: date | None = None
    travelers: int | None = Field(default=None, ge=1, le=20)
    trip_type: TripType | None = None
    notes: str | None = Field(default=None, max_length=2000)

    @field_validator("origin", "destination")
    @classmethod
    def validate_iata_code(cls, v: str | None) -> str | None:
        """Ensure IATA codes are uppercase alphabetic."""
        if v is None:
            return v
        v = v.upper()
        if not v.isalpha():
            raise ValueError("IATA code must contain only letters")
        return v


class TripResponse(BaseModel):
    """Schema for trip data in API responses."""

    id: uuid.UUID
    user_id: uuid.UUID
    origin: str
    destination: str
    departure_date: date
    return_date: date | None
    travelers: int
    trip_type: str
    notes: str | None
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}
