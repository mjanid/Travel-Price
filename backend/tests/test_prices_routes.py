"""Integration tests for price/scrape API endpoints."""

import uuid
from datetime import datetime, timezone
from unittest.mock import AsyncMock, patch

from app.scrapers.types import PriceResult, ScrapeError


VALID_TRIP = {
    "origin": "JFK",
    "destination": "LAX",
    "departure_date": "2026-06-15",
    "return_date": "2026-06-22",
    "travelers": 2,
    "trip_type": "flight",
}


async def _register_and_login(client, email="price@example.com"):
    """Helper to register a user and return access token."""
    await client.post(
        "/api/v1/auth/register",
        json={
            "email": email,
            "password": "securepassword",
            "full_name": "Price Tester",
        },
    )
    resp = await client.post(
        "/api/v1/auth/login",
        json={"email": email, "password": "securepassword"},
    )
    return resp.json()["data"]["access_token"]


def _auth_header(token):
    return {"Authorization": f"Bearer {token}"}


async def _create_trip(client, token):
    """Create a trip and return its ID."""
    resp = await client.post(
        "/api/v1/trips/",
        json=VALID_TRIP,
        headers=_auth_header(token),
    )
    return resp.json()["data"]["id"]


def _mock_results():
    """Return mock scraper results."""
    now = datetime.now(timezone.utc)
    return [
        PriceResult(
            provider="google_flights",
            price=25000,
            currency="USD",
            cabin_class="economy",
            airline="Delta",
            stops=0,
            scraped_at=now,
        ),
    ]


async def test_scrape_trip_success(client):
    """POST /trips/{id}/scrape returns 201 with scraped data."""
    token = await _register_and_login(client)
    trip_id = await _create_trip(client, token)

    mock_scraper = AsyncMock()
    mock_scraper.execute.return_value = _mock_results()

    with patch("app.services.scraper_service.get_scraper", return_value=mock_scraper):
        resp = await client.post(
            f"/api/v1/trips/{trip_id}/scrape",
            json={"provider": "google_flights", "cabin_class": "economy"},
            headers=_auth_header(token),
        )

    assert resp.status_code == 201
    body = resp.json()
    assert len(body["data"]) == 1
    assert body["data"][0]["price"] == 25000
    assert body["data"][0]["provider"] == "google_flights"
    assert body["data"][0]["airline"] == "Delta"


async def test_scrape_trip_default_params(client):
    """POST /trips/{id}/scrape works with empty body (defaults)."""
    token = await _register_and_login(client)
    trip_id = await _create_trip(client, token)

    mock_scraper = AsyncMock()
    mock_scraper.execute.return_value = _mock_results()

    with patch("app.services.scraper_service.get_scraper", return_value=mock_scraper):
        resp = await client.post(
            f"/api/v1/trips/{trip_id}/scrape",
            headers=_auth_header(token),
        )

    assert resp.status_code == 201


async def test_scrape_trip_not_found(client):
    """POST /trips/{id}/scrape returns 404 for non-existent trip."""
    token = await _register_and_login(client)
    fake_id = str(uuid.uuid4())

    resp = await client.post(
        f"/api/v1/trips/{fake_id}/scrape",
        json={"provider": "google_flights"},
        headers=_auth_header(token),
    )
    assert resp.status_code == 404


async def test_scrape_trip_unauthenticated(client):
    """POST /trips/{id}/scrape without token returns 401."""
    fake_id = str(uuid.uuid4())
    resp = await client.post(f"/api/v1/trips/{fake_id}/scrape")
    assert resp.status_code == 401


async def test_scrape_trip_unknown_provider(client):
    """POST /trips/{id}/scrape with unknown provider returns 422."""
    token = await _register_and_login(client)
    trip_id = await _create_trip(client, token)

    resp = await client.post(
        f"/api/v1/trips/{trip_id}/scrape",
        json={"provider": "nonexistent_provider"},
        headers=_auth_header(token),
    )
    assert resp.status_code == 422


