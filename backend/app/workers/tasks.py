"""Celery task definitions for scheduled scraping."""

from __future__ import annotations

import asyncio
import logging
import uuid

from app.workers.celery_app import celery_app

logger = logging.getLogger(__name__)


@celery_app.task(name="app.workers.tasks.scrape_all_active_trips", bind=True)
def scrape_all_active_trips(self) -> dict:
    """Fan-out task: find active trips and dispatch individual scrape tasks."""
    return asyncio.run(_scrape_all_active_trips_async())


async def _scrape_all_active_trips_async() -> dict:
    """Async implementation of the fan-out logic."""
    from app.services.scheduled_scrape_service import ScheduledScrapeService
    from app.workers.db import get_worker_db

    async with get_worker_db() as db:
        service = ScheduledScrapeService(db)
        trip_pairs = await service.get_active_trip_ids()

    dispatched = 0
    for trip_id, user_id in trip_pairs:
        scrape_single_trip.delay(str(trip_id), str(user_id))
        dispatched += 1

    logger.info("Dispatched %d scrape tasks", dispatched)
    return {"dispatched": dispatched, "trips": len(trip_pairs)}


@celery_app.task(
    name="app.workers.tasks.scrape_single_trip",
    bind=True,
    max_retries=2,
    default_retry_delay=60,
)
def scrape_single_trip(self, trip_id: str, user_id: str) -> dict:
    """Scrape prices for a single trip.

    Args:
        trip_id: Trip UUID as string (JSON-serializable).
        user_id: User UUID as string (JSON-serializable).

    Returns:
        Dict with trip_id and count of snapshots stored.
    """
    return asyncio.run(_scrape_single_trip_async(trip_id, user_id))


async def _scrape_single_trip_async(trip_id: str, user_id: str) -> dict:
    """Async implementation of single-trip scraping."""
    from app.services.scheduled_scrape_service import ScheduledScrapeService
    from app.workers.db import get_worker_db

    tid = uuid.UUID(trip_id)
    uid = uuid.UUID(user_id)

    async with get_worker_db() as db:
        service = ScheduledScrapeService(db)
        count = await service.scrape_trip_background(tid, uid)

    return {"trip_id": trip_id, "snapshots_stored": count}
