"""Tests for dynamic per-watch scrape intervals.

Covers interval field on create/update, next_scrape_at calculation,
due-watch dispatching, and interval validation boundaries.
"""

import uuid
from datetime import date, datetime, timedelta, timezone

import pytest
from pydantic import ValidationError
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.price_watch import PriceWatch
from app.models.trip import Trip
from app.models.user import User
from app.schemas.price_watch import (
    PriceWatchCreateRequest,
    PriceWatchUpdateRequest,
)
from app.services.price_watch_service import PriceWatchService
from app.services.scheduled_scrape_service import ScheduledScrapeService


async def _create_user(db: AsyncSession, email: str = "interval@example.com") -> User:
    """Create a test user."""
    user = User(
        email=email,
        hashed_password="fakehash",
        full_name="Interval Tester",
    )
    db.add(user)
    await db.flush()
    await db.refresh(user)
    return user


async def _create_trip(
    db: AsyncSession,
    user_id: uuid.UUID,
    departure_date: date | None = None,
) -> Trip:
    """Create a test trip."""
    trip = Trip(
        user_id=user_id,
        origin="JFK",
        destination="LAX",
        departure_date=departure_date or date(2027, 6, 15),
        return_date=date(2027, 6, 22),
        travelers=2,
        trip_type="flight",
    )
    db.add(trip)
    await db.flush()
    await db.refresh(trip)
    return trip


async def _create_watch(
    db: AsyncSession,
    user_id: uuid.UUID,
    trip_id: uuid.UUID,
    scrape_interval_minutes: int = 60,
    next_scrape_at: datetime | None = None,
    is_active: bool = True,
) -> PriceWatch:
    """Create a PriceWatch directly in the database."""
    watch = PriceWatch(
        user_id=user_id,
        trip_id=trip_id,
        provider="google_flights",
        target_price=25000,
        currency="USD",
        is_active=is_active,
        scrape_interval_minutes=scrape_interval_minutes,
        next_scrape_at=next_scrape_at,
    )
    db.add(watch)
    await db.flush()
    await db.refresh(watch)
    return watch


# ── PriceWatchService: create ─────────────────────────────────


def _ensure_aware(dt: datetime) -> datetime:
    """Ensure a datetime is timezone-aware (SQLite returns naive datetimes)."""
    if dt.tzinfo is None:
        return dt.replace(tzinfo=timezone.utc)
    return dt


async def test_create_watch_sets_default_interval_and_next_scrape_at(db_session):
    """create() with default interval sets scrape_interval_minutes=60 and next_scrape_at to ~now."""
    user = await _create_user(db_session)
    trip = await _create_trip(db_session, user.id)

    service = PriceWatchService(db_session)
    payload = PriceWatchCreateRequest(trip_id=trip.id, target_price=25000)
    watch = await service.create(user.id, payload)

    assert watch.scrape_interval_minutes == 60
    assert watch.next_scrape_at is not None
    # next_scrape_at should be approximately now (within 5 seconds)
    next_scrape = _ensure_aware(watch.next_scrape_at)
    delta = abs((next_scrape - datetime.now(timezone.utc)).total_seconds())
    assert delta < 5


async def test_create_watch_accepts_custom_interval(db_session):
    """create() stores the custom scrape_interval_minutes value."""
    user = await _create_user(db_session)
    trip = await _create_trip(db_session, user.id)

    service = PriceWatchService(db_session)
    payload = PriceWatchCreateRequest(
        trip_id=trip.id, target_price=25000, scrape_interval_minutes=120
    )
    watch = await service.create(user.id, payload)

    assert watch.scrape_interval_minutes == 120


# ── PriceWatchService: update ─────────────────────────────────


async def test_update_watch_recalculates_next_scrape_at(db_session):
    """update() recalculates next_scrape_at when interval changes."""
    user = await _create_user(db_session)
    trip = await _create_trip(db_session, user.id)

    service = PriceWatchService(db_session)
    payload = PriceWatchCreateRequest(
        trip_id=trip.id, target_price=25000, scrape_interval_minutes=60
    )
    created = await service.create(user.id, payload)

    before = datetime.now(timezone.utc)
    updated = await service.update(
        user.id,
        created.id,
        PriceWatchUpdateRequest(scrape_interval_minutes=240),
    )

    assert updated.scrape_interval_minutes == 240
    assert updated.next_scrape_at is not None
    # next_scrape_at should be ~now + 240 minutes
    expected = before + timedelta(minutes=240)
    next_scrape = _ensure_aware(updated.next_scrape_at)
    delta = abs((next_scrape - expected).total_seconds())
    assert delta < 5


async def test_update_watch_without_interval_preserves_next_scrape_at(db_session):
    """update() without scrape_interval_minutes does not change next_scrape_at."""
    user = await _create_user(db_session)
    trip = await _create_trip(db_session, user.id)

    service = PriceWatchService(db_session)
    payload = PriceWatchCreateRequest(
        trip_id=trip.id, target_price=25000, scrape_interval_minutes=60
    )
    created = await service.create(user.id, payload)
    original_next = created.next_scrape_at

    updated = await service.update(
        user.id,
        created.id,
        PriceWatchUpdateRequest(target_price=20000),
    )

    assert updated.scrape_interval_minutes == 60
    assert updated.next_scrape_at == original_next


