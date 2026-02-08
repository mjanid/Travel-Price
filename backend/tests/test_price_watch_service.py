"""Unit tests for PriceWatchService."""

import uuid
from datetime import date

import pytest

from app.models.trip import TripType
from app.schemas.price_watch import PriceWatchCreateRequest, PriceWatchUpdateRequest
from app.schemas.trip import TripCreateRequest
from app.services.price_watch_service import PriceWatchService
from app.services.trip_service import TripService


async def _create_user(db_session) -> uuid.UUID:
    """Insert a minimal user and return its ID."""
    from app.core.security import hash_password
    from app.models.user import User

    user = User(
        email=f"{uuid.uuid4().hex[:8]}@test.com",
        hashed_password=hash_password("testpassword"),
        full_name="Test User",
    )
    db_session.add(user)
    await db_session.flush()
    await db_session.refresh(user)
    return user.id


async def _create_trip(db_session, user_id: uuid.UUID) -> uuid.UUID:
    """Create a trip and return its ID."""
    service = TripService(db_session)
    trip = await service.create(
        user_id,
        TripCreateRequest(
            origin="JFK",
            destination="LAX",
            departure_date=date(2026, 6, 15),
            return_date=date(2026, 6, 22),
            travelers=2,
            trip_type=TripType.FLIGHT,
        ),
    )
    return trip.id


def _make_watch_request(**overrides):
    """Build a PriceWatchCreateRequest with sensible defaults."""
    defaults = {
        "provider": "google_flights",
        "target_price": 35000,
        "currency": "USD",
    }
    defaults.update(overrides)
    return PriceWatchCreateRequest(**defaults)


async def test_create_watch(db_session):
    """Service creates a price watch and returns PriceWatchResponse."""
    user_id = await _create_user(db_session)
    trip_id = await _create_trip(db_session, user_id)
    service = PriceWatchService(db_session)

    watch = await service.create(user_id, trip_id, _make_watch_request())

    assert watch.provider == "google_flights"
    assert watch.target_price == 35000
    assert watch.currency == "USD"
    assert watch.trip_id == trip_id
    assert watch.is_active is True
    assert watch.alert_cooldown_hours == 6


async def test_create_watch_trip_not_owned(db_session):
    """Service raises 404 when creating a watch on another user's trip."""
    user1 = await _create_user(db_session)
    user2 = await _create_user(db_session)
    trip_id = await _create_trip(db_session, user1)
    service = PriceWatchService(db_session)

    from fastapi import HTTPException

    with pytest.raises(HTTPException) as exc_info:
        await service.create(user2, trip_id, _make_watch_request())
    assert exc_info.value.status_code == 404


async def test_get_by_id(db_session):
    """Service returns a price watch by its ID."""
    user_id = await _create_user(db_session)
    trip_id = await _create_trip(db_session, user_id)
    service = PriceWatchService(db_session)
    created = await service.create(user_id, trip_id, _make_watch_request())

    fetched = await service.get_by_id(user_id, created.id)
    assert fetched.id == created.id
    assert fetched.provider == "google_flights"


async def test_get_by_id_wrong_user(db_session):
    """Service raises 404 when watch belongs to another user's trip."""
    user1 = await _create_user(db_session)
    user2 = await _create_user(db_session)
    trip_id = await _create_trip(db_session, user1)
    service = PriceWatchService(db_session)
    created = await service.create(user1, trip_id, _make_watch_request())

    from fastapi import HTTPException

    with pytest.raises(HTTPException) as exc_info:
        await service.get_by_id(user2, created.id)
    assert exc_info.value.status_code == 404


async def test_list_by_trip_pagination(db_session):
    """Service returns paginated watches for a trip."""
    user_id = await _create_user(db_session)
    trip_id = await _create_trip(db_session, user_id)
    service = PriceWatchService(db_session)

    for i in range(5):
        await service.create(
            user_id, trip_id, _make_watch_request(provider=f"provider_{i}")
        )

    watches, total = await service.list_by_trip(user_id, trip_id, page=1, per_page=3)
    assert total == 5
    assert len(watches) == 3


async def test_list_by_trip_isolation(db_session):
    """Service only returns watches for the specified trip."""
    user_id = await _create_user(db_session)
    trip1 = await _create_trip(db_session, user_id)
    trip2 = await _create_trip(db_session, user_id)
    service = PriceWatchService(db_session)

    await service.create(user_id, trip1, _make_watch_request())
    await service.create(user_id, trip2, _make_watch_request())

    watches1, total1 = await service.list_by_trip(user_id, trip1)
    watches2, total2 = await service.list_by_trip(user_id, trip2)
    assert total1 == 1
    assert total2 == 1


async def test_update_partial(db_session):
    """Service applies only provided fields during update."""
    user_id = await _create_user(db_session)
    trip_id = await _create_trip(db_session, user_id)
    service = PriceWatchService(db_session)
    created = await service.create(user_id, trip_id, _make_watch_request())

    updated = await service.update(
        user_id, created.id,
        PriceWatchUpdateRequest(target_price=25000, is_active=False),
    )
    assert updated.target_price == 25000
    assert updated.is_active is False
    assert updated.provider == "google_flights"  # unchanged


async def test_delete(db_session):
    """Service deletes a price watch."""
    user_id = await _create_user(db_session)
    trip_id = await _create_trip(db_session, user_id)
    service = PriceWatchService(db_session)
    created = await service.create(user_id, trip_id, _make_watch_request())

    await service.delete(user_id, created.id)

    from fastapi import HTTPException

    with pytest.raises(HTTPException) as exc_info:
        await service.get_by_id(user_id, created.id)
    assert exc_info.value.status_code == 404
