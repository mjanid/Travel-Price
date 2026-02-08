"""Integration tests for price watch API routes."""

import uuid
from datetime import date

from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import create_access_token
from app.models.trip import Trip
from app.models.user import User
from tests.factories import build_user


async def _setup_auth(db: AsyncSession) -> tuple[User, str]:
    """Create user and return (user, auth_header_value)."""
    user = build_user(email="watchroute@example.com")
    db.add(user)
    await db.flush()
    await db.refresh(user)
    token = create_access_token(str(user.id))
    return user, f"Bearer {token}"


async def _create_trip(db: AsyncSession, user_id: uuid.UUID) -> Trip:
    """Create a test trip."""
    trip = Trip(
        user_id=user_id,
        origin="JFK",
        destination="LAX",
        departure_date=date(2027, 6, 15),
        travelers=1,
        trip_type="flight",
    )
    db.add(trip)
    await db.flush()
    await db.refresh(trip)
    return trip


async def test_create_watch_success(client: AsyncClient, db_session: AsyncSession):
    """POST /watches/ creates a price watch."""
    user, auth = await _setup_auth(db_session)
    trip = await _create_trip(db_session, user.id)

    resp = await client.post(
        "/api/v1/watches/",
        json={"trip_id": str(trip.id), "target_price": 25000},
        headers={"Authorization": auth},
    )
    assert resp.status_code == 201
    data = resp.json()["data"]
    assert data["target_price"] == 25000
    assert data["trip_id"] == str(trip.id)
    assert data["is_active"] is True


async def test_create_watch_unauthenticated(client: AsyncClient):
    """POST /watches/ requires authentication."""
    resp = await client.post(
        "/api/v1/watches/",
        json={"trip_id": str(uuid.uuid4()), "target_price": 25000},
    )
    assert resp.status_code == 401


async def test_list_watches(client: AsyncClient, db_session: AsyncSession):
    """GET /watches/ returns paginated list."""
    user, auth = await _setup_auth(db_session)
    trip = await _create_trip(db_session, user.id)

    # Create 3 watches
    for price in [20000, 25000, 30000]:
        await client.post(
            "/api/v1/watches/",
            json={"trip_id": str(trip.id), "target_price": price},
            headers={"Authorization": auth},
        )

    resp = await client.get(
        "/api/v1/watches/", headers={"Authorization": auth}
    )
    assert resp.status_code == 200
    assert resp.json()["meta"]["total"] == 3


async def test_get_watch(client: AsyncClient, db_session: AsyncSession):
    """GET /watches/{id} returns a single watch."""
    user, auth = await _setup_auth(db_session)
    trip = await _create_trip(db_session, user.id)

    create_resp = await client.post(
        "/api/v1/watches/",
        json={"trip_id": str(trip.id), "target_price": 25000},
        headers={"Authorization": auth},
    )
    watch_id = create_resp.json()["data"]["id"]

    resp = await client.get(
        f"/api/v1/watches/{watch_id}", headers={"Authorization": auth}
    )
    assert resp.status_code == 200
    assert resp.json()["data"]["id"] == watch_id


async def test_get_watch_not_found(client: AsyncClient, db_session: AsyncSession):
    """GET /watches/{id} returns 404 for nonexistent watch."""
    user, auth = await _setup_auth(db_session)
    resp = await client.get(
        f"/api/v1/watches/{uuid.uuid4()}", headers={"Authorization": auth}
    )
    assert resp.status_code == 404


async def test_update_watch(client: AsyncClient, db_session: AsyncSession):
    """PATCH /watches/{id} updates the watch."""
    user, auth = await _setup_auth(db_session)
    trip = await _create_trip(db_session, user.id)

    create_resp = await client.post(
        "/api/v1/watches/",
        json={"trip_id": str(trip.id), "target_price": 25000},
        headers={"Authorization": auth},
    )
    watch_id = create_resp.json()["data"]["id"]

    resp = await client.patch(
        f"/api/v1/watches/{watch_id}",
        json={"target_price": 20000, "is_active": False},
        headers={"Authorization": auth},
    )
    assert resp.status_code == 200
    data = resp.json()["data"]
    assert data["target_price"] == 20000
    assert data["is_active"] is False


async def test_delete_watch(client: AsyncClient, db_session: AsyncSession):
    """DELETE /watches/{id} removes the watch."""
    user, auth = await _setup_auth(db_session)
    trip = await _create_trip(db_session, user.id)

    create_resp = await client.post(
        "/api/v1/watches/",
        json={"trip_id": str(trip.id), "target_price": 25000},
        headers={"Authorization": auth},
    )
    watch_id = create_resp.json()["data"]["id"]

    resp = await client.delete(
        f"/api/v1/watches/{watch_id}", headers={"Authorization": auth}
    )
    assert resp.status_code == 204

    # Verify deleted
    get_resp = await client.get(
        f"/api/v1/watches/{watch_id}", headers={"Authorization": auth}
    )
    assert get_resp.status_code == 404


async def test_list_trip_watches(client: AsyncClient, db_session: AsyncSession):
    """GET /trips/{id}/watches lists watches for a specific trip."""
    user, auth = await _setup_auth(db_session)
    trip1 = await _create_trip(db_session, user.id)
    trip2 = await _create_trip(db_session, user.id)

    await client.post(
        "/api/v1/watches/",
        json={"trip_id": str(trip1.id), "target_price": 25000},
        headers={"Authorization": auth},
    )
    await client.post(
        "/api/v1/watches/",
        json={"trip_id": str(trip2.id), "target_price": 30000},
        headers={"Authorization": auth},
    )

    resp = await client.get(
        f"/api/v1/trips/{trip1.id}/watches", headers={"Authorization": auth}
    )
    assert resp.status_code == 200
    assert resp.json()["meta"]["total"] == 1