async def test_scrape_trip_scraper_failure(client):
    """POST /trips/{id}/scrape returns 502 on scraper failure."""
    token = await _register_and_login(client)
    trip_id = await _create_trip(client, token)

    mock_scraper = AsyncMock()
    mock_scraper.execute.side_effect = ScrapeError("google_flights", "Timeout", 3)

    with patch("app.services.scraper_service.get_scraper", return_value=mock_scraper):
        resp = await client.post(
            f"/api/v1/trips/{trip_id}/scrape",
            json={"provider": "google_flights"},
            headers=_auth_header(token),
        )

    assert resp.status_code == 502


async def test_get_price_history_empty(client):
    """GET /trips/{id}/prices returns empty list when no snapshots."""
    token = await _register_and_login(client)
    trip_id = await _create_trip(client, token)

    resp = await client.get(
        f"/api/v1/trips/{trip_id}/prices",
        headers=_auth_header(token),
    )
    assert resp.status_code == 200
    body = resp.json()
    assert body["data"] == []
    assert body["meta"]["total"] == 0


async def test_get_price_history_after_scrape(client):
    """GET /trips/{id}/prices returns data after a scrape."""
    token = await _register_and_login(client)
    trip_id = await _create_trip(client, token)

    mock_scraper = AsyncMock()
    mock_scraper.execute.return_value = _mock_results()

    with patch("app.services.scraper_service.get_scraper", return_value=mock_scraper):
        await client.post(
            f"/api/v1/trips/{trip_id}/scrape",
            json={"provider": "google_flights"},
            headers=_auth_header(token),
        )

    resp = await client.get(
        f"/api/v1/trips/{trip_id}/prices",
        headers=_auth_header(token),
    )
    assert resp.status_code == 200
    body = resp.json()
    assert body["meta"]["total"] == 1
    assert body["data"][0]["price"] == 25000


async def test_get_price_history_pagination(client):
    """GET /trips/{id}/prices respects pagination params."""
    token = await _register_and_login(client)
    trip_id = await _create_trip(client, token)

    mock_scraper = AsyncMock()
    now = datetime.now(timezone.utc)
    mock_scraper.execute.return_value = [
        PriceResult(
            provider="google_flights",
            price=20000 + i * 1000,
            currency="USD",
            scraped_at=now,
        )
        for i in range(5)
    ]

    with patch("app.services.scraper_service.get_scraper", return_value=mock_scraper):
        await client.post(
            f"/api/v1/trips/{trip_id}/scrape",
            json={"provider": "google_flights"},
            headers=_auth_header(token),
        )

    resp = await client.get(
        f"/api/v1/trips/{trip_id}/prices?page=1&per_page=2",
        headers=_auth_header(token),
    )
    body = resp.json()
    assert len(body["data"]) == 2
    assert body["meta"]["total"] == 5
    assert body["meta"]["total_pages"] == 3


async def test_get_price_history_filter_provider(client):
    """GET /trips/{id}/prices?provider= filters by provider."""
    token = await _register_and_login(client)
    trip_id = await _create_trip(client, token)

    mock_scraper = AsyncMock()
    mock_scraper.execute.return_value = _mock_results()

    with patch("app.services.scraper_service.get_scraper", return_value=mock_scraper):
        await client.post(
            f"/api/v1/trips/{trip_id}/scrape",
            json={"provider": "google_flights"},
            headers=_auth_header(token),
        )

    # Filter by provider that has data
    resp = await client.get(
        f"/api/v1/trips/{trip_id}/prices?provider=google_flights",
        headers=_auth_header(token),
    )
    assert resp.json()["meta"]["total"] == 1

    # Filter by provider with no data
    resp2 = await client.get(
        f"/api/v1/trips/{trip_id}/prices?provider=other",
        headers=_auth_header(token),
    )
    assert resp2.json()["meta"]["total"] == 0


async def test_get_price_history_not_found(client):
    """GET /trips/{id}/prices returns 404 for non-existent trip."""
    token = await _register_and_login(client)
    fake_id = str(uuid.uuid4())

    resp = await client.get(
        f"/api/v1/trips/{fake_id}/prices",
        headers=_auth_header(token),
    )
    assert resp.status_code == 404


async def test_get_price_history_unauthenticated(client):
    """GET /trips/{id}/prices without token returns 401."""
    fake_id = str(uuid.uuid4())
    resp = await client.get(f"/api/v1/trips/{fake_id}/prices")
    assert resp.status_code == 401
