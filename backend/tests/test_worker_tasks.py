"""Tests for Celery worker tasks."""

import uuid
from contextlib import asynccontextmanager
from unittest.mock import AsyncMock, patch

import pytest

from app.workers.tasks import (
    _scrape_all_active_trips_async,
    _scrape_single_trip_async,
)


def _mock_get_worker_db(mock_session):
    """Create a mock get_worker_db context manager."""

    @asynccontextmanager
    async def _get_worker_db():
        yield mock_session

    return _get_worker_db


# --- scrape_all_active_trips tests ---


async def test_scrape_all_active_trips_dispatches_tasks():
    """Fan-out task dispatches one scrape_single_trip per active trip."""
    trip1_id = uuid.uuid4()
    trip2_id = uuid.uuid4()
    user1_id = uuid.uuid4()
    user2_id = uuid.uuid4()

    mock_service = AsyncMock()
    mock_service.get_active_trip_ids.return_value = [
        (trip1_id, user1_id),
        (trip2_id, user2_id),
    ]

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
        result = await _scrape_all_active_trips_async()

    assert result["dispatched"] == 2
    assert result["trips"] == 2
    assert mock_task.delay.call_count == 2
    mock_task.delay.assert_any_call(str(trip1_id), str(user1_id))
    mock_task.delay.assert_any_call(str(trip2_id), str(user2_id))


async def test_scrape_all_active_trips_no_trips():
    """Fan-out task dispatches nothing when no active trips exist."""
    mock_service = AsyncMock()
    mock_service.get_active_trip_ids.return_value = []

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
        result = await _scrape_all_active_trips_async()

    assert result["dispatched"] == 0
    assert result["trips"] == 0
    mock_task.delay.assert_not_called()


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
    mock_service.scrape_trip_background.assert_called_once_with(trip_id, user_id)


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
