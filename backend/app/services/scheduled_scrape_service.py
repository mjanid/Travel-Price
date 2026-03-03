"""Business logic for scheduled/background scraping."""

from __future__ import annotations

import json
import logging
import uuid
from datetime import datetime, timedelta, timezone

from sqlalchemy import or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.price_snapshot import PriceSnapshot
from app.models.price_watch import PriceWatch
from app.models.trip import Trip
from app.scrapers.registry import get_scraper
from app.scrapers.types import PriceResult, ScrapeError, ScrapeQuery

logger = logging.getLogger(__name__)


class ScheduledScrapeService:
    """Service for background/scheduled scraping operations.

    Unlike ScraperService, this does not raise HTTPExceptions.
    Errors are logged and returned as results.

    Args:
        db: The async database session.
    """

    def __init__(self, db: AsyncSession) -> None:
        self.db = db

    async def get_due_watches(self) -> list[PriceWatch]:
        """Return active watches that are due for scraping.

        A watch is due when next_scrape_at is NULL (never scraped) or
        next_scrape_at <= now().  Only includes watches for trips whose
        departure date has not yet passed.

        Returns:
            List of PriceWatch ORM objects that should be scraped.
        """
        now = datetime.now(timezone.utc)
        today = now.date()
        result = await self.db.execute(
            select(PriceWatch)
            .join(Trip, PriceWatch.trip_id == Trip.id)
            .where(
                PriceWatch.is_active.is_(True),
                Trip.departure_date >= today,
                or_(
                    PriceWatch.next_scrape_at.is_(None),
                    PriceWatch.next_scrape_at <= now,
                ),
            )
            .order_by(PriceWatch.created_at)
        )
        return list(result.scalars().all())

    async def mark_dispatched(self, watch: PriceWatch) -> None:
        """Set next_scrape_at to now + watch's interval after dispatching.

        Args:
            watch: The PriceWatch that was just dispatched.
        """
        now = datetime.now(timezone.utc)
        watch.next_scrape_at = now + timedelta(minutes=watch.scrape_interval_minutes)
        await self.db.flush()

    async def scrape_trip_background(
        self,
        trip_id: uuid.UUID,
        user_id: uuid.UUID,
        provider: str = "google_flights",
    ) -> int:
        """Scrape a single trip in background context.

        Does not raise on failure -- logs errors and returns 0.

        Args:
            trip_id: The trip to scrape.
            user_id: The trip owner's ID.
            provider: Scraper provider name.

        Returns:
            Number of snapshots stored.
        """
        try:
            result = await self.db.execute(
                select(Trip).where(Trip.id == trip_id, Trip.user_id == user_id)
            )
            trip = result.scalar_one_or_none()
            if trip is None:
                logger.warning(
                    "Trip %s not found for user %s, skipping", trip_id, user_id
                )
                return 0

            scraper = get_scraper(provider)
            query = ScrapeQuery(
                origin=trip.origin,
                destination=trip.destination,
                departure_date=trip.departure_date,
                return_date=trip.return_date,
                travelers=trip.travelers,
                cabin_class="economy",
                trip_id=trip_id,
                user_id=user_id,
            )
            results = await scraper.execute(query)
            snapshots = await self._store_results(results, trip_id, user_id)

            # Check price watches and send alerts
            if snapshots:
                try:
                    from app.services.alert_service import AlertService

                    alert_service = AlertService(self.db)
                    await alert_service.check_and_alert(trip_id, user_id, snapshots)
                except Exception as exc:
                    logger.error(
                        "Alert check failed for trip %s: %s", trip_id, exc
                    )

            logger.info(
                "Scraped %d results for trip %s", len(snapshots), trip_id
            )
            return len(snapshots)

        except ScrapeError as exc:
            logger.error("Scrape failed for trip %s: %s", trip_id, exc)
            return 0
        except Exception as exc:
            logger.exception("Unexpected error scraping trip %s: %s", trip_id, exc)
            return 0

    async def _store_results(
        self,
        results: list[PriceResult],
        trip_id: uuid.UUID,
        user_id: uuid.UUID,
    ) -> list[PriceSnapshot]:
        """Store scrape results as PriceSnapshot records.

        Args:
            results: List of PriceResult from the scraper.
            trip_id: Associated trip ID.
            user_id: Associated user ID.

        Returns:
            List of stored PriceSnapshot ORM objects.
        """
        snapshots: list[PriceSnapshot] = []
        for result in results:
            raw_data_str = None
            if result.raw_data is not None:
                try:
                    raw_data_str = json.dumps(result.raw_data, default=str)
                except (TypeError, ValueError):
                    raw_data_str = str(result.raw_data)

            snapshot = PriceSnapshot(
                trip_id=trip_id,
                user_id=user_id,
                provider=result.provider,
                price=result.price,
                currency=result.currency,
                cabin_class=result.cabin_class,
                airline=result.airline,
                outbound_departure=result.outbound_departure,
                outbound_arrival=result.outbound_arrival,
                return_departure=result.return_departure,
                return_arrival=result.return_arrival,
                stops=result.stops,
                raw_data=raw_data_str,
                scraped_at=result.scraped_at,
            )
            self.db.add(snapshot)
            snapshots.append(snapshot)

        if snapshots:
            await self.db.flush()
            for snap in snapshots:
                await self.db.refresh(snap)

        return snapshots
