"""Request and response schemas for price watch endpoints."""

import uuid
from datetime import datetime
from typing import Literal

from pydantic import BaseModel, Field

ALLOWED_PROVIDERS = Literal["google_flights"]
ALLOWED_CURRENCIES = Literal["USD", "EUR", "GBP", "CAD", "AUD", "JPY", "INR", "BRL", "MXN"]


class PriceWatchCreateRequest(BaseModel):
    """Schema for creating a new price watch.

    Attributes:
        trip_id: The trip to monitor.
        provider: Scraper provider name (must match a registered scraper).
        target_price: Alert threshold in cents (must be positive).
        currency: ISO 4217 currency code (supported currencies only).
        alert_cooldown_hours: Minimum hours between alerts.
    """

    trip_id: uuid.UUID
    provider: ALLOWED_PROVIDERS = "google_flights"
    target_price: int = Field(gt=0)
    currency: ALLOWED_CURRENCIES = "USD"
    alert_cooldown_hours: int = Field(default=6, ge=1, le=168)


class PriceWatchUpdateRequest(BaseModel):
    """Schema for partially updating a price watch. All fields optional."""

    target_price: int | None = Field(default=None, gt=0)
    is_active: bool | None = None
    alert_cooldown_hours: int | None = Field(default=None, ge=1, le=168)


class PriceWatchResponse(BaseModel):
    """Schema for price watch data in API responses."""

    id: uuid.UUID
    user_id: uuid.UUID
    trip_id: uuid.UUID
    provider: str
    target_price: int
    currency: str
    is_active: bool
    alert_cooldown_hours: int
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}
