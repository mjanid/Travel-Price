"""Integration tests for trip API endpoints."""

import uuid

import pytest

pytestmark = pytest.mark.integration


async def _register_and_login(pg_client, email="trip@example.com"):
    """Helper to register a user and return access token."""
    await pg_client.post(
        "/api/v1/auth/register",
        json={
            "email": email,
            "password": "securepassword",
            "full_name": "Trip Tester",
        },
    )
    resp = await pg_client.post(
        "/api/v1/auth/login",
        json={"email": email, "password": "securepassword"},
    )
    return resp.json()["data"]["access_token"]


def _auth_header(token):
    return {"Authorization": f"Bearer {token}"}


VALID_TRIP = {
    "origin": "JFK",
    "destination": "LAX",
    "departure_date": "2026-06-15",
    "return_date": "2026-06-22",
    "travelers": 2,
    "trip_type": "flight",
}


async def test_create_trip_success(pg_client):
    """POST /trips returns 201 with trip data."""
    token = await _register_and_login(pg_client)
    resp = await pg_client.post(
        "/api/v1/trips/",
        json=VALID_TRIP,
        headers=_auth_header(token),
    )
    assert resp.status_code == 201
    body = resp.json()
    assert body["data"]["origin"] == "JFK"
    assert body["data"]["destination"] == "LAX"
    assert body["data"]["travelers"] == 2
    assert "id" in body["data"]


async def test_create_trip_unauthenticated(pg_client):
    """POST /trips without token returns 401."""
    resp = await pg_client.post("/api/v1/trips/", json=VALID_TRIP)
    assert resp.status_code == 401


async def test_create_trip_invalid_iata(pg_client):
    """POST /trips with invalid IATA code returns 422."""
    token = await _register_and_login(pg_client)
    bad_trip = {**VALID_TRIP, "origin": "12"}
    resp = await pg_client.post(
        "/api/v1/trips/",
        json=bad_trip,
        headers=_auth_header(token),
    )
    assert resp.status_code == 422


async def test_create_trip_return_before_departure(pg_client):
    """POST /trips with return_date <= departure_date returns 422."""
    token = await _register_and_login(pg_client)
    bad_trip = {**VALID_TRIP, "return_date": "2026-06-10"}
    resp = await pg_client.post(
        "/api/v1/trips/",
        json=bad_trip,
        headers=_auth_header(token),
    )
    assert resp.status_code == 422


async def test_create_trip_one_way(pg_client):
    """POST /trips without return_date succeeds (one-way trip)."""
    token = await _register_and_login(pg_client)
    one_way = {k: v for k, v in VALID_TRIP.items() if k != "return_date"}
    resp = await pg_client.post(
        "/api/v1/trips/",
        json=one_way,
        headers=_auth_header(token),
    )
    assert resp.status_code == 201
    assert resp.json()["data"]["return_date"] is None


async def test_create_trip_lowercase_iata_normalized(pg_client):
    """POST /trips with lowercase IATA normalizes to uppercase."""
    token = await _register_and_login(pg_client)
    trip = {**VALID_TRIP, "origin": "jfk", "destination": "lax"}
    resp = await pg_client.post(
        "/api/v1/trips/",
        json=trip,
        headers=_auth_header(token),
    )
    assert resp.status_code == 201
    assert resp.json()["data"]["origin"] == "JFK"
    assert resp.json()["data"]["destination"] == "LAX"


async def test_list_trips_empty(pg_client):
    """GET /trips returns empty paginated list."""
    token = await _register_and_login(pg_client)
    resp = await pg_client.get(
        "/api/v1/trips/",
        headers=_auth_header(token),
    )
    assert resp.status_code == 200
    body = resp.json()
    assert body["data"] == []
    assert body["meta"]["total"] == 0
    assert body["meta"]["page"] == 1


