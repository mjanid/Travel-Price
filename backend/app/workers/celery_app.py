"""Celery application configuration."""

from celery import Celery

from app.core.config import get_settings

settings = get_settings()

celery_app = Celery(
    "travel_price_scraper",
    broker=settings.celery_broker_url,
    backend=settings.celery_result_backend,
)

celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,
    task_track_started=True,
    task_acks_late=True,
    worker_prefetch_multiplier=1,
    beat_schedule={
        "scrape-active-trips": {
            "task": "app.workers.tasks.scrape_all_active_trips",
            "schedule": settings.scrape_interval_minutes * 60,
        },
    },
)

celery_app.autodiscover_tasks(["app.workers"])
