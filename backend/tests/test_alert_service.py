"""Tests for AlertService."""

import uuid
from datetime import date, datetime, timedelta, timezone
from unittest.mock import AsyncMock, patch

import pytest
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.alert import Alert, AlertStatus
from app.models.price_snapshot import PriceSnapshot
from app.models.price_watch import PriceWatch
from app.models.trip import Trip
from app.models.user import User
from app.services.alert_service import AlertService


async def _create_user(db: AsyncSession, email: str = "alert@example.com") -> User:
    """Create a test user."""
    user = User(email=email, hashed_password="fakehash", full_name="Alert Tester")
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


async def _create_watch(
    db: AsyncSession,
    user_id: uuid.UUID,
    trip_id: uuid.UUID,
    target_price: int = 30000,
    is_active: bool = True,
    provider: str = "google_flights",
    cooldown_hours: int = 6,
) -> PriceWatch:
    """Create a test price watch."""
    watch = PriceWatch(
        user_id=user_id,
        trip_id=trip_id,
        provider=provider,
        target_price=target_price,
        currency="USD",
        is_active=is_active,
        alert_cooldown_hours=cooldown_hours,
    )
    db.add(watch)
    await db.flush()
    await db.refresh(watch)
    return watch


async def _create_snapshot(
    db: AsyncSession,
    trip_id: uuid.UUID,
    user_id: uuid.UUID,
    price: int = 25000,
    provider: str = "google_flights",
) -> PriceSnapshot:
    """Create a test price snapshot."""
    snapshot = PriceSnapshot(
        trip_id=trip_id,
        user_id=user_id,
        provider=provider,
        price=price,
        currency="USD",
    )
    db.add(snapshot)
    await db.flush()
    await db.refresh(snapshot)
    return snapshot


# --- check_and_alert tests ---


async def test_check_and_alert_triggers_when_below_target(db_session):
    """Creates alert when snapshot price < target price."""
    user = await _create_user(db_session)
    trip = await _create_trip(db_session, user.id)
    watch = await _create_watch(db_session, user.id, trip.id, target_price=30000)
    snapshot = await _create_snapshot(db_session, trip.id, user.id, price=25000)

    service = AlertService(db_session)
    alerts = await service.check_and_alert(trip.id, user.id, [snapshot])

    assert len(alerts) == 1
    assert alerts[0].triggered_price == 25000
    assert alerts[0].target_price == 30000
    assert alerts[0].status == AlertStatus.SENT.value
    assert alerts[0].sent_at is not None


async def test_check_and_alert_triggers_at_exact_target(db_session):
    """Creates alert when snapshot price == target price."""
    user = await _create_user(db_session)
    trip = await _create_trip(db_session, user.id)
    watch = await _create_watch(db_session, user.id, trip.id, target_price=25000)
    snapshot = await _create_snapshot(db_session, trip.id, user.id, price=25000)

    service = AlertService(db_session)
    alerts = await service.check_and_alert(trip.id, user.id, [snapshot])

    assert len(alerts) == 1
    assert alerts[0].triggered_price == 25000


async def test_check_and_alert_no_trigger_when_above_target(db_session):
    """No alert when snapshot price > target price."""
    user = await _create_user(db_session)
    trip = await _create_trip(db_session, user.id)
    watch = await _create_watch(db_session, user.id, trip.id, target_price=20000)
    snapshot = await _create_snapshot(db_session, trip.id, user.id, price=25000)

    service = AlertService(db_session)
    alerts = await service.check_and_alert(trip.id, user.id, [snapshot])

    assert len(alerts) == 0