async def test_list_trips_pagination(pg_client):
    """GET /trips respects page and per_page params."""
    token = await _register_and_login(pg_client)
    # Create 3 trips
    for i in range(3):
        trip = {**VALID_TRIP, "departure_date": f"2026-07-{10 + i:02d}", "return_date": f"2026-08-{10 + i:02d}"}
        await pg_client.post(
            "/api/v1/trips/",
            json=trip,
            headers=_auth_header(token),
        )
    # Page 1 with per_page=2
    resp = await pg_client.get(
        "/api/v1/trips/?page=1&per_page=2",
        headers=_auth_header(token),
    )
    body = resp.json()
    assert len(body["data"]) == 2
    assert body["meta"]["total"] == 3
    assert body["meta"]["total_pages"] == 2

    # Page 2
    resp2 = await pg_client.get(
        "/api/v1/trips/?page=2&per_page=2",
        headers=_auth_header(token),
    )
    assert len(resp2.json()["data"]) == 1


async def test_get_trip_success(pg_client):
    """GET /trips/{id} returns the trip."""
    token = await _register_and_login(pg_client)
    create_resp = await pg_client.post(
        "/api/v1/trips/",
        json=VALID_TRIP,
        headers=_auth_header(token),
    )
    trip_id = create_resp.json()["data"]["id"]

    resp = await pg_client.get(
        f"/api/v1/trips/{trip_id}",
        headers=_auth_header(token),
    )
    assert resp.status_code == 200
    assert resp.json()["data"]["id"] == trip_id


async def test_get_trip_not_found(pg_client):
    """GET /trips/{id} with non-existent ID returns 404."""
    token = await _register_and_login(pg_client)
    fake_id = str(uuid.uuid4())
    resp = await pg_client.get(
        f"/api/v1/trips/{fake_id}",
        headers=_auth_header(token),
    )
    assert resp.status_code == 404


async def test_get_trip_other_user(pg_client):
    """GET /trips/{id} for another user's trip returns 404."""
    token1 = await _register_and_login(pg_client, email="user1@example.com")
    token2 = await _register_and_login(pg_client, email="user2@example.com")

    create_resp = await pg_client.post(
        "/api/v1/trips/",
        json=VALID_TRIP,
        headers=_auth_header(token1),
    )
    trip_id = create_resp.json()["data"]["id"]

    resp = await pg_client.get(
        f"/api/v1/trips/{trip_id}",
        headers=_auth_header(token2),
    )
    assert resp.status_code == 404


async def test_update_trip_success(pg_client):
    """PATCH /trips/{id} updates specified fields."""
    token = await _register_and_login(pg_client)
    create_resp = await pg_client.post(
        "/api/v1/trips/",
        json=VALID_TRIP,
        headers=_auth_header(token),
    )
    trip_id = create_resp.json()["data"]["id"]

    resp = await pg_client.patch(
        f"/api/v1/trips/{trip_id}",
        json={"travelers": 4, "notes": "Business trip"},
        headers=_auth_header(token),
    )
    assert resp.status_code == 200
    body = resp.json()
    assert body["data"]["travelers"] == 4
    assert body["data"]["notes"] == "Business trip"
    # Unchanged fields preserved
    assert body["data"]["origin"] == "JFK"


async def test_update_trip_not_found(pg_client):
    """PATCH /trips/{id} with non-existent ID returns 404."""
    token = await _register_and_login(pg_client)
    fake_id = str(uuid.uuid4())
    resp = await pg_client.patch(
        f"/api/v1/trips/{fake_id}",
        json={"travelers": 3},
        headers=_auth_header(token),
    )
    assert resp.status_code == 404


async def test_delete_trip_success(pg_client):
    """DELETE /trips/{id} returns 204 and removes trip."""
    token = await _register_and_login(pg_client)
    create_resp = await pg_client.post(
        "/api/v1/trips/",
        json=VALID_TRIP,
        headers=_auth_header(token),
    )
    trip_id = create_resp.json()["data"]["id"]

    resp = await pg_client.delete(
        f"/api/v1/trips/{trip_id}",
        headers=_auth_header(token),
    )
    assert resp.status_code == 204

    # Confirm deleted
    get_resp = await pg_client.get(
        f"/api/v1/trips/{trip_id}",
        headers=_auth_header(token),
    )
    assert get_resp.status_code == 404


async def test_delete_trip_not_found(pg_client):
    """DELETE /trips/{id} with non-existent ID returns 404."""
    token = await _register_and_login(pg_client)
    fake_id = str(uuid.uuid4())
    resp = await pg_client.delete(
        f"/api/v1/trips/{fake_id}",
        headers=_auth_header(token),
    )
    assert resp.status_code == 404
