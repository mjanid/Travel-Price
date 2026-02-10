"""Business logic for price alert checking and alert history."""

from __future__ import annotations

import logging
import uuid
from datetime import datetime, timedelta, timezone

from fastapi import HTTPException, status
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.alert import Alert, AlertChannel, AlertStatus, AlertType
from app.models.price_snapshot import PriceSnapshot
from app.models.price_watch import PriceWatch
from app.models.trip import Trip
from app.models.user import User
from app.notifications.email import get_notifier
from app.notifications.base import NotificationPayload
from app.schemas.alert import AlertResponse

logger = logging.getLogger(__name__)


class AlertService:
    """Service for price alert checking, creation, and history.

    Args:
        db: The async database session.
    """

    def __init__(self, db: AsyncSession) -> None:
        self.db = db

    async def check_and_alert(
        self,
        trip_id: uuid.UUID,
        user_id: uuid.UUID,
        snapshots: list[PriceSnapshot],
    ) -> list[Alert]:
        """Check new snapshots against active PriceWatches and send alerts.

        For each active watch on this trip, finds the lowest price among new
        snapshots matching the watch's provider. If that price is at or below
        the target and the watch is not in cooldown, creates an alert and
        sends a notification.

        Args:
            trip_id: The trip that was just scraped.
            user_id: The trip owner.
            snapshots: The PriceSnapshot ORM objects just stored.

        Returns:
            List of Alert objects created (may be empty).
        """
        watches = await self._get_active_watches_for_trip(trip_id, user_id)
        if not watches:
            return []

        # Group snapshots by provider for fast lookup
        snapshots_by_provider: dict[str, list[PriceSnapshot]] = {}
        for snap in snapshots:
            snapshots_by_provider.setdefault(snap.provider, []).append(snap)

        # Load user and trip for notification messages
        user = await self._get_user(user_id)
        trip = await self._get_trip(trip_id)

        alerts: list[Alert] = []
        for watch in watches:
            provider_snapshots = snapshots_by_provider.get(watch.provider, [])
            if not provider_snapshots:
                continue

            # Find the lowest price snapshot for this provider
            best_snapshot = min(provider_snapshots, key=lambda s: s.price)

            if best_snapshot.price > watch.target_price:
                continue

            if await self._is_in_cooldown(watch):
                logger.debug(
                    "Watch %s in cooldown, skipping alert", watch.id
                )
                continue

            alert = await self._create_and_send_alert(
                watch, best_snapshot, user, trip
            )
            alerts.append(alert)

        return alerts

    # --- API-facing methods ---

    async def list_alerts_for_user(
        self, user_id: uuid.UUID, page: int = 1, per_page: int = 20
    ) -> tuple[list[AlertResponse], int]:
        """Get paginated alert history for a user.

        Args:
            user_id: The user's ID.
            page: Page number (1-indexed).
            per_page: Items per page.

        Returns:
            Tuple of (alert responses, total count).
        """
        conditions = [Alert.user_id == user_id]
        return await self._paginated_alerts(conditions, page, per_page)

    async def get_alert_by_id(
        self, user_id: uuid.UUID, alert_id: uuid.UUID
    ) -> AlertResponse:
        """Get a single alert by ID, enforcing ownership.

        Args:
            user_id: The requesting user's ID.
            alert_id: The alert to retrieve.

        Returns:
            The alert data.

        Raises:
            HTTPException: 404 if not found or not owned by user.
        """
        result = await self.db.execute(
            select(Alert).where(Alert.id == alert_id, Alert.user_id == user_id)
        )
        alert = result.scalar_one_or_none()
        if alert is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Alert not found",
            )
        return AlertResponse.model_validate(alert)

    async def list_alerts_for_watch(
        self,
        user_id: uuid.UUID,
        watch_id: uuid.UUID,
        page: int = 1,
        per_page: int = 20,
    ) -> tuple[list[AlertResponse], int]:
        """Get paginated alert history for a specific watch.

        Args:
            user_id: The requesting user's ID.
            watch_id: The watch to filter by.
            page: Page number (1-indexed).
            per_page: Items per page.

        Returns:
            Tuple of (alert responses, total count).
        """
        conditions = [Alert.user_id == user_id, Alert.price_watch_id == watch_id]
        return await self._paginated_alerts(conditions, page, per_page)

    # --- Internal helpers ---

    async def _get_active_watches_for_trip(
        self, trip_id: uuid.UUID, user_id: uuid.UUID
    ) -> list[PriceWatch]:
        """Fetch active PriceWatches for a trip."""
        result = await self.db.execute(
            select(PriceWatch).where(
                PriceWatch.trip_id == trip_id,
                PriceWatch.user_id == user_id,
                PriceWatch.is_active == True,  # noqa: E712
            )
        )
        return list(result.scalars().all())

    async def _is_in_cooldown(self, watch: PriceWatch) -> bool:
        """Check if a successful alert was sent within the cooldown window."""
        cutoff = datetime.now(timezone.utc) - timedelta(
            hours=watch.alert_cooldown_hours
        )
        result = await self.db.execute(
            select(func.count())
            .select_from(Alert)
            .where(
                Alert.price_watch_id == watch.id,
                Alert.status == AlertStatus.SENT.value,
                Alert.created_at > cutoff,
            )
        )
        return result.scalar_one() > 0

    async def _create_and_send_alert(
        self,
        watch: PriceWatch,
        snapshot: PriceSnapshot,
        user: User,
        trip: Trip,
    ) -> Alert:
        """Create an Alert record and dispatch the notification."""
        message = self._build_alert_message(watch, snapshot, trip)

        alert = Alert(
            price_watch_id=watch.id,
            user_id=user.id,
            price_snapshot_id=snapshot.id,
            alert_type=AlertType.PRICE_DROP.value,
            channel=AlertChannel.EMAIL.value,
            status=AlertStatus.PENDING.value,
            target_price=watch.target_price,
            triggered_price=snapshot.price,
            message=message,
        )
        self.db.add(alert)
        await self.db.flush()
        await self.db.refresh(alert)

        # Send notification
        try:
            notifier = get_notifier(AlertChannel.EMAIL.value)
            payload = NotificationPayload(
                recipient_email=user.email,
                recipient_name=user.full_name,
                subject=f"Price drop alert: {trip.origin} → {trip.destination}",
                body=message,
                alert_id=alert.id,
            )
            success = await notifier.send(payload)
            if success:
                alert.status = AlertStatus.SENT.value
                alert.sent_at = datetime.now(timezone.utc)
            else:
                alert.status = AlertStatus.FAILED.value
        except Exception:
            logger.exception("Failed to send notification for alert %s", alert.id)
            alert.status = AlertStatus.FAILED.value

        await self.db.flush()
        await self.db.refresh(alert)

        logger.info(
            "Alert %s created for watch %s (status=%s, price=%d <= target=%d)",
            alert.id,
            watch.id,
            alert.status,
            snapshot.price,
            watch.target_price,
        )
        return alert

    def _build_alert_message(
        self, watch: PriceWatch, snapshot: PriceSnapshot, trip: Trip
    ) -> str:
        """Build human-readable alert message body."""
        price_dollars = snapshot.price / 100
        target_dollars = watch.target_price / 100
        savings_dollars = target_dollars - price_dollars
        return (
            f"Great news! A flight from {trip.origin} to {trip.destination} "
            f"on {trip.departure_date} is now ${price_dollars:.2f}, "
            f"which is ${savings_dollars:.2f} below your target of "
            f"${target_dollars:.2f}."
        )

    async def _get_user(self, user_id: uuid.UUID) -> User:
        """Fetch a user by ID.

        Raises:
            HTTPException: 404 if user not found.
        """
        result = await self.db.execute(
            select(User).where(User.id == user_id)
        )
        user = result.scalar_one_or_none()
        if user is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found",
            )
        return user

    async def _get_trip(self, trip_id: uuid.UUID) -> Trip:
        """Fetch a trip by ID.

        Raises:
            HTTPException: 404 if trip not found.
        """
        result = await self.db.execute(
            select(Trip).where(Trip.id == trip_id)
        )
        trip = result.scalar_one_or_none()
        if trip is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Trip not found",
            )
        return trip

    async def _paginated_alerts(
        self,
        conditions: list,
        page: int,
        per_page: int,
    ) -> tuple[list[AlertResponse], int]:
        """Run a paginated alert query with the given conditions."""
        count_result = await self.db.execute(
            select(func.count()).select_from(Alert).where(*conditions)
        )
        total = count_result.scalar_one()

        offset = (page - 1) * per_page
        result = await self.db.execute(
            select(Alert)
            .where(*conditions)
            .order_by(Alert.created_at.desc())
            .offset(offset)
            .limit(per_page)
        )
        alerts = result.scalars().all()
        return [AlertResponse.model_validate(a) for a in alerts], total
