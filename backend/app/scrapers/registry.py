"""Scraper registry mapping provider names to scraper classes."""

from __future__ import annotations

from app.scrapers.base import BaseScraper
from app.scrapers.flights.google_flights import GoogleFlightsScraper

SCRAPER_REGISTRY: dict[str, type[BaseScraper]] = {
    "google_flights": GoogleFlightsScraper,
}


def get_scraper(
    provider: str,
    redis_client: object | None = None,
    proxies: list[str] | None = None,
    **kwargs: object,
) -> BaseScraper:
    """Instantiate a scraper by provider name.

    Args:
        provider: Provider identifier (must exist in SCRAPER_REGISTRY).
        redis_client: Optional async Redis client for rate limiting.
        proxies: Optional proxy URL list for rotation.
        **kwargs: Extra arguments forwarded to the scraper constructor.

    Returns:
        An instantiated scraper.

    Raises:
        ValueError: If the provider is not registered.
    """
    scraper_cls = SCRAPER_REGISTRY.get(provider)
    if scraper_cls is None:
        available = ", ".join(sorted(SCRAPER_REGISTRY.keys()))
        raise ValueError(
            f"Unknown scraper provider '{provider}'. Available: {available}"
        )
    return scraper_cls(redis_client=redis_client, proxies=proxies, **kwargs)
