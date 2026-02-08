"""Tests for Celery application configuration."""

from app.workers.celery_app import celery_app


def test_celery_app_has_correct_name():
    """Celery app is named 'travel_price_scraper'."""
    assert celery_app.main == "travel_price_scraper"


def test_celery_app_uses_json_serializer():
    """Tasks use JSON serialization."""
    assert celery_app.conf.task_serializer == "json"
    assert "json" in celery_app.conf.accept_content


def test_celery_app_uses_utc():
    """Celery is configured for UTC."""
    assert celery_app.conf.timezone == "UTC"
    assert celery_app.conf.enable_utc is True


def test_celery_beat_schedule_contains_scrape_task():
    """Beat schedule includes the scrape-active-trips entry."""
    assert "scrape-active-trips" in celery_app.conf.beat_schedule
    entry = celery_app.conf.beat_schedule["scrape-active-trips"]
    assert entry["task"] == "app.workers.tasks.scrape_all_active_trips"
    assert isinstance(entry["schedule"], (int, float))
    assert entry["schedule"] > 0


def test_celery_tasks_are_registered():
    """Both scrape tasks are discoverable."""
    # Force task module import so autodiscover picks them up
    import app.workers.tasks  # noqa: F401

    task_names = list(celery_app.tasks.keys())
    assert "app.workers.tasks.scrape_all_active_trips" in task_names
    assert "app.workers.tasks.scrape_single_trip" in task_names


def test_celery_task_acks_late():
    """Tasks acknowledge after completion (crash safety)."""
    assert celery_app.conf.task_acks_late is True
