"""Abstract base scraper using Playwright for JS-rendered pages."""

from __future__ import annotations

import asyncio
import logging
import random
from abc import abstractmethod
from contextlib import asynccontextmanager

from playwright.async_api import Browser, BrowserContext, Page, async_playwright

from app.scrapers.base import BaseScraper, _USER_AGENTS
from app.scrapers.types import PriceResult, ScrapeQuery

logger = logging.getLogger(__name__)


class _BrowserPool:
    """Singleton async browser pool for Playwright.

    Lazily launches a single Chromium instance and provides
    BrowserContext instances for individual scrape operations.
    Contexts are isolated (separate cookies/storage) and disposed after use.
    """

    _instance: _BrowserPool | None = None
    _lock: asyncio.Lock = asyncio.Lock()

    def __init__(self) -> None:
        self._playwright = None
        self._browser: Browser | None = None

    @classmethod
    async def get_instance(cls) -> _BrowserPool:
        """Return the singleton browser pool, creating it if needed."""
        if cls._instance is None:
            async with cls._lock:
                if cls._instance is None:
                    cls._instance = cls()
        return cls._instance

    async def _ensure_browser(self) -> Browser:
        """Launch Chromium if not already running or if disconnected."""
        if self._browser is None or not self._browser.is_connected():
            pw = await async_playwright().start()
            self._playwright = pw
            self._browser = await pw.chromium.launch(
                headless=True,
                args=[
                    "--no-sandbox",
                    "--disable-setuid-sandbox",
                    "--disable-dev-shm-usage",
                    "--disable-gpu",
                ],
            )
        return self._browser

    @asynccontextmanager
    async def context(self, user_agent: str | None = None):
        """Yield an isolated BrowserContext, auto-disposed on exit.

        Args:
            user_agent: Optional User-Agent string override.

        Yields:
            An isolated Playwright BrowserContext.
        """
        browser = await self._ensure_browser()
        ctx: BrowserContext = await browser.new_context(
            user_agent=user_agent or random.choice(_USER_AGENTS),
            viewport={"width": 1280, "height": 800},
            locale="en-US",
            timezone_id="America/New_York",
        )
        try:
            yield ctx
        finally:
            await ctx.close()

    async def close(self) -> None:
        """Shut down the browser and Playwright instance."""
        if self._browser:
            await self._browser.close()
            self._browser = None
        if self._playwright:
            await self._playwright.stop()
            self._playwright = None

    @classmethod
    async def reset(cls) -> None:
        """Close and discard the singleton instance.

        Used during shutdown and in tests.
        """
        if cls._instance is not None:
            await cls._instance.close()
            cls._instance = None


class PlaywrightBaseScraper(BaseScraper):
    """Base class for scrapers that need JavaScript rendering.

    Subclasses implement ``scrape_page(page, query)`` instead of
    ``scrape(query)``.  The Playwright browser lifecycle is handled
    automatically.

    Attributes:
        page_timeout: Default timeout in milliseconds for Playwright
            page operations (navigation, selectors, etc.).
    """

    page_timeout: float = 60_000  # milliseconds

    @abstractmethod
    async def scrape_page(
        self, page: Page, query: ScrapeQuery
    ) -> list[PriceResult]:
        """Scrape results from a loaded Playwright page.

        Args:
            page: The Playwright Page with content loaded.
            query: The scrape parameters.

        Returns:
            List of price results extracted from the page.
        """

    async def scrape(self, query: ScrapeQuery) -> list[PriceResult]:
        """Launch browser context, navigate, and delegate to scrape_page().

        This method is called by BaseScraper.execute() which handles
        retries and rate limiting.

        Args:
            query: The scrape parameters.

        Returns:
            List of price results.
        """
        pool = await _BrowserPool.get_instance()
        async with pool.context(user_agent=random.choice(_USER_AGENTS)) as ctx:
            page = await ctx.new_page()
            page.set_default_timeout(self.page_timeout)
            try:
                results = await self.scrape_page(page, query)
            finally:
                await page.close()
        return results
