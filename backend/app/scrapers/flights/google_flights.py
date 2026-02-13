"""Google Flights scraper using Playwright for JS-rendered pages.

Google Flights is a JavaScript SPA — the HTML returned without JS
rendering contains no flight data.  This scraper uses Playwright to
launch headless Chromium, navigate to Google Flights, wait for results
to render, and extract flight data from the live DOM.
"""

from __future__ import annotations

import asyncio
import logging
from datetime import datetime, timezone

from playwright.async_api import Page

from app.scrapers.playwright_base import PlaywrightBaseScraper
from app.scrapers.types import PriceResult, ScrapeQuery

logger = logging.getLogger(__name__)

_GOOGLE_FLIGHTS_URL = "https://www.google.com/travel/flights"


class GoogleFlightsScraper(PlaywrightBaseScraper):
    """Scraper for Google Flights search results.

    Navigates to a Google Flights search URL via Playwright, waits for
    JS-rendered flight result cards, and extracts price / airline /
    stops / time data from the live DOM.
    """

    provider_name = "google_flights"
    page_timeout = 45_000  # Google Flights can be slow

    # Maps ScrapeQuery cabin_class values to Google Flights tfc parameter values.
    _CABIN_CLASS_MAP: dict[str, int] = {
        "economy": 1,
        "premium_economy": 2,
        "business": 3,
        "first": 4,
    }

    async def scrape_page(
        self, page: Page, query: ScrapeQuery
    ) -> list[PriceResult]:
        """Navigate to Google Flights and extract rendered results.

        Args:
            page: The Playwright Page (provided by PlaywrightBaseScraper).
            query: The scrape parameters with origin/destination/dates.

        Returns:
            List of PriceResult with parsed flight data.
        """
        url = self._build_search_url(query)
        await page.goto(url, wait_until="domcontentloaded")

        # Dismiss cookie consent dialog if present
        await self._dismiss_consent(page)

        # Wait for flight results to render
        await self._wait_for_results(page)

        # Extract results from the rendered DOM
        return await self._extract_results(page, query)

    def _build_search_url(self, query: ScrapeQuery) -> str:
        """Build the Google Flights search URL.

        Encodes origin, destination, dates, travelers, and cabin class
        so that fetched prices match the requested trip details.

        Args:
            query: The scrape parameters.

        Returns:
            The full search URL string.
        """
        dep = query.departure_date.strftime("%Y-%m-%d")
        params = f"?hl=en&curr=USD&tfs={query.origin}-{query.destination}-{dep}"
        if query.return_date:
            ret = query.return_date.strftime("%Y-%m-%d")
            params += f"-{ret}"
        if query.travelers and query.travelers > 1:
            params += f"&tfa={query.travelers}"
        cabin_code = self._CABIN_CLASS_MAP.get(query.cabin_class)
        if cabin_code and cabin_code != 1:
            params += f"&tfc={cabin_code}"
        return f"{_GOOGLE_FLIGHTS_URL}{params}"

    async def _dismiss_consent(self, page: Page) -> None:
        """Dismiss Google cookie consent dialog if it appears.

        Args:
            page: The Playwright Page.
        """
        try:
            # Google consent dialog buttons — try common selectors
            for selector in [
                "button:has-text('Reject all')",
                "button:has-text('Accept all')",
                "[aria-label='Reject all']",
                "[aria-label='Accept all']",
            ]:
                btn = page.locator(selector).first
                if await btn.is_visible(timeout=2000):
                    await btn.click()
                    await asyncio.sleep(0.5)
                    return
        except Exception:
            # Consent dialog didn't appear or selector failed — continue
            pass

    async def _wait_for_results(self, page: Page) -> None:
        """Wait for flight result cards to render on the page.

        Tries multiple selector strategies since Google Flights DOM
        changes frequently.

        Args:
            page: The Playwright Page.
        """
        selectors = [
            "[role='listitem']",
            "li[data-resultid]",
            "[data-price]",
        ]
        for selector in selectors:
            try:
                await page.wait_for_selector(selector, timeout=15_000)
                return
            except Exception:
                continue

        # Final fallback: wait for any price-like text to appear
        try:
            await page.wait_for_function(
                "() => document.body.innerText.match(/\\$\\d+/)",
                timeout=10_000,
            )
        except Exception:
            logger.warning(
                "%s: no flight results detected after waiting", self.provider_name
            )

    async def _extract_results(
        self, page: Page, query: ScrapeQuery
    ) -> list[PriceResult]:
        """Extract flight results from the rendered DOM.

        Uses page.evaluate() to run JS in the browser context and
        return structured flight data.

        Args:
            page: The Playwright Page with rendered results.
            query: Original scrape parameters for context.

        Returns:
            List of PriceResult parsed from the page.
        """
        now = datetime.now(timezone.utc)

        # Extract data from the page via JS evaluation
        raw_results = await page.evaluate("""
            () => {
                const results = [];

                // Strategy 1: listitem elements (most common Google Flights structure)
                const items = document.querySelectorAll("[role='listitem']");
                for (const item of items) {
                    const text = item.innerText || '';

                    // Extract price — look for $XXX pattern
                    const priceMatch = text.match(/\\$(\\d[\\d,]*)/);
                    if (!priceMatch) continue;

                    const price = priceMatch[1].replace(/,/g, '');

                    // Extract airline — usually first line or prominent text
                    const lines = text.split('\\n').map(l => l.trim()).filter(Boolean);
                    let airline = null;
                    for (const line of lines) {
                        // Airline names are typically short text without $ or time patterns
                        if (line.length > 2 && line.length < 40
                            && !line.startsWith('$')
                            && !line.match(/^\\d{1,2}:\\d{2}/)
                            && !line.match(/stop/i)
                            && !line.match(/^\\d+ hr/i)
                            && !line.match(/^\\d+h/i)) {
                            airline = line;
                            break;
                        }
                    }

                    // Extract stops
                    let stops = null;
                    const stopsMatch = text.match(/Nonstop|Direct|(\\d+)\\s*stop/i);
                    if (stopsMatch) {
                        if (stopsMatch[0].toLowerCase().includes('nonstop')
                            || stopsMatch[0].toLowerCase().includes('direct')) {
                            stops = 0;
                        } else {
                            stops = parseInt(stopsMatch[1], 10);
                        }
                    }

                    // Extract departure time (HH:MM AM/PM pattern)
                    let departureTime = null;
                    let arrivalTime = null;
                    const timeMatches = text.match(
                        /\\d{1,2}:\\d{2}\\s*(?:AM|PM)/gi
                    );
                    if (timeMatches && timeMatches.length >= 1) {
                        departureTime = timeMatches[0];
                    }
                    if (timeMatches && timeMatches.length >= 2) {
                        arrivalTime = timeMatches[1];
                    }

                    results.push({
                        price: price,
                        airline: airline,
                        stops: stops,
                        departureTime: departureTime,
                        arrivalTime: arrivalTime,
                    });
                }

                // Strategy 2: data-price attributes (fallback)
                if (results.length === 0) {
                    const priceEls = document.querySelectorAll('[data-price]');
                    for (const el of priceEls) {
                        const priceAttr = el.getAttribute('data-price');
                        if (priceAttr) {
                            results.push({
                                price: priceAttr.replace(/[$,]/g, ''),
                                airline: null,
                                stops: null,
                                departureTime: null,
                                arrivalTime: null,
                            });
                        }
                    }
                }

                return results;
            }
        """)

        results: list[PriceResult] = []
        for item in raw_results:
            price_cents = self._parse_price_text(str(item.get("price", "")))
            if price_cents is None:
                continue

            results.append(
                PriceResult(
                    provider=self.provider_name,
                    price=price_cents,
                    currency="USD",
                    cabin_class=query.cabin_class,
                    airline=item.get("airline"),
                    stops=item.get("stops"),
                    raw_data=item,
                    scraped_at=now,
                )
            )

        if not results:
            logger.warning(
                "%s: page loaded but no results extracted for %s -> %s",
                self.provider_name,
                query.origin,
                query.destination,
            )

        return results

    def _parse_price_text(self, text: str) -> int | None:
        """Parse a price text string like '234' or '234.50' into cents.

        Args:
            text: Price string to parse (already stripped of $ and commas
                by the JS extraction).

        Returns:
            Price in cents or None if unparseable.
        """
        cleaned = text.replace("$", "").replace(",", "").strip()
        try:
            return int(float(cleaned) * 100)
        except (ValueError, TypeError):
            return None
