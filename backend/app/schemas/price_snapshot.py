"""Request and response schemas for price snapshot endpoints."""

import uuid
from datetime import datetime

from pydantic import BaseModel, Field


class ScrapeRequest(BaseModel):
    """Schema for triggering a manual scrape.

    Attributes:
        provider: Scraper provider to use.
        cabin_class: Desired cabin class.
    """

    provider: str = Field(default="google_flights", max_length=50)
    cabin_class: str = Field(default="economy", max_length=20)


class PriceSnapshotResponse(BaseModel):
    """Schema for price snapshot data in API responses.

    Attributes:
        id: Unique identifier.
        trip_id: Associated trip ID.
        provider: Scraper provider name.
        price: Price in cents.
        currency: ISO 4217 currency code.
        cabin_class: Cabin class (economy, business, first).
        airline: Airline name if available.
        outbound_departure: Outbound departure time.
        outbound_arrival: Outbound arrival time.
        return_departure: Return departure time.
        return_arrival: Return arrival time.
        stops: Number of stops.
        scraped_at: When the price was scraped.
        created_at: Record creation time.
    """

    id: uuid.UUID
    trip_id: uuid.UUID
    provider: str
    price: int
    currency: str
    cabin_class: str | None
    airline: str | None
    outbound_departure: datetime | None
    outbound_arrival: datetime | None
    return_departure: datetime | None
    return_arrival: datetime | None
    stops: int | None
    raw_data: str | None = None
    scraped_at: datetime
    created_at: datetime

    model_config = {"from_attributes": True}
