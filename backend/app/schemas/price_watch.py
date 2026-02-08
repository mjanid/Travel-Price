"""Request and response schemas for price watch endpoints."""

import uuid
from datetime import datetime

from pydantic import BaseModel, Field


class PriceWatchCreateRequest(BaseModel):
    """Schema for creating a new price watch.

    Attributes:
        provider: Price source identifier (e.g. 'google_flights').
        target_price: Target price threshold in cents (must be positive).
        currency: ISO 4217 currency code.
        is_active: Whether to start monitoring immediately.
        alert_cooldown_hours: Minimum hours between alerts.
    """

    provider: str = Field(min_length=1, max_length=50)
    target_price: int = Field(gt=0)
    currency: str = Field(default="USD", min_length=3, max_length=3)
    is_active: bool = True
    alert_cooldown_hours: int = Field(default=6, ge=1, le=168)

    @classmethod
    def __get_validators__(cls):
        yield cls.validate

    @classmethod
    def validate(cls, v):
        return v


class PriceWatchUpdateRequest(BaseModel):
    """Schema for partially updating a price watch. All fields optional."""

    provider: str | None = Field(default=None, min_length=1, max_length=50)
    target_price: int | None = Field(default=None, gt=0)
    currency: str | None = Field(default=None, min_length=3, max_length=3)
    is_active: bool | None = None
    alert_cooldown_hours: int | None = Field(default=None, ge=1, le=168)


class PriceWatchResponse(BaseModel):
    """Schema for price watch data in API responses."""

    id: uuid.UUID
    trip_id: uuid.UUID
    provider: str
    target_price: int
    currency: str
    is_active: bool
    alert_cooldown_hours: int
    last_alerted_at: datetime | None
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}
