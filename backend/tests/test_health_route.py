"""Integration tests for health check endpoint."""


async def test_health_check_returns_ok(client):
    """GET /health returns 200 with status payload."""
    response = await client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}