async def test_check_and_alert_respects_cooldown(db_session):
    """No alert if one was sent within cooldown window."""
    user = await _create_user(db_session)
    trip = await _create_trip(db_session, user.id)
    watch = await _create_watch(
        db_session, user.id, trip.id, target_price=30000, cooldown_hours=6
    )
    snapshot1 = await _create_snapshot(db_session, trip.id, user.id, price=25000)

    # Create an existing recent alert
    recent_alert = Alert(
        price_watch_id=watch.id,
        user_id=user.id,
        price_snapshot_id=snapshot1.id,
        alert_type="price_drop",
        channel="email",
        status=AlertStatus.SENT.value,
        target_price=30000,
        triggered_price=25000,
        sent_at=datetime.now(timezone.utc),
    )
    db_session.add(recent_alert)
    await db_session.flush()

    # New snapshot, should be blocked by cooldown
    snapshot2 = await _create_snapshot(db_session, trip.id, user.id, price=24000)

    service = AlertService(db_session)
    alerts = await service.check_and_alert(trip.id, user.id, [snapshot2])

    assert len(alerts) == 0


async def test_check_and_alert_alerts_after_cooldown_expires(db_session):
    """Alert fires when cooldown has passed."""
    user = await _create_user(db_session)
    trip = await _create_trip(db_session, user.id)
    watch = await _create_watch(
        db_session, user.id, trip.id, target_price=30000, cooldown_hours=6
    )
    snapshot1 = await _create_snapshot(db_session, trip.id, user.id, price=25000)

    # Create an old alert (outside cooldown window)
    old_alert = Alert(
        price_watch_id=watch.id,
        user_id=user.id,
        price_snapshot_id=snapshot1.id,
        alert_type="price_drop",
        channel="email",
        status=AlertStatus.SENT.value,
        target_price=30000,
        triggered_price=25000,
        sent_at=datetime.now(timezone.utc) - timedelta(hours=7),
        created_at=datetime.now(timezone.utc) - timedelta(hours=7),
    )
    db_session.add(old_alert)
    await db_session.flush()

    snapshot2 = await _create_snapshot(db_session, trip.id, user.id, price=24000)

    service = AlertService(db_session)
    alerts = await service.check_and_alert(trip.id, user.id, [snapshot2])

    assert len(alerts) == 1


async def test_check_and_alert_only_active_watches(db_session):
    """Inactive watches are skipped."""
    user = await _create_user(db_session)
    trip = await _create_trip(db_session, user.id)
    watch = await _create_watch(
        db_session, user.id, trip.id, target_price=30000, is_active=False
    )
    snapshot = await _create_snapshot(db_session, trip.id, user.id, price=25000)

    service = AlertService(db_session)
    alerts = await service.check_and_alert(trip.id, user.id, [snapshot])

    assert len(alerts) == 0


async def test_check_and_alert_matches_provider(db_session):
    """Watch for provider X ignores snapshots from provider Y."""
    user = await _create_user(db_session)
    trip = await _create_trip(db_session, user.id)
    watch = await _create_watch(
        db_session, user.id, trip.id, target_price=30000, provider="google_flights"
    )
    snapshot = await _create_snapshot(
        db_session, trip.id, user.id, price=25000, provider="other_provider"
    )

    service = AlertService(db_session)
    alerts = await service.check_and_alert(trip.id, user.id, [snapshot])

    assert len(alerts) == 0


async def test_check_and_alert_picks_lowest_price(db_session):
    """When multiple snapshots match, alert uses the cheapest."""
    user = await _create_user(db_session)
    trip = await _create_trip(db_session, user.id)
    watch = await _create_watch(db_session, user.id, trip.id, target_price=30000)

    snap_high = await _create_snapshot(db_session, trip.id, user.id, price=28000)
    snap_low = await _create_snapshot(db_session, trip.id, user.id, price=22000)

    service = AlertService(db_session)
    alerts = await service.check_and_alert(trip.id, user.id, [snap_high, snap_low])

    assert len(alerts) == 1
    assert alerts[0].triggered_price == 22000


async def test_check_and_alert_notification_failure_creates_failed_alert(db_session):
    """When notifier.send() returns False, alert status is 'failed'."""
    user = await _create_user(db_session)
    trip = await _create_trip(db_session, user.id)
    watch = await _create_watch(db_session, user.id, trip.id, target_price=30000)
    snapshot = await _create_snapshot(db_session, trip.id, user.id, price=25000)

    mock_notifier = AsyncMock()
    mock_notifier.send.return_value = False

    with patch(
        "app.services.alert_service.get_notifier", return_value=mock_notifier
    ):
        service = AlertService(db_session)
        alerts = await service.check_and_alert(trip.id, user.id, [snapshot])

    assert len(alerts) == 1
    assert alerts[0].status == AlertStatus.FAILED.value
    assert alerts[0].sent_at is None


