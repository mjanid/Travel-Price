"""Integration tests for price watch API endpoints."""

import uuid


async def _register_and_login(client, email="watch@example.com"):
    """Helper to register a user and return access token."""
    await client.post(
        "/api/v1/auth/register",
        json={
            "email": email,
            "password": "securepassword",
            "full_name": "Watch Tester",
        },
    )
    resp = await client.post(
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

VALID_WATCH = {
    "provider": "google_flights",
    "target_price": 35000,
    "currency": "USD",
}


async def _create_trip(client, token):
    """Helper to create a trip and return its ID."""
    resp = await client.post(
        "/api/v1/trips/",
        json=VALID_TRIP,
        headers=_auth_header(token),
    )
    return resp.json()["data"]["id"]


async def test_create_watch_success(client):
    """POST /trips/{trip_id}/watches returns 201 with watch data."""
    token = await _register_and_login(client)
    trip_id = await _create_trip(client, token)

    resp = await client.post(
        f"/api/v1/trips/{trip_id}/watches",
        json=VALID_WATCH,
        headers=_auth_header(token),
    )
    assert resp.status_code == 201
    body = resp.json()
    assert body["data"]["provider"] == "google_flights"
    assert body["data"]["target_price"] == 35000
    assert body["data"]["currency"] == "USD"
    assert body["data"]["is_active"] is True
    assert body["data"]["alert_cooldown_hours"] == 6
    assert body["data"]["trip_id"] == trip_id
    assert "id" in body["data"]


async def test_create_watch_unauthenticated(client):
    """POST /trips/{trip_id}/watches without token returns 401."""
    fake_id = str(uuid.uuid4())
    resp = await client.post(
        f"/api/v1/trips/{fake_id}/watches",
        json=VALID_WATCH,
    )
    assert resp.status_code == 401


async def test_create_watch_trip_not_found(client):
    """POST /trips/{trip_id}/watches with non-existent trip returns 404."""
    token = await _register_and_login(client)
    fake_id = str(uuid.uuid4())
    resp = await client.post(
        f"/api/v1/trips/{fake_id}/watches",
        json=VALID_WATCH,
        headers=_auth_header(token),
    )
    assert resp.status_code == 404


async def test_create_watch_other_users_trip(client):
    """POST /trips/{trip_id}/watches on another user's trip returns 404."""
    token1 = await _register_and_login(client, email="owner@example.com")
    token2 = await _register_and_login(client, email="other@example.com")
    trip_id = await _create_trip(client, token1)

    resp = await client.post(
        f"/api/v1/trips/{trip_id}/watches",
        json=VALID_WATCH,
        headers=_auth_header(token2),
    )
    assert resp.status_code == 404


async def test_create_watch_invalid_target_price(client):
    """POST /trips/{trip_id}/watches with zero target_price returns 422."""
    token = await _register_and_login(client)
    trip_id = await _create_trip(client, token)

    resp = await client.post(
        f"/api/v1/trips/{trip_id}/watches",
        json={**VALID_WATCH, "target_price": 0},
        headers=_auth_header(token),
    )
    assert resp.status_code == 422


async def test_list_watches_empty(client):
    """GET /trips/{trip_id}/watches returns empty paginated list."""
    token = await _register_and_login(client)
    trip_id = await _create_trip(client, token)

    resp = await client.get(
        f"/api/v1/trips/{trip_id}/watches",
        headers=_auth_header(token),
    )
    assert resp.status_code == 200
    body = resp.json()
    assert body["data"] == []
    assert body["meta"]["total"] == 0


async def test_list_watches_pagination(client):
    """GET /trips/{trip_id}/watches respects pagination params."""
    token = await _register_and_login(client)
    trip_id = await _create_trip(client, token)

    for i in range(3):
        await client.post(
            f"/api/v1/trips/{trip_id}/watches",
            json={**VALID_WATCH, "provider": f"provider_{i}"},
            headers=_auth_header(token),
        )

    resp = await client.get(
        f"/api/v1/trips/{trip_id}/watches?page=1&per_page=2",
        headers=_auth_header(token),
    )
    body = resp.json()
    assert len(body["data"]) == 2
    assert body["meta"]["total"] == 3
    assert body["meta"]["total_pages"] == 2

    resp2 = await client.get(
        f"/api/v1/trips/{trip_id}/watches?page=2&per_page=2",
        headers=_auth_header(token),
    )
    assert len(resp2.json()["data"]) == 1


async def test_list_watches_other_users_trip(client):
    """GET /trips/{trip_id}/watches on another user's trip returns 404."""
    token1 = await _register_and_login(client, email="owner2@example.com")
    token2 = await _register_and_login(client, email="other2@example.com")
    trip_id = await _create_trip(client, token1)

    resp = await client.get(
        f"/api/v1/trips/{trip_id}/watches",
        headers=_auth_header(token2),
    )
    assert resp.status_code == 404


async def test_get_watch_success(client):
    """GET /watches/{watch_id} returns the watch."""
    token = await _register_and_login(client)
    trip_id = await _create_trip(client, token)

    create_resp = await client.post(
        f"/api/v1/trips/{trip_id}/watches",
        json=VALID_WATCH,
        headers=_auth_header(token),
    )
    watch_id = create_resp.json()["data"]["id"]

    resp = await client.get(
        f"/api/v1/watches/{watch_id}",
        headers=_auth_header(token),
    )
    assert resp.status_code == 200
    assert resp.json()["data"]["id"] == watch_id
    assert resp.json()["data"]["provider"] == "google_flights"


async def test_get_watch_not_found(client):
    """GET /watches/{watch_id} with non-existent ID returns 404."""
    token = await _register_and_login(client)
    fake_id = str(uuid.uuid4())
    resp = await client.get(
        f"/api/v1/watches/{fake_id}",
        headers=_auth_header(token),
    )
    assert resp.status_code == 404


async def test_get_watch_other_user(client):
    """GET /watches/{watch_id} for another user's watch returns 404."""
    token1 = await _register_and_login(client, email="owner3@example.com")
    token2 = await _register_and_login(client, email="other3@example.com")
    trip_id = await _create_trip(client, token1)

    create_resp = await client.post(
        f"/api/v1/trips/{trip_id}/watches",
        json=VALID_WATCH,
        headers=_auth_header(token1),
    )
    watch_id = create_resp.json()["data"]["id"]

    resp = await client.get(
        f"/api/v1/watches/{watch_id}",
        headers=_auth_header(token2),
    )
    assert resp.status_code == 404


async def test_update_watch_success(client):
    """PATCH /watches/{watch_id} updates specified fields."""
    token = await _register_and_login(client)
    trip_id = await _create_trip(client, token)

    create_resp = await client.post(
        f"/api/v1/trips/{trip_id}/watches",
        json=VALID_WATCH,
        headers=_auth_header(token),
    )
    watch_id = create_resp.json()["data"]["id"]

    resp = await client.patch(
        f"/api/v1/watches/{watch_id}",
        json={"target_price": 28000, "is_active": False},
        headers=_auth_header(token),
    )
    assert resp.status_code == 200
    body = resp.json()
    assert body["data"]["target_price"] == 28000
    assert body["data"]["is_active"] is False
    assert body["data"]["provider"] == "google_flights"  # unchanged


async def test_update_watch_not_found(client):
    """PATCH /watches/{watch_id} with non-existent ID returns 404."""
    token = await _register_and_login(client)
    fake_id = str(uuid.uuid4())
    resp = await client.patch(
        f"/api/v1/watches/{fake_id}",
        json={"target_price": 20000},
        headers=_auth_header(token),
    )
    assert resp.status_code == 404


async def test_delete_watch_success(client):
    """DELETE /watches/{watch_id} returns 204 and removes watch."""
    token = await _register_and_login(client)
    trip_id = await _create_trip(client, token)

    create_resp = await client.post(
        f"/api/v1/trips/{trip_id}/watches",
        json=VALID_WATCH,
        headers=_auth_header(token),
    )
    watch_id = create_resp.json()["data"]["id"]

    resp = await client.delete(
        f"/api/v1/watches/{watch_id}",
        headers=_auth_header(token),
    )
    assert resp.status_code == 204

    get_resp = await client.get(
        f"/api/v1/watches/{watch_id}",
        headers=_auth_header(token),
    )
    assert get_resp.status_code == 404


async def test_delete_watch_not_found(client):
    """DELETE /watches/{watch_id} with non-existent ID returns 404."""
    token = await _register_and_login(client)
    fake_id = str(uuid.uuid4())
    resp = await client.delete(
        f"/api/v1/watches/{fake_id}",
        headers=_auth_header(token),
    )
    assert resp.status_code == 404
