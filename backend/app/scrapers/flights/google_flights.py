"""Google Flights scraper using httpx + BeautifulSoup.

Google Flights is a JavaScript-heavy site, so full production scraping
would require Playwright (planned for Feature 5). This implementation
provides the correct structure and parsing logic, and works with the
httpx-based approach for testability with recorded/mocked responses.
"""

from __future__ import annotations

import json
import logging
from datetime import datetime, timezone

from bs4 import BeautifulSoup

from app.scrapers.base import BaseScraper
from app.scrapers.types import PriceResult, ScrapeQuery

logger = logging.getLogger(__name__)

_GOOGLE_FLIGHTS_URL = "https://www.google.com/travel/flights"


class GoogleFlightsScraper(BaseScraper):
    """Scraper for Google Flights search results.

    Builds a Google Flights search URL from the query parameters,
    fetches the page, and parses flight results from the HTML.
    """

    provider_name = "google_flights"

    async def scrape(self, query: ScrapeQuery) -> list[PriceResult]:
        """Fetch and parse flight prices from Google Flights.

        Args:
            query: The scrape parameters with origin/destination/dates.

        Returns:
            List of PriceResult with parsed flight data.

        Raises:
            Exception: On HTTP errors or parsing failures (handled by
                retry logic in BaseScraper).
        """
        url = self._build_search_url(query)
        async with self._build_client() as client:
            response = await client.get(url)
            response.raise_for_status()

        return self._parse_results(response.text, query)

    def _build_search_url(self, query: ScrapeQuery) -> str:
        """Build the Google Flights search URL.

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
        return f"{_GOOGLE_FLIGHTS_URL}{params}"

    def _parse_results(
        self, html: str, query: ScrapeQuery
    ) -> list[PriceResult]:
        """Parse flight results from HTML content.

        Extracts flight data from structured elements in the page.
        Falls back to meta/script tag parsing if primary selectors fail.

        Args:
            html: Raw HTML response body.
            query: Original scrape parameters for context.

        Returns:
            List of parsed PriceResult objects.
        """
        soup = BeautifulSoup(html, "lxml")
        results: list[PriceResult] = []
        now = datetime.now(timezone.utc)

        # Try structured data (JSON-LD) first
        for script in soup.find_all("script", type="application/ld+json"):
            try:
                data = json.loads(script.string or "")
                if isinstance(data, list):
                    for item in data:
                        result = self._parse_json_ld_offer(item, now)
                        if result:
                            results.append(result)
                elif isinstance(data, dict):
                    result = self._parse_json_ld_offer(data, now)
                    if result:
                        results.append(result)
            except (json.JSONDecodeError, KeyError):
                continue

        # Fallback: parse flight result cards by common CSS patterns
        if not results:
            results = self._parse_flight_cards(soup, query, now)

        return results

    def _parse_json_ld_offer(
        self, data: dict, scraped_at: datetime
    ) -> PriceResult | None:
        """Attempt to parse a JSON-LD offer into a PriceResult.

        Args:
            data: Parsed JSON-LD data dict.
            scraped_at: Timestamp for when this was scraped.

        Returns:
            PriceResult if the data represents a flight offer, else None.
        """
        if data.get("@type") not in ("Offer", "Flight", "FlightReservation"):
            return None

        price_value = data.get("price") or data.get("totalPrice")
        if price_value is None:
            offers = data.get("offers", [])
            if offers and isinstance(offers, list):
                price_value = offers[0].get("price")
        if price_value is None:
            return None

        try:
            price_cents = int(float(price_value) * 100)
        except (ValueError, TypeError):
            return None

        currency = (
            data.get("priceCurrency")
            or data.get("currency")
            or "USD"
        )

        return PriceResult(
            provider=self.provider_name,
            price=price_cents,
            currency=currency,
            cabin_class=data.get("cabinClass"),
            airline=data.get("airline", {}).get("name") if isinstance(data.get("airline"), dict) else data.get("airline"),
            stops=None,
            raw_data=data,
            scraped_at=scraped_at,
        )

    def _parse_flight_cards(
        self, soup: BeautifulSoup, query: ScrapeQuery, scraped_at: datetime
    ) -> list[PriceResult]:
        """Parse flight results from HTML card elements.

        Uses common patterns found in Google Flights HTML structure.

        Args:
            soup: Parsed BeautifulSoup document.
            query: Original scrape query for context.
            scraped_at: Timestamp for when this was scraped.

        Returns:
            List of PriceResult parsed from card elements.
        """
        results: list[PriceResult] = []

        # Google Flights uses li elements with role="listitem" for results
        cards = soup.select("[role='listitem']")
        if not cards:
            # Fallback: look for divs with price-like content
            cards = soup.find_all("div", attrs={"data-price": True})

        for card in cards:
            price_text = card.get("data-price") or self._extract_price_text(card)
            if not price_text:
                continue

            price_cents = self._parse_price_text(price_text)
            if price_cents is None:
                continue

            airline_el = card.find(attrs={"data-airline": True}) or card.find(
                class_=lambda c: c and "airline" in c.lower() if c else False
            )
            airline = None
            if airline_el:
                airline = airline_el.get("data-airline") or airline_el.get_text(strip=True)

            stops_text = card.find(
                string=lambda t: t and ("stop" in t.lower() or "nonstop" in t.lower()) if t else False
            )
            stops = None
            if stops_text:
                text = stops_text.strip().lower()
                if "nonstop" in text or "direct" in text:
                    stops = 0
                else:
                    try:
                        stops = int("".join(c for c in text if c.isdigit()) or "0")
                    except ValueError:
                        pass

            results.append(
                PriceResult(
                    provider=self.provider_name,
                    price=price_cents,
                    currency="USD",
                    cabin_class=query.cabin_class,
                    airline=airline,
                    stops=stops,
                    raw_data={"html_snippet": str(card)[:500]},
                    scraped_at=scraped_at,
                )
            )

        return results

    def _extract_price_text(self, element: object) -> str | None:
        """Extract a price string from an element's text content.

        Args:
            element: A BeautifulSoup element.

        Returns:
            Price text string or None if not found.
        """
        text = element.get_text(" ", strip=True)
        # Look for $XXX pattern
        for word in text.split():
            if word.startswith("$"):
                return word
        return None

    def _parse_price_text(self, text: str) -> int | None:
        """Parse a price text string like '$234' or '234.50' into cents.

        Args:
            text: Price string to parse.

        Returns:
            Price in cents or None if unparseable.
        """
        cleaned = text.replace("$", "").replace(",", "").strip()
        try:
            return int(float(cleaned) * 100)
        except (ValueError, TypeError):
            return None
