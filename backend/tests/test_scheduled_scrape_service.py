"""Tests for ScheduledScrapeService."""

import uuid
from datetime import date, datetime, timezone
from unittest.mock import AsyncMock, patch

import pytest
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.price_snapshot import PriceSnapshot
from app.models.trip import Trip
from app.models.user import User
from app.scrapers.types import PriceResult, ScrapeError
from app.services.scheduled_scrape_service import ScheduledScrapeService


async def _create_user(db: AsyncSession, email: str = "worker@example.com") -> User:
    """Create a test user."""
    user = User(
        email=email,
        hashed_password="fakehash",
        full_name="Worker Tester",
    )
    db.add(user)
    await db.flush()
    await db.refresh(user)
    return user


async def _create_trip(
    db: AsyncSession,
    user_id: uuid.UUID,
    departure_date: date | None = None,
    return_date: date | None = None,
) -> Trip:
    """Create a test trip."""
    trip = Trip(
        user_id=user_id,
        origin="JFK",
        destination="LAX",
        departure_date=departure_date or date(2027, 6, 15),
        return_date=return_date or date(2027, 6, 22),
        travelers=2,
        trip_type="flight",
    )
    db.add(trip)
    await db.flush()
    await db.refresh(trip)
    return trip


def _mock_price_results(provider: str = "google_flights") -> list[PriceResult]:
    """Return mock price results."""
    now = datetime.now(timezone.utc)
    return [
        PriceResult(
            provider=provider,
            price=25000,
            currency="USD",
            cabin_class="economy",
            airline="Delta",
            stops=0,
            scraped_at=now,
        ),
        PriceResult(
            provider=provider,
            price=35000,
            currency="USD",
            cabin_class="economy",
            airline="United",
            stops=1,
            scraped_at=now,
        ),
    ]


# --- get_active_trip_ids tests ---


async def test_get_active_trip_ids_returns_future_trips(db_session):
    """Only trips with departure_date >= today are returned."""
    user = await _create_user(db_session)

    # Future trip
    future_trip = await _create_trip(db_session, user.id, departure_date=date(2027, 12, 1))
    # Past trip
    await _create_trip(db_session, user.id, departure_date=date(2020, 1, 1))

    service = ScheduledScrapeService(db_session)
    trip_ids = await service.get_active_trip_ids()

    assert len(trip_ids) == 1
    assert trip_ids[0][0] == future_trip.id
    assert trip_ids[0][1] == user.id


async def test_get_active_trip_ids_empty_when_no_trips(db_session):
    """Returns empty list when no trips exist."""
    service = ScheduledScrapeService(db_session)
    trip_ids = await service.get_active_trip_ids()
    assert trip_ids == []


async def test_get_active_trip_ids_empty_when_all_past(db_session):
    """Returns empty list when all trips are in the past."""
    user = await _create_user(db_session)
    await _create_trip(db_session, user.id, departure_date=date(2020, 1, 1))
    await _create_trip(db_session, user.id, departure_date=date(2021, 6, 1))

    service = ScheduledScrapeService(db_session)
    trip_ids = await service.get_active_trip_ids()
    assert trip_ids == []


async def test_get_active_trip_ids_multiple_users(db_session):
    """Returns trips from all users."""
    user1 = await _create_user(db_session, email="user1@example.com")
    user2 = await _create_user(db_session, email="user2@example.com")
    trip1 = await _create_trip(db_session, user1.id)
    trip2 = await _create_trip(db_session, user2.id)

    service = ScheduledScrapeService(db_session)
    trip_ids = await service.get_active_trip_ids()

    assert len(trip_ids) == 2
    ids = {t[0] for t in trip_ids}
    assert trip1.id in ids
    assert trip2.id in ids


# --- scrape_trip_background tests ---


async def test_scrape_trip_background_stores_snapshots(db_session):
    """Successful scrape stores snapshots and returns count."""
    user = await _create_user(db_session)
    trip = await _create_trip(db_session, user.id)

    mock_scraper = AsyncMock()
    mock_scraper.execute.return_value = _mock_price_results()

    with patch(
        "app.services.scheduled_scrape_service.get_scraper",
        return_value=mock_scraper,
    ):
        service = ScheduledScrapeService(db_session)
        count = await service.scrape_trip_background(trip.id, user.id)

    assert count == 2

    # Verify snapshots in DB
    result = await db_session.execute(
        select(PriceSnapshot).where(PriceSnapshot.trip_id == trip.id)
    )
    snapshots = result.scalars().all()
    assert len(snapshots) == 2
    assert snapshots[0].price == 25000
    assert snapshots[1].price == 35000


async def test_scrape_trip_background_returns_zero_on_missing_trip(db_session):
    """Returns 0 when trip doesn't exist."""
    user = await _create_user(db_session)

    service = ScheduledScrapeService(db_session)
    count = await service.scrape_trip_background(uuid.uuid4(), user.id)
    assert count == 0


async def test_scrape_trip_background_returns_zero_on_scraper_failure(db_session):
    """Returns 0 when scraper raises ScrapeError."""
    user = await _create_user(db_session)
    trip = await _create_trip(db_session, user.id)

    mock_scraper = AsyncMock()
    mock_scraper.execute.side_effect = ScrapeError("google_flights", "Timeout", 3)

    with patch(
        "app.services.scheduled_scrape_service.get_scraper",
        return_value=mock_scraper,
    ):
        service = ScheduledScrapeService(db_session)
        count = await service.scrape_trip_background(trip.id, user.id)

    assert count == 0


async def test_scrape_trip_background_returns_zero_on_unexpected_error(db_session):
    """Returns 0 when an unexpected exception occurs."""
    user = await _create_user(db_session)
    trip = await _create_trip(db_session, user.id)

    mock_scraper = AsyncMock()
    mock_scraper.execute.side_effect = RuntimeError("Something unexpected")

    with patch(
        "app.services.scheduled_scrape_service.get_scraper",
        return_value=mock_scraper,
    ):
        service = ScheduledScrapeService(db_session)
        count = await service.scrape_trip_background(trip.id, user.id)

    assert count == 0


async def test_scrape_trip_background_wrong_user(db_session):
    """Returns 0 when trip belongs to a different user."""
    user = await _create_user(db_session)
    trip = await _create_trip(db_session, user.id)

    service = ScheduledScrapeService(db_session)
    count = await service.scrape_trip_background(trip.id, uuid.uuid4())
    assert count == 0
