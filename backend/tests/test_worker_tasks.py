"""Tests for Celery worker tasks."""

import uuid
from contextlib import asynccontextmanager
from datetime import datetime, timedelta, timezone
from unittest.mock import AsyncMock, patch

import pytest

from app.workers.tasks import (
    _dispatch_due_scrapes_async,
    _scrape_single_trip_async,
)


def _mock_get_worker_db(mock_session):
    """Create a mock get_worker_db context manager."""

    @asynccontextmanager
    async def _get_worker_db():
        yield mock_session

    return _get_worker_db


def _make_mock_watch(
    trip_id=None, user_id=None, provider="google_flights",
    scrape_interval_minutes=60, next_scrape_at=None,
):
    """Create a mock PriceWatch object."""
    watch = AsyncMock()
    watch.trip_id = trip_id or uuid.uuid4()
    watch.user_id = user_id or uuid.uuid4()
    watch.provider = provider
    watch.scrape_interval_minutes = scrape_interval_minutes
    watch.next_scrape_at = next_scrape_at
    return watch


# --- dispatch_due_scrapes tests ---


async def test_dispatch_due_scrapes_dispatches_tasks():
    """Dispatcher dispatches one scrape_single_trip per due watch."""
    watch1 = _make_mock_watch()
    watch2 = _make_mock_watch()

    mock_service = AsyncMock()
    mock_service.get_due_watches.return_value = [watch1, watch2]

    mock_session = AsyncMock()

    with (
        patch(
            "app.workers.db.get_worker_db",
            _mock_get_worker_db(mock_session),
        ),
        patch(
            "app.services.scheduled_scrape_service.ScheduledScrapeService",
            return_value=mock_service,
        ),
        patch("app.workers.tasks.scrape_single_trip") as mock_task,
    ):
        result = await _dispatch_due_scrapes_async()

    assert result["dispatched"] == 2
    assert result["watches_checked"] == 2
    assert mock_task.delay.call_count == 2
    mock_task.delay.assert_any_call(
        str(watch1.trip_id), str(watch1.user_id), watch1.provider
    )
    mock_task.delay.assert_any_call(
        str(watch2.trip_id), str(watch2.user_id), watch2.provider
    )
    assert mock_service.mark_dispatched.call_count == 2


async def test_dispatch_due_scrapes_no_due_watches():
    """Dispatcher dispatches nothing when no watches are due."""
    mock_service = AsyncMock()
    mock_service.get_due_watches.return_value = []

    mock_session = AsyncMock()

    with (
        patch(
            "app.workers.db.get_worker_db",
            _mock_get_worker_db(mock_session),
        ),
        patch(
            "app.services.scheduled_scrape_service.ScheduledScrapeService",
            return_value=mock_service,
        ),
        patch("app.workers.tasks.scrape_single_trip") as mock_task,
    ):
        result = await _dispatch_due_scrapes_async()

    assert result["dispatched"] == 0
    assert result["watches_checked"] == 0
    mock_task.delay.assert_not_called()
    mock_service.mark_dispatched.assert_not_called()


async def test_dispatch_due_scrapes_marks_dispatched():
    """Dispatcher calls mark_dispatched for each watch after dispatching."""
    watch = _make_mock_watch()

    mock_service = AsyncMock()
    mock_service.get_due_watches.return_value = [watch]

    mock_session = AsyncMock()

    with (
        patch(
            "app.workers.db.get_worker_db",
            _mock_get_worker_db(mock_session),
        ),
        patch(
            "app.services.scheduled_scrape_service.ScheduledScrapeService",
            return_value=mock_service,
        ),
        patch("app.workers.tasks.scrape_single_trip"),
    ):
        await _dispatch_due_scrapes_async()

    mock_service.mark_dispatched.assert_called_once_with(watch)


# --- scrape_single_trip tests ---


async def test_scrape_single_trip_calls_service():
    """Single trip task calls service with correct UUIDs."""
    trip_id = uuid.uuid4()
    user_id = uuid.uuid4()

    mock_service = AsyncMock()
    mock_service.scrape_trip_background.return_value = 3

    mock_session = AsyncMock()

    with (
        patch(
            "app.workers.db.get_worker_db",
            _mock_get_worker_db(mock_session),
        ),
        patch(
            "app.services.scheduled_scrape_service.ScheduledScrapeService",
            return_value=mock_service,
        ),
    ):
        result = await _scrape_single_trip_async(str(trip_id), str(user_id))

    assert result["trip_id"] == str(trip_id)
    assert result["snapshots_stored"] == 3
    mock_service.scrape_trip_background.assert_called_once_with(
        trip_id, user_id, provider="google_flights"
    )


async def test_scrape_single_trip_passes_provider():
    """Single trip task passes custom provider to service."""
    trip_id = uuid.uuid4()
    user_id = uuid.uuid4()

    mock_service = AsyncMock()
    mock_service.scrape_trip_background.return_value = 1

    mock_session = AsyncMock()

    with (
        patch(
            "app.workers.db.get_worker_db",
            _mock_get_worker_db(mock_session),
        ),
        patch(
            "app.services.scheduled_scrape_service.ScheduledScrapeService",
            return_value=mock_service,
        ),
    ):
        result = await _scrape_single_trip_async(
            str(trip_id), str(user_id), provider="skyscanner"
        )

    assert result["snapshots_stored"] == 1
    mock_service.scrape_trip_background.assert_called_once_with(
        trip_id, user_id, provider="skyscanner"
    )


async def test_scrape_single_trip_invalid_uuid():
    """Single trip task raises ValueError for invalid UUID."""
    with pytest.raises(ValueError):
        await _scrape_single_trip_async("not-a-uuid", "also-not-a-uuid")


async def test_scrape_single_trip_zero_results():
    """Single trip task returns 0 when service finds nothing."""
    trip_id = uuid.uuid4()
    user_id = uuid.uuid4()

    mock_service = AsyncMock()
    mock_service.scrape_trip_background.return_value = 0

    mock_session = AsyncMock()

    with (
        patch(
            "app.workers.db.get_worker_db",
            _mock_get_worker_db(mock_session),
        ),
        patch(
            "app.services.scheduled_scrape_service.ScheduledScrapeService",
            return_value=mock_service,
        ),
    ):
        result = await _scrape_single_trip_async(str(trip_id), str(user_id))

    assert result["snapshots_stored"] == 0
