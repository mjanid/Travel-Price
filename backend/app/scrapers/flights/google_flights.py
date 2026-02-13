"""Google Flights scraper using Playwright for JS-rendered pages.

Google Flights is a JavaScript SPA — the HTML returned without JS
rendering contains no flight data.  This scraper uses Playwright to
launch headless Chromium, navigate to Google Flights, wait for results
to render, and extract flight data from the live DOM.
"""

from __future__ import annotations

import asyncio
import logging
import re
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

    async def scrape_page(
        self, page: Page, query: ScrapeQuery
    ) -> list[PriceResult]:
        """Navigate to Google Flights and extract rendered results."""
        url = self._build_search_url(query)
        logger.info("%s: navigating to %s", self.provider_name, url)
        await page.goto(url, wait_until="domcontentloaded")

        # Dismiss cookie consent dialog (lives in an iframe)
        await self._dismiss_consent(page)

        # Wait for flight results to render
        await self._wait_for_results(page)

        # Extract results from the rendered DOM
        return await self._extract_results(page, query)

    def _build_search_url(self, query: ScrapeQuery) -> str:
        """Build the Google Flights search URL using the q= query format.

        Uses the natural-language query parameter that Google Flights
        supports, e.g. ``?q=Flights+to+BER+from+VIE+on+2026-03-27``.
        This avoids the need to generate protobuf-encoded ``tfs``
        parameters.
        """
        dep = query.departure_date.strftime("%Y-%m-%d")
        q = f"Flights to {query.destination} from {query.origin} on {dep}"
        if query.return_date:
            ret = query.return_date.strftime("%Y-%m-%d")
            q += f" through {ret}"
        if query.travelers and query.travelers > 1:
            q += f" {query.travelers} passengers"

        params = f"?q={q.replace(' ', '+')}&curr=USD&hl=en"
        return f"{_GOOGLE_FLIGHTS_URL}{params}"

    async def _dismiss_consent(self, page: Page) -> None:
        """Dismiss Google cookie consent dialog if it appears.

        The consent dialog is rendered inside an iframe from
        ``consent.google.com``. We locate the frame and click the
        reject/accept button inside it.
        """
        try:
            for frame in page.frames:
                if "consent.google.com" not in frame.url:
                    continue
                for label in ("Reject all", "Accept all"):
                    btns = await frame.query_selector_all("button")
                    for btn in btns:
                        text = (await btn.inner_text()).strip()
                        if label in text:
                            await btn.click()
                            logger.debug(
                                "%s: dismissed consent with '%s'",
                                self.provider_name,
                                label,
                            )
                            await asyncio.sleep(2)
                            return
        except Exception:
            pass

    async def _wait_for_results(self, page: Page) -> None:
        """Wait for flight result cards to render on the page."""
        try:
            await page.wait_for_selector(
                "li.pIav2d", timeout=15_000
            )
            return
        except Exception:
            pass

        # Fallback: wait for any price-like text to appear
        try:
            await page.wait_for_function(
                r"() => document.body.innerText.match(/\$\d+/)",
                timeout=10_000,
            )
        except Exception:
            logger.warning(
                "%s: no flight results detected after waiting",
                self.provider_name,
            )

    async def _extract_results(
        self, page: Page, query: ScrapeQuery
    ) -> list[PriceResult]:
        """Extract flight results from the rendered DOM.

        Google Flights renders each flight as an ``li.pIav2d`` element.
        The inner text follows a consistent line-based structure:

        Nonstop flights::

            departure_time | – | arrival_time | airline | duration |
            route | Nonstop | emissions | emissions_label | price |
            trip_type

        Flights with stops::

            departure_time | – | arrival_time | airline | duration |
            route | N stop(s) | layover_info | emissions | emissions_label |
            price | trip_type
        """
        now = datetime.now(timezone.utc)

        raw_results = await page.evaluate(r"""
            () => {
                const items = document.querySelectorAll('li.pIav2d');
                const flights = [];
                for (const item of items) {
                    const text = (item.innerText || '').trim();
                    if (!text) continue;
                    flights.push(text);
                }
                return flights;
            }
        """)

        results: list[PriceResult] = []
        for text in raw_results:
            parsed = self._parse_flight_text(text)
            if parsed is None:
                continue

            results.append(
                PriceResult(
                    provider=self.provider_name,
                    price=parsed["price_cents"],
                    currency="USD",
                    cabin_class=query.cabin_class,
                    airline=parsed.get("airline"),
                    stops=parsed.get("stops"),
                    raw_data={
                        "departure_time": parsed.get("departure_time"),
                        "arrival_time": parsed.get("arrival_time"),
                        "duration": parsed.get("duration"),
                        "text": text,
                    },
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

    def _parse_flight_text(self, text: str) -> dict | None:
        """Parse the inner text of a single flight card.

        Returns a dict with keys: price_cents, airline, stops,
        departure_time, arrival_time, duration.  Returns None if the
        text cannot be parsed.

        Handles two Google Flights DOM formats:

        **Format A** — departure and arrival on separate lines (dash
        filtered out)::

            "7:10 AM"  →  line 0 (departure)
            "8:25 AM"  →  line 1 (arrival)
            "Austrian" →  line 2 (airline)
            "1 hr 15 min" → line 3 (duration)

        **Format B** — departure and arrival on a single line joined
        by ``\\xa0–\\xa0`` or `` – ``::

            "3:05 PM\\xa0–\\xa04:20 PM"  →  line 0 (dep + arr)
            "Austrian"                    →  line 1 (airline)
            "1 hr 15 min"                 →  line 2 (duration)
        """
        lines = [
            line.strip()
            for line in text.split("\n")
            if line.strip()
            and line.strip() not in ("\xa0–\xa0", "–", "\u2013", "-")
        ]

        if len(lines) < 5:
            return None

        # Extract price — look for $NNN pattern anywhere in lines
        price_cents = None
        for line in lines:
            m = re.match(r"^\$(\d[\d,]*)", line)
            if m:
                price_cents = int(m.group(1).replace(",", "")) * 100
                break

        if price_cents is None:
            return None

        # Detect Format B: first line contains both dep and arr times
        # joined by \xa0–\xa0 or " – " (e.g. "3:05 PM\xa0–\xa04:20 PM")
        _dash_sep = re.compile(r"\xa0–\xa0|\xa0\u2013\xa0|\s–\s|\s\u2013\s")
        if _dash_sep.search(lines[0]):
            # Format B: split combined dep–arr line
            parts = _dash_sep.split(lines[0], maxsplit=1)
            departure_time = parts[0].strip()
            arrival_time = parts[1].strip() if len(parts) > 1 else None
            # Remaining lines shift up by one
            airline = lines[1] if len(lines) > 1 else None
            duration = lines[2] if len(lines) > 2 else None
        else:
            # Format A: dep and arr on separate lines
            departure_time = (
                lines[0] if re.search(r"\d{1,2}:\d{2}", lines[0]) else None
            )
            arrival_time = (
                lines[1] if re.search(r"\d{1,2}:\d{2}", lines[1]) else None
            )
            airline = lines[2] if len(lines) > 2 else None
            duration = lines[3] if len(lines) > 3 else None

        # Stops: look for "Nonstop" or "N stop" pattern
        stops = None
        for line in lines:
            if line.lower() == "nonstop":
                stops = 0
                break
            m = re.match(r"^(\d+)\s*stop", line, re.IGNORECASE)
            if m:
                stops = int(m.group(1))
                break

        return {
            "price_cents": price_cents,
            "airline": airline,
            "stops": stops,
            "departure_time": departure_time,
            "arrival_time": arrival_time,
            "duration": duration,
        }

    def _parse_price_text(self, text: str) -> int | None:
        """Parse a price text string like '234' into cents."""
        cleaned = text.replace("$", "").replace(",", "").strip()
        try:
            return int(float(cleaned) * 100)
        except (ValueError, TypeError):
            return None
