"""Integration tests for ScraperService."""

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
from app.services.scraper_service import ScraperService


async def _create_user(db: AsyncSession) -> User:
    """Create a test user."""
    user = User(
        email="scraper@example.com",
        hashed_password="fakehash",
        full_name="Scraper Tester",
    )
    db.add(user)
    await db.flush()
    await db.refresh(user)
    return user


async def _create_trip(db: AsyncSession, user_id: uuid.UUID) -> Trip:
    """Create a test trip."""
    trip = Trip(
        user_id=user_id,
        origin="JFK",
        destination="LAX",
        departure_date=date(2026, 6, 15),
        return_date=date(2026, 6, 22),
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


async def test_scrape_trip_stores_snapshots(db_session):
    """scrape_trip() stores price results as PriceSnapshot records."""
    user = await _create_user(db_session)
    trip = await _create_trip(db_session, user.id)

    mock_scraper = AsyncMock()
    mock_scraper.execute.return_value = _mock_price_results()

    with patch("app.services.scraper_service.get_scraper", return_value=mock_scraper):
        service = ScraperService(db_session)
        snapshots = await service.scrape_trip(trip.id, user.id)

    assert len(snapshots) == 2
    assert snapshots[0].price == 25000
    assert snapshots[0].airline == "Delta"
    assert snapshots[1].price == 35000
    assert snapshots[1].airline == "United"

    # Verify persisted in DB
    result = await db_session.execute(
        select(PriceSnapshot).where(PriceSnapshot.trip_id == trip.id)
    )
    db_snapshots = result.scalars().all()
    assert len(db_snapshots) == 2


async def test_scrape_trip_not_found(db_session):
    """scrape_trip() raises 404 for non-existent trip."""
    user = await _create_user(db_session)
    fake_trip_id = uuid.uuid4()

    service = ScraperService(db_session)
    with pytest.raises(Exception) as exc_info:
        await service.scrape_trip(fake_trip_id, user.id)
    assert "404" in str(exc_info.value.status_code)


async def test_scrape_trip_wrong_user(db_session):
    """scrape_trip() raises 404 when trip belongs to different user."""
    user = await _create_user(db_session)
    trip = await _create_trip(db_session, user.id)

    service = ScraperService(db_session)
    with pytest.raises(Exception) as exc_info:
        await service.scrape_trip(trip.id, uuid.uuid4())
    assert "404" in str(exc_info.value.status_code)


async def test_scrape_trip_unknown_provider(db_session):
    """scrape_trip() raises 422 for unknown provider."""
    user = await _create_user(db_session)
    trip = await _create_trip(db_session, user.id)

    service = ScraperService(db_session)
    with pytest.raises(Exception) as exc_info:
        await service.scrape_trip(trip.id, user.id, provider="nonexistent")
    assert "422" in str(exc_info.value.status_code)


async def test_scrape_trip_scraper_failure(db_session):
    """scrape_trip() raises 502 when scraper fails."""
    user = await _create_user(db_session)
    trip = await _create_trip(db_session, user.id)

    mock_scraper = AsyncMock()
    mock_scraper.execute.side_effect = ScrapeError("google_flights", "Timeout", 3)

    with patch("app.services.scraper_service.get_scraper", return_value=mock_scraper):
        service = ScraperService(db_session)
        with pytest.raises(Exception) as exc_info:
            await service.scrape_trip(trip.id, user.id)
        assert "502" in str(exc_info.value.status_code)


async def test_get_price_history_empty(db_session):
    """get_price_history() returns empty list when no snapshots."""
    user = await _create_user(db_session)
    trip = await _create_trip(db_session, user.id)

    service = ScraperService(db_session)
    snapshots, total = await service.get_price_history(trip.id, user.id)
    assert snapshots == []
    assert total == 0


async def test_get_price_history_with_data(db_session):
    """get_price_history() returns stored snapshots."""
    user = await _create_user(db_session)
    trip = await _create_trip(db_session, user.id)

    # Store some snapshots directly
    for price in [25000, 30000, 28000]:
        snapshot = PriceSnapshot(
            trip_id=trip.id,
            user_id=user.id,
            provider="google_flights",
            price=price,
            currency="USD",
        )
        db_session.add(snapshot)
    await db_session.flush()

    service = ScraperService(db_session)
    snapshots, total = await service.get_price_history(trip.id, user.id)
    assert total == 3
    assert len(snapshots) == 3


async def test_get_price_history_pagination(db_session):
    """get_price_history() paginates correctly."""
    user = await _create_user(db_session)
    trip = await _create_trip(db_session, user.id)

    for i in range(5):
        snapshot = PriceSnapshot(
            trip_id=trip.id,
            user_id=user.id,
            provider="google_flights",
            price=20000 + i * 1000,
            currency="USD",
        )
        db_session.add(snapshot)
    await db_session.flush()

    service = ScraperService(db_session)
    page1, total = await service.get_price_history(
        trip.id, user.id, page=1, per_page=2
    )
    assert total == 5
    assert len(page1) == 2

    page2, _ = await service.get_price_history(
        trip.id, user.id, page=2, per_page=2
    )
    assert len(page2) == 2

    page3, _ = await service.get_price_history(
        trip.id, user.id, page=3, per_page=2
    )
    assert len(page3) == 1


async def test_get_price_history_filter_by_provider(db_session):
    """get_price_history() filters by provider name."""
    user = await _create_user(db_session)
    trip = await _create_trip(db_session, user.id)

    for provider in ["google_flights", "google_flights", "other_provider"]:
        snapshot = PriceSnapshot(
            trip_id=trip.id,
            user_id=user.id,
            provider=provider,
            price=25000,
            currency="USD",
        )
        db_session.add(snapshot)
    await db_session.flush()

    service = ScraperService(db_session)
    snapshots, total = await service.get_price_history(
        trip.id, user.id, provider="google_flights"
    )
    assert total == 2
    assert all(s.provider == "google_flights" for s in snapshots)
