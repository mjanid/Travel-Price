"""Integration tests for alert API routes."""

import uuid
from datetime import date, datetime, timezone

from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import create_access_token
from app.models.alert import Alert, AlertStatus
from app.models.price_snapshot import PriceSnapshot
from app.models.price_watch import PriceWatch
from app.models.trip import Trip
from app.models.user import User
from tests.factories import build_user


async def _setup_with_alert(
    db: AsyncSession,
) -> tuple[User, str, Alert]:
    """Create user, trip, watch, snapshot, and alert. Return (user, auth, alert)."""
    user = build_user(email="alertroute@example.com")
    db.add(user)
    await db.flush()
    await db.refresh(user)
    token = create_access_token(str(user.id))

    trip = Trip(
        user_id=user.id,
        origin="JFK",
        destination="LAX",
        departure_date=date(2027, 6, 15),
        travelers=1,
        trip_type="flight",
    )
    db.add(trip)
    await db.flush()
    await db.refresh(trip)

    watch = PriceWatch(
        user_id=user.id,
        trip_id=trip.id,
        provider="google_flights",
        target_price=30000,
        currency="USD",
        is_active=True,
    )
    db.add(watch)
    await db.flush()
    await db.refresh(watch)

    snapshot = PriceSnapshot(
        trip_id=trip.id,
        user_id=user.id,
        provider="google_flights",
        price=25000,
        currency="USD",
    )
    db.add(snapshot)
    await db.flush()
    await db.refresh(snapshot)

    alert = Alert(
        price_watch_id=watch.id,
        user_id=user.id,
        price_snapshot_id=snapshot.id,
        alert_type="price_drop",
        channel="email",
        status=AlertStatus.SENT.value,
        target_price=30000,
        triggered_price=25000,
        message="Test alert",
        sent_at=datetime.now(timezone.utc),
    )
    db.add(alert)
    await db.flush()
    await db.refresh(alert)

    return user, f"Bearer {token}", alert


async def test_list_alerts(client: AsyncClient, db_session: AsyncSession):
    """GET /alerts/ returns paginated alerts for the user."""
    user, auth, alert = await _setup_with_alert(db_session)

    resp = await client.get(
        "/api/v1/alerts/", headers={"Authorization": auth}
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["meta"]["total"] == 1
    assert data["data"][0]["id"] == str(alert.id)


async def test_list_alerts_unauthenticated(client: AsyncClient):
    """GET /alerts/ requires authentication."""
    resp = await client.get("/api/v1/alerts/")
    assert resp.status_code == 401


async def test_get_alert(client: AsyncClient, db_session: AsyncSession):
    """GET /alerts/{id} returns a single alert."""
    user, auth, alert = await _setup_with_alert(db_session)

    resp = await client.get(
        f"/api/v1/alerts/{alert.id}", headers={"Authorization": auth}
    )
    assert resp.status_code == 200
    assert resp.json()["data"]["id"] == str(alert.id)
    assert resp.json()["data"]["triggered_price"] == 25000


async def test_get_alert_not_found(client: AsyncClient, db_session: AsyncSession):
    """GET /alerts/{id} returns 404 for nonexistent alert."""
    user, auth, _ = await _setup_with_alert(db_session)

    resp = await client.get(
        f"/api/v1/alerts/{uuid.uuid4()}", headers={"Authorization": auth}
    )
    assert resp.status_code == 404


async def test_list_watch_alerts(client: AsyncClient, db_session: AsyncSession):
    """GET /watches/{id}/alerts returns alerts for that watch."""
    user, auth, alert = await _setup_with_alert(db_session)

    resp = await client.get(
        f"/api/v1/watches/{alert.price_watch_id}/alerts",
        headers={"Authorization": auth},
    )
    assert resp.status_code == 200
    assert resp.json()["meta"]["total"] == 1
    assert resp.json()["data"][0]["price_watch_id"] == str(alert.price_watch_id)
