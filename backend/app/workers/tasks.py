"""Celery task definitions for scheduled scraping."""

from __future__ import annotations

import asyncio
import logging
import uuid

from app.workers.celery_app import celery_app

logger = logging.getLogger(__name__)


@celery_app.task(name="app.workers.tasks.dispatch_due_scrapes", bind=True)
def dispatch_due_scrapes(self) -> dict:
    """Dispatcher task: find due watches and dispatch individual scrape tasks.

    Runs every 5 minutes via Celery Beat.  Queries active watches whose
    next_scrape_at is NULL or <= now(), dispatches a scrape_single_trip
    task for each, and advances next_scrape_at.
    """
    try:
        return asyncio.run(_dispatch_due_scrapes_async())
    except Exception as exc:
        logger.exception("dispatch_due_scrapes failed: %s", exc)
        raise


async def _dispatch_due_scrapes_async() -> dict:
    """Async implementation of the due-watch dispatcher."""
    from app.services.scheduled_scrape_service import ScheduledScrapeService
    from app.workers.db import get_worker_db

    async with get_worker_db() as db:
        service = ScheduledScrapeService(db)
        due_watches = await service.get_due_watches()

        dispatched = 0
        for watch in due_watches:
            scrape_single_trip.delay(
                str(watch.trip_id), str(watch.user_id), watch.provider
            )
            await service.mark_dispatched(watch)
            dispatched += 1

    logger.info("Dispatched %d scrape tasks for due watches", dispatched)
    return {"dispatched": dispatched, "watches_checked": len(due_watches)}


@celery_app.task(
    name="app.workers.tasks.scrape_single_trip",
    bind=True,
    max_retries=3,
    default_retry_delay=60,
)
def scrape_single_trip(
    self, trip_id: str, user_id: str, provider: str = "google_flights"
) -> dict:
    """Scrape prices for a single trip.

    Args:
        trip_id: Trip UUID as string (JSON-serializable).
        user_id: User UUID as string (JSON-serializable).
        provider: Scraper provider name.

    Returns:
        Dict with trip_id and count of snapshots stored.
    """
    try:
        return asyncio.run(_scrape_single_trip_async(trip_id, user_id, provider))
    except Exception as exc:
        logger.exception(
            "scrape_single_trip failed for trip %s: %s", trip_id, exc
        )
        raise self.retry(exc=exc)


async def _scrape_single_trip_async(
    trip_id: str, user_id: str, provider: str = "google_flights"
) -> dict:
    """Async implementation of single-trip scraping."""
    from app.services.scheduled_scrape_service import ScheduledScrapeService
    from app.workers.db import get_worker_db

    try:
        tid = uuid.UUID(trip_id)
        uid = uuid.UUID(user_id)
    except ValueError:
        logger.error("Invalid UUID format: trip_id=%s, user_id=%s", trip_id, user_id)
        raise

    async with get_worker_db() as db:
        service = ScheduledScrapeService(db)
        count = await service.scrape_trip_background(tid, uid, provider=provider)

    return {"trip_id": trip_id, "snapshots_stored": count}