async def test_check_and_alert_multiple_watches(db_session):
    """Multiple watches on same trip are evaluated independently."""
    user = await _create_user(db_session)
    trip = await _create_trip(db_session, user.id)
    watch1 = await _create_watch(db_session, user.id, trip.id, target_price=30000)
    watch2 = await _create_watch(db_session, user.id, trip.id, target_price=20000)

    snapshot = await _create_snapshot(db_session, trip.id, user.id, price=25000)

    service = AlertService(db_session)
    alerts = await service.check_and_alert(trip.id, user.id, [snapshot])

    # watch1 triggers (25000 <= 30000), watch2 doesn't (25000 > 20000)
    assert len(alerts) == 1
    assert alerts[0].target_price == 30000


async def test_check_and_alert_no_watches(db_session):
    """No alerts when trip has no watches."""
    user = await _create_user(db_session)
    trip = await _create_trip(db_session, user.id)
    snapshot = await _create_snapshot(db_session, trip.id, user.id, price=25000)

    service = AlertService(db_session)
    alerts = await service.check_and_alert(trip.id, user.id, [snapshot])

    assert len(alerts) == 0


# --- list/get tests ---


async def test_list_alerts_for_user(db_session):
    """list_alerts_for_user() returns paginated alerts."""
    user = await _create_user(db_session)
    trip = await _create_trip(db_session, user.id)
    watch = await _create_watch(db_session, user.id, trip.id, target_price=30000)
    snapshot = await _create_snapshot(db_session, trip.id, user.id, price=25000)

    service = AlertService(db_session)
    await service.check_and_alert(trip.id, user.id, [snapshot])

    alerts, total = await service.list_alerts_for_user(user.id)
    assert total == 1
    assert len(alerts) == 1
    assert alerts[0].user_id == user.id


async def test_list_alerts_for_watch(db_session):
    """list_alerts_for_watch() filters by watch_id."""
    user = await _create_user(db_session)
    trip = await _create_trip(db_session, user.id)
    watch1 = await _create_watch(db_session, user.id, trip.id, target_price=30000)
    watch2 = await _create_watch(db_session, user.id, trip.id, target_price=28000)

    snap1 = await _create_snapshot(db_session, trip.id, user.id, price=25000)
    snap2 = await _create_snapshot(db_session, trip.id, user.id, price=27000)

    service = AlertService(db_session)
    # This will trigger alerts for both watches on snap1 (25000 <= 30000 and 25000 <= 28000)
    await service.check_and_alert(trip.id, user.id, [snap1, snap2])

    alerts1, total1 = await service.list_alerts_for_watch(user.id, watch1.id)
    alerts2, total2 = await service.list_alerts_for_watch(user.id, watch2.id)

    assert total1 == 1
    assert total2 == 1
    assert alerts1[0].price_watch_id == watch1.id
    assert alerts2[0].price_watch_id == watch2.id


async def test_get_alert_by_id(db_session):
    """get_alert_by_id() returns a single alert."""
    user = await _create_user(db_session)
    trip = await _create_trip(db_session, user.id)
    watch = await _create_watch(db_session, user.id, trip.id, target_price=30000)
    snapshot = await _create_snapshot(db_session, trip.id, user.id, price=25000)

    service = AlertService(db_session)
    created = await service.check_and_alert(trip.id, user.id, [snapshot])

    alert = await service.get_alert_by_id(user.id, created[0].id)
    assert alert.id == created[0].id


async def test_get_alert_by_id_not_found(db_session):
    """get_alert_by_id() raises 404 for nonexistent alert."""
    user = await _create_user(db_session)

    service = AlertService(db_session)
    with pytest.raises(Exception) as exc_info:
        await service.get_alert_by_id(user.id, uuid.uuid4())
    assert "404" in str(exc_info.value.status_code)
