"""Shared type definitions for the scraping subsystem."""

from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from datetime import date, datetime, timezone


@dataclass
class ScrapeQuery:
    """Input parameters for a scrape operation.

    Attributes:
        origin: Origin IATA airport code.
        destination: Destination IATA airport code.
        departure_date: Planned departure date.
        return_date: Planned return date (None for one-way).
        travelers: Number of travelers.
        cabin_class: Desired cabin class.
        trip_id: Associated trip ID (set by service layer).
        user_id: Associated user ID (set by service layer).
    """

    origin: str
    destination: str
    departure_date: date
    return_date: date | None = None
    travelers: int = 1
    cabin_class: str = "economy"
    trip_id: uuid.UUID | None = None
    user_id: uuid.UUID | None = None


@dataclass
class PriceResult:
    """A single price result returned by a scraper.

    Attributes:
        provider: The scraper provider name.
        price: Price in cents (integer).
        currency: ISO 4217 currency code.
        cabin_class: Cabin class for this result.
        airline: Airline name, if available.
        outbound_departure: Outbound departure datetime (UTC).
        outbound_arrival: Outbound arrival datetime (UTC).
        return_departure: Return departure datetime (UTC).
        return_arrival: Return arrival datetime (UTC).
        stops: Number of stops.
        raw_data: Raw provider data for debugging.
        scraped_at: When the price was scraped (UTC).
    """

    provider: str
    price: int
    currency: str = "USD"
    cabin_class: str | None = None
    airline: str | None = None
    outbound_departure: datetime | None = None
    outbound_arrival: datetime | None = None
    return_departure: datetime | None = None
    return_arrival: datetime | None = None
    stops: int | None = None
    raw_data: dict | None = field(default=None, repr=False)
    scraped_at: datetime = field(
        default_factory=lambda: datetime.now(timezone.utc)
    )


class ScrapeError(Exception):
    """Raised when a scrape operation fails after all retries.

    Attributes:
        provider: The scraper provider that failed.
        message: Human-readable error description.
        retries: Number of retries attempted before failure.
    """

    def __init__(self, provider: str, message: str, retries: int = 0) -> None:
        self.provider = provider
        self.retries = retries
        super().__init__(f"[{provider}] {message} (after {retries} retries)")
