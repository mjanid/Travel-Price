"""Tests for PriceWatchService."""

import uuid
from datetime import date

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.price_watch import PriceWatch
from app.models.trip import Trip
from app.models.user import User
from app.schemas.price_watch import PriceWatchCreateRequest, PriceWatchUpdateRequest
from app.services.price_watch_service import PriceWatchService


async def _create_user(db: AsyncSession, email: str = "watch@example.com") -> User:
    """Create a test user."""
    user = User(
        email=email,
        hashed_password="fakehash",
        full_name="Watch Tester",
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
        departure_date=date(2027, 6, 15),
        return_date=date(2027, 6, 22),
        travelers=2,
        trip_type="flight",
    )
    db.add(trip)
    await db.flush()
    await db.refresh(trip)
    return trip


# --- create tests ---


async def test_create_price_watch(db_session):
    """create() stores a new PriceWatch and returns response."""
    user = await _create_user(db_session)
    trip = await _create_trip(db_session, user.id)

    service = PriceWatchService(db_session)
    payload = PriceWatchCreateRequest(
        trip_id=trip.id, target_price=25000, provider="google_flights"
    )
    watch = await service.create(user.id, payload)

    assert watch.trip_id == trip.id
    assert watch.user_id == user.id
    assert watch.target_price == 25000
    assert watch.provider == "google_flights"
    assert watch.is_active is True
    assert watch.alert_cooldown_hours == 6


async def test_create_price_watch_nonexistent_trip(db_session):
    """create() raises 404 when trip does not exist."""
    user = await _create_user(db_session)

    service = PriceWatchService(db_session)
    payload = PriceWatchCreateRequest(
        trip_id=uuid.uuid4(), target_price=25000
    )
    with pytest.raises(Exception) as exc_info:
        await service.create(user.id, payload)
    assert "404" in str(exc_info.value.status_code)


async def test_create_price_watch_wrong_user_trip(db_session):
    """create() raises 404 when trip belongs to another user."""
    user1 = await _create_user(db_session, email="user1@example.com")
    user2 = await _create_user(db_session, email="user2@example.com")
    trip = await _create_trip(db_session, user1.id)

    service = PriceWatchService(db_session)
    payload = PriceWatchCreateRequest(
        trip_id=trip.id, target_price=25000
    )
    with pytest.raises(Exception) as exc_info:
        await service.create(user2.id, payload)
    assert "404" in str(exc_info.value.status_code)


# --- get_by_id tests ---


async def test_get_by_id(db_session):
    """get_by_id() returns watch data."""
    user = await _create_user(db_session)
    trip = await _create_trip(db_session, user.id)

    service = PriceWatchService(db_session)
    payload = PriceWatchCreateRequest(trip_id=trip.id, target_price=25000)
    created = await service.create(user.id, payload)

    watch = await service.get_by_id(user.id, created.id)
    assert watch.id == created.id
    assert watch.target_price == 25000


async def test_get_by_id_wrong_user(db_session):
    """get_by_id() raises 404 when watch belongs to another user."""
    user = await _create_user(db_session)
    trip = await _create_trip(db_session, user.id)

    service = PriceWatchService(db_session)
    payload = PriceWatchCreateRequest(trip_id=trip.id, target_price=25000)
    created = await service.create(user.id, payload)

    with pytest.raises(Exception) as exc_info:
        await service.get_by_id(uuid.uuid4(), created.id)
    assert "404" in str(exc_info.value.status_code)


# --- list tests ---


async def test_list_for_user_pagination(db_session):
    """list_for_user() paginates correctly."""
    user = await _create_user(db_session)
    trip = await _create_trip(db_session, user.id)

    service = PriceWatchService(db_session)
    for i in range(5):
        payload = PriceWatchCreateRequest(
            trip_id=trip.id, target_price=20000 + i * 1000
        )
        await service.create(user.id, payload)

    page1, total = await service.list_for_user(user.id, page=1, per_page=2)
    assert total == 5
    assert len(page1) == 2

    page3, _ = await service.list_for_user(user.id, page=3, per_page=2)
    assert len(page3) == 1


async def test_list_for_user_isolation(db_session):
    """list_for_user() only returns watches for the given user."""
    user1 = await _create_user(db_session, email="u1@example.com")
    user2 = await _create_user(db_session, email="u2@example.com")
    trip1 = await _create_trip(db_session, user1.id)
    trip2 = await _create_trip(db_session, user2.id)

    service = PriceWatchService(db_session)
    await service.create(
        user1.id, PriceWatchCreateRequest(trip_id=trip1.id, target_price=20000)
    )
    await service.create(
        user2.id, PriceWatchCreateRequest(trip_id=trip2.id, target_price=30000)
    )

    watches, total = await service.list_for_user(user1.id)
    assert total == 1
    assert watches[0].user_id == user1.id


async def test_list_for_trip(db_session):
    """list_for_trip() filters watches by trip."""
    user = await _create_user(db_session)
    trip1 = await _create_trip(db_session, user.id)
    trip2 = await _create_trip(db_session, user.id)

    service = PriceWatchService(db_session)
    await service.create(
        user.id, PriceWatchCreateRequest(trip_id=trip1.id, target_price=20000)
    )
    await service.create(
        user.id, PriceWatchCreateRequest(trip_id=trip1.id, target_price=25000)
    )
    await service.create(
        user.id, PriceWatchCreateRequest(trip_id=trip2.id, target_price=30000)
    )

    watches, total = await service.list_for_trip(user.id, trip1.id)
    assert total == 2
    assert all(w.trip_id == trip1.id for w in watches)


# --- update tests ---


async def test_update_partial(db_session):
    """update() only changes provided fields."""
    user = await _create_user(db_session)
    trip = await _create_trip(db_session, user.id)

    service = PriceWatchService(db_session)
    payload = PriceWatchCreateRequest(trip_id=trip.id, target_price=25000)
    created = await service.create(user.id, payload)

    updated = await service.update(
        user.id, created.id, PriceWatchUpdateRequest(target_price=20000)
    )
    assert updated.target_price == 20000
    assert updated.is_active is True  # unchanged


async def test_update_deactivate(db_session):
    """update() can deactivate a watch."""
    user = await _create_user(db_session)
    trip = await _create_trip(db_session, user.id)

    service = PriceWatchService(db_session)
    payload = PriceWatchCreateRequest(trip_id=trip.id, target_price=25000)
    created = await service.create(user.id, payload)

    updated = await service.update(
        user.id, created.id, PriceWatchUpdateRequest(is_active=False)
    )
    assert updated.is_active is False


# --- delete tests ---


async def test_delete(db_session):
    """delete() removes the watch."""
    user = await _create_user(db_session)
    trip = await _create_trip(db_session, user.id)

    service = PriceWatchService(db_session)
    payload = PriceWatchCreateRequest(trip_id=trip.id, target_price=25000)
    created = await service.create(user.id, payload)

    await service.delete(user.id, created.id)

    with pytest.raises(Exception) as exc_info:
        await service.get_by_id(user.id, created.id)
    assert "404" in str(exc_info.value.status_code)


async def test_delete_wrong_user(db_session):
    """delete() raises 404 when watch belongs to another user."""
    user = await _create_user(db_session)
    trip = await _create_trip(db_session, user.id)

    service = PriceWatchService(db_session)
    payload = PriceWatchCreateRequest(trip_id=trip.id, target_price=25000)
    created = await service.create(user.id, payload)

    with pytest.raises(Exception) as exc_info:
        await service.delete(uuid.uuid4(), created.id)
    assert "404" in str(exc_info.value.status_code)