# ── Schema validation ─────────────────────────────────────────


def test_interval_validation_rejects_below_15():
    """PriceWatchCreateRequest rejects scrape_interval_minutes < 15."""
    with pytest.raises(ValidationError) as exc_info:
        PriceWatchCreateRequest(
            trip_id=uuid.uuid4(), target_price=25000, scrape_interval_minutes=10
        )
    errors = exc_info.value.errors()
    assert any("scrape_interval_minutes" in str(e["loc"]) for e in errors)


def test_interval_validation_rejects_above_1440():
    """PriceWatchCreateRequest rejects scrape_interval_minutes > 1440."""
    with pytest.raises(ValidationError) as exc_info:
        PriceWatchCreateRequest(
            trip_id=uuid.uuid4(), target_price=25000, scrape_interval_minutes=2000
        )
    errors = exc_info.value.errors()
    assert any("scrape_interval_minutes" in str(e["loc"]) for e in errors)


def test_update_interval_validation_rejects_below_15():
    """PriceWatchUpdateRequest rejects scrape_interval_minutes < 15."""
    with pytest.raises(ValidationError) as exc_info:
        PriceWatchUpdateRequest(scrape_interval_minutes=5)
    errors = exc_info.value.errors()
    assert any("scrape_interval_minutes" in str(e["loc"]) for e in errors)


def test_update_interval_validation_rejects_above_1440():
    """PriceWatchUpdateRequest rejects scrape_interval_minutes > 1440."""
    with pytest.raises(ValidationError) as exc_info:
        PriceWatchUpdateRequest(scrape_interval_minutes=1500)
    errors = exc_info.value.errors()
    assert any("scrape_interval_minutes" in str(e["loc"]) for e in errors)


def test_interval_validation_accepts_boundary_values():
    """Schema accepts scrape_interval_minutes at boundaries: 15 and 1440."""
    low = PriceWatchCreateRequest(
        trip_id=uuid.uuid4(), target_price=25000, scrape_interval_minutes=15
    )
    assert low.scrape_interval_minutes == 15

    high = PriceWatchCreateRequest(
        trip_id=uuid.uuid4(), target_price=25000, scrape_interval_minutes=1440
    )
    assert high.scrape_interval_minutes == 1440


# ── ScheduledScrapeService: get_due_watches ───────────────────


async def test_dispatch_due_scrapes_only_picks_due_watches(db_session):
    """get_due_watches() returns only watches with next_scrape_at <= now or NULL."""
    user = await _create_user(db_session)
    trip = await _create_trip(db_session, user.id)
    now = datetime.now(timezone.utc)

    # Due watch (past next_scrape_at)
    due_watch = await _create_watch(
        db_session, user.id, trip.id,
        next_scrape_at=now - timedelta(minutes=5),
    )
    # NULL next_scrape_at (never scraped, should also be due)
    null_watch = await _create_watch(
        db_session, user.id, trip.id,
        next_scrape_at=None,
    )
    # Not yet due (future next_scrape_at)
    await _create_watch(
        db_session, user.id, trip.id,
        next_scrape_at=now + timedelta(hours=1),
    )

    service = ScheduledScrapeService(db_session)
    due = await service.get_due_watches()

    due_ids = {w.id for w in due}
    assert due_watch.id in due_ids
    assert null_watch.id in due_ids
    assert len(due) == 2


async def test_dispatch_due_scrapes_skips_watches_not_yet_due(db_session):
    """get_due_watches() returns empty when all watches have future next_scrape_at."""
    user = await _create_user(db_session)
    trip = await _create_trip(db_session, user.id)
    now = datetime.now(timezone.utc)

    await _create_watch(
        db_session, user.id, trip.id,
        next_scrape_at=now + timedelta(hours=1),
    )
    await _create_watch(
        db_session, user.id, trip.id,
        next_scrape_at=now + timedelta(hours=2),
    )

    service = ScheduledScrapeService(db_session)
    due = await service.get_due_watches()
    assert len(due) == 0


async def test_dispatch_due_scrapes_skips_inactive_watches(db_session):
    """get_due_watches() ignores inactive watches even if they are due."""
    user = await _create_user(db_session)
    trip = await _create_trip(db_session, user.id)
    now = datetime.now(timezone.utc)

    await _create_watch(
        db_session, user.id, trip.id,
        next_scrape_at=now - timedelta(minutes=5),
        is_active=False,
    )

    service = ScheduledScrapeService(db_session)
    due = await service.get_due_watches()
    assert len(due) == 0


# ── ScheduledScrapeService: mark_dispatched ───────────────────


async def test_dispatch_updates_next_scrape_at_after_dispatch(db_session):
    """mark_dispatched() sets next_scrape_at to now + interval."""
    user = await _create_user(db_session)
    trip = await _create_trip(db_session, user.id)

    watch = await _create_watch(
        db_session, user.id, trip.id,
        scrape_interval_minutes=30,
        next_scrape_at=None,
    )

    service = ScheduledScrapeService(db_session)
    before = datetime.now(timezone.utc)
    await service.mark_dispatched(watch)

    expected = before + timedelta(minutes=30)
    assert watch.next_scrape_at is not None
    next_scrape = _ensure_aware(watch.next_scrape_at)
    delta = abs((next_scrape - expected).total_seconds())
    assert delta < 5
