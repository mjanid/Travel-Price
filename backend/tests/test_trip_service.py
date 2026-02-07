"""Unit tests for TripService."""

import uuid
from datetime import date

import pytest

from app.models.trip import TripType
from app.schemas.trip import TripCreateRequest, TripUpdateRequest
from app.services.trip_service import TripService


def _make_create_request(**overrides):
    """Build a TripCreateRequest with sensible defaults."""
    defaults = {
        "origin": "JFK",
        "destination": "LAX",
        "departure_date": date(2026, 6, 15),
        "return_date": date(2026, 6, 22),
        "travelers": 2,
        "trip_type": TripType.FLIGHT,
    }
    defaults.update(overrides)
    return TripCreateRequest(**defaults)


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


async def test_create_trip(db_session):
    """Service creates a trip and returns TripResponse."""
    user_id = await _create_user(db_session)
    service = TripService(db_session)
    payload = _make_create_request()

    trip = await service.create(user_id, payload)

    assert trip.origin == "JFK"
    assert trip.destination == "LAX"
    assert trip.user_id == user_id
    assert trip.travelers == 2


async def test_get_by_id(db_session):
    """Service returns a trip by its ID."""
    user_id = await _create_user(db_session)
    service = TripService(db_session)
    created = await service.create(user_id, _make_create_request())

    fetched = await service.get_by_id(user_id, created.id)
    assert fetched.id == created.id


async def test_get_by_id_wrong_user(db_session):
    """Service raises 404 when trip belongs to another user."""
    user_id = await _create_user(db_session)
    other_user_id = await _create_user(db_session)
    service = TripService(db_session)
    created = await service.create(user_id, _make_create_request())

    from fastapi import HTTPException

    with pytest.raises(HTTPException) as exc_info:
        await service.get_by_id(other_user_id, created.id)
    assert exc_info.value.status_code == 404


async def test_list_pagination(db_session):
    """Service returns paginated trips sorted by departure date."""
    user_id = await _create_user(db_session)
    service = TripService(db_session)

    for i in range(5):
        await service.create(
            user_id,
            _make_create_request(departure_date=date(2026, 7, 10 + i), return_date=date(2026, 8, 10 + i)),
        )

    trips, total = await service.list(user_id, page=1, per_page=3)
    assert total == 5
    assert len(trips) == 3
    # Sorted ascending by departure_date
    assert trips[0].departure_date <= trips[1].departure_date


async def test_list_user_isolation(db_session):
    """Service only returns trips belonging to the requesting user."""
    user1 = await _create_user(db_session)
    user2 = await _create_user(db_session)
    service = TripService(db_session)

    await service.create(user1, _make_create_request())
    await service.create(user2, _make_create_request())

    trips1, total1 = await service.list(user1)
    trips2, total2 = await service.list(user2)
    assert total1 == 1
    assert total2 == 1


async def test_update_partial(db_session):
    """Service applies only provided fields during update."""
    user_id = await _create_user(db_session)
    service = TripService(db_session)
    created = await service.create(user_id, _make_create_request())

    updated = await service.update(
        user_id, created.id, TripUpdateRequest(travelers=5, notes="Updated")
    )
    assert updated.travelers == 5
    assert updated.notes == "Updated"
    assert updated.origin == "JFK"  # unchanged


async def test_delete(db_session):
    """Service deletes a trip."""
    user_id = await _create_user(db_session)
    service = TripService(db_session)
    created = await service.create(user_id, _make_create_request())

    await service.delete(user_id, created.id)

    from fastapi import HTTPException

    with pytest.raises(HTTPException) as exc_info:
        await service.get_by_id(user_id, created.id)
    assert exc_info.value.status_code == 404
