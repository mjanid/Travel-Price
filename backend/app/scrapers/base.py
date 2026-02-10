"""Abstract base scraper with retry logic, rate limiting, and proxy rotation."""

from __future__ import annotations

import asyncio
import itertools
import logging
import random
from abc import ABC, abstractmethod

import httpx

from app.scrapers.types import PriceResult, ScrapeError, ScrapeQuery

logger = logging.getLogger(__name__)

_USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:121.0) Gecko/20100101 Firefox/121.0",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.2 Safari/605.1.15",
]


class BaseScraper(ABC):
    """Abstract base class for all scrapers.

    Subclasses must set ``provider_name`` and implement ``scrape()``.
    The public entry point is ``execute()`` which wraps ``scrape()``
    with rate limiting and exponential-backoff retries.

    Args:
        redis_client: Optional async Redis client for rate limiting.
            If None, rate limiting is skipped.
        proxies: Optional list of proxy URLs for rotation.
        max_retries: Maximum retry attempts on failure.
        base_delay: Base delay in seconds for exponential backoff.
        rate_limit_requests: Max requests allowed per window.
        rate_limit_window: Rate limit window in seconds.
        timeout: HTTP request timeout in seconds.
    """

    provider_name: str = ""
    max_retries: int = 3
    base_delay: float = 1.0
    rate_limit_requests: int = 10
    rate_limit_window: int = 60
    timeout: float = 30.0

    def __init__(
        self,
        redis_client: object | None = None,
        proxies: list[str] | None = None,
        max_retries: int | None = None,
        base_delay: float | None = None,
        rate_limit_requests: int | None = None,
        rate_limit_window: int | None = None,
        timeout: float | None = None,
    ) -> None:
        self._redis = redis_client
        self._proxies = proxies or []
        self._proxy_cycle = itertools.cycle(self._proxies) if self._proxies else None

        if max_retries is not None:
            self.max_retries = max_retries
        if base_delay is not None:
            self.base_delay = base_delay
        if rate_limit_requests is not None:
            self.rate_limit_requests = rate_limit_requests
        if rate_limit_window is not None:
            self.rate_limit_window = rate_limit_window
        if timeout is not None:
            self.timeout = timeout

    @abstractmethod
    async def scrape(self, query: ScrapeQuery) -> list[PriceResult]:
        """Execute a scrape for the given query.

        Subclasses implement this method with provider-specific logic.

        Args:
            query: The scrape parameters.

        Returns:
            List of price results from the provider.
        """

    async def execute(self, query: ScrapeQuery) -> list[PriceResult]:
        """Public entry point: rate-limit check then retry loop around scrape().

        Args:
            query: The scrape parameters.

        Returns:
            List of price results.

        Raises:
            ScrapeError: If all retries are exhausted.
        """
        await self._check_rate_limit()
        return await self._retry_with_backoff(query)

    async def _retry_with_backoff(self, query: ScrapeQuery) -> list[PriceResult]:
        """Call scrape() with exponential backoff on failure.

        Args:
            query: The scrape parameters.

        Returns:
            List of price results on success.

        Raises:
            ScrapeError: After max_retries failures.
        """
        last_error: Exception | None = None
        for attempt in range(self.max_retries + 1):
            try:
                results = await self.scrape(query)
                if attempt > 0:
                    logger.info(
                        "%s: succeeded on attempt %d", self.provider_name, attempt + 1
                    )
                return results
            except Exception as exc:
                last_error = exc
                if attempt < self.max_retries:
                    delay = min(self.base_delay * (2 ** attempt) + random.uniform(0, 0.5), 60.0)
                    logger.warning(
                        "%s: attempt %d failed (%s), retrying in %.1fs",
                        self.provider_name,
                        attempt + 1,
                        exc,
                        delay,
                    )
                    await asyncio.sleep(delay)

        raise ScrapeError(
            provider=self.provider_name,
            message=str(last_error),
            retries=self.max_retries,
        )

    async def _check_rate_limit(self) -> None:
        """Check Redis-based per-provider rate limit.

        Raises:
            ScrapeError: If rate limit is exceeded.
        """
        if self._redis is None:
            return

        key = f"scraper:rate_limit:{self.provider_name}"
        try:
            current = await self._redis.incr(key)
            if current == 1:
                await self._redis.expire(key, self.rate_limit_window)
            if current > self.rate_limit_requests:
                ttl = await self._redis.ttl(key)
                raise ScrapeError(
                    provider=self.provider_name,
                    message=f"Rate limit exceeded ({self.rate_limit_requests}/{self.rate_limit_window}s). Retry after {ttl}s.",
                )
        except ScrapeError:
            raise
        except Exception as exc:
            logger.warning(
                "%s: Redis rate limit check failed (%s), proceeding without limit",
                self.provider_name,
                exc,
            )

    def _get_proxy(self) -> str | None:
        """Return next proxy URL via round-robin rotation."""
        if self._proxy_cycle is None:
            return None
        return next(self._proxy_cycle)

    def _get_headers(self) -> dict[str, str]:
        """Return default HTTP headers with a random User-Agent."""
        return {
            "User-Agent": random.choice(_USER_AGENTS),
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
            "Accept-Language": "en-US,en;q=0.9",
        }

    def _build_client(self, **kwargs: object) -> httpx.AsyncClient:
        """Build an httpx.AsyncClient with optional proxy and timeout.

        Args:
            **kwargs: Extra keyword arguments forwarded to AsyncClient.

        Returns:
            Configured async HTTP client.
        """
        proxy = self._get_proxy()
        return httpx.AsyncClient(
            timeout=self.timeout,
            proxy=proxy,
            headers=self._get_headers(),
            follow_redirects=True,
            **kwargs,
        )
