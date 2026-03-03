"""Tests for health and readiness probe endpoints."""

from unittest.mock import AsyncMock, patch


async def test_health_returns_200(client):
    """GET /health returns 200 with status ok."""
    response = await client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


async def test_health_does_not_require_auth(client):
    """GET /health returns 200 without any Authorization header."""
    # Explicitly ensure no auth header is sent
    response = await client.get("/health", headers={})
    assert response.status_code == 200
    assert response.json()["status"] == "ok"


async def test_ready_returns_200_when_healthy(client):
    """GET /ready returns 200 when Postgres and Redis are both reachable."""
    mock_redis = AsyncMock()
    mock_redis.ping = AsyncMock(return_value=True)
    mock_redis.aclose = AsyncMock()

    with patch("app.api.v1.health.aioredis.from_url", return_value=mock_redis):
        response = await client.get("/ready")

    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "ready"
    assert body["checks"]["postgres"] == "ok"
    assert body["checks"]["redis"] == "ok"


async def test_ready_returns_503_when_db_down(client, db_session):
    """GET /ready returns 503 when Postgres is unreachable."""
    mock_redis = AsyncMock()
    mock_redis.ping = AsyncMock(return_value=True)
    mock_redis.aclose = AsyncMock()

    # Mock the session's execute to simulate a DB failure
    with (
        patch("app.api.v1.health.aioredis.from_url", return_value=mock_redis),
        patch.object(db_session, "execute", side_effect=Exception("connection refused")),
    ):
        response = await client.get("/ready")

    assert response.status_code == 503
    body = response.json()
    assert body["status"] == "degraded"
    assert body["checks"]["postgres"] == "error"
    assert body["checks"]["redis"] == "ok"


async def test_ready_returns_503_when_redis_down(client):
    """GET /ready returns 503 when Redis is unreachable."""
    with patch(
        "app.api.v1.health.aioredis.from_url",
        side_effect=Exception("redis connection refused"),
    ):
        response = await client.get("/ready")

    assert response.status_code == 503
    body = response.json()
    assert body["status"] == "degraded"
    assert body["checks"]["postgres"] == "ok"
    assert body["checks"]["redis"] == "error"


async def test_ready_returns_503_when_both_down(client, db_session):
    """GET /ready returns 503 when both Postgres and Redis are unreachable."""
    with (
        patch(
            "app.api.v1.health.aioredis.from_url",
            side_effect=Exception("redis connection refused"),
        ),
        patch.object(db_session, "execute", side_effect=Exception("connection refused")),
    ):
        response = await client.get("/ready")

    assert response.status_code == 503
    body = response.json()
    assert body["status"] == "degraded"
    assert body["checks"]["postgres"] == "error"
    assert body["checks"]["redis"] == "error"
