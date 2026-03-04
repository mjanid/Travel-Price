"""Scraper registry mapping provider names to scraper classes."""

from __future__ import annotations

import logging

from app.scrapers.base import BaseScraper
from app.scrapers.playwright_base import PLAYWRIGHT_AVAILABLE

logger = logging.getLogger(__name__)

SCRAPER_REGISTRY: dict[str, type[BaseScraper]] = {}

# Always register static/httpx scrapers here:
# e.g. SCRAPER_REGISTRY["some_static_provider"] = SomeStaticScraper

# Only register Playwright scrapers if the dependency is available
if PLAYWRIGHT_AVAILABLE:
    from app.scrapers.flights.google_flights import GoogleFlightsScraper

    SCRAPER_REGISTRY["google_flights"] = GoogleFlightsScraper
else:
    logger.info(
        "Playwright is not installed — Playwright-based scrapers "
        "(google_flights) will not be available."
    )


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
        if available:
            raise ValueError(
                f"Unknown scraper provider '{provider}'. "
                f"Available: {available}"
            )
        raise ValueError(
            f"Provider '{provider}' is not available. "
            "It may require Playwright which is not installed "
            "in this environment."
        )
    return scraper_cls(redis_client=redis_client, proxies=proxies, **kwargs)
