"""Tests for GoogleFlightsScraper with mocked Playwright pages."""

from datetime import date
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from app.scrapers.flights.google_flights import GoogleFlightsScraper
from app.scrapers.types import ScrapeQuery


@pytest.fixture
def query():
    return ScrapeQuery(
        origin="JFK",
        destination="LAX",
        departure_date=date(2026, 6, 15),
        return_date=date(2026, 6, 22),
        travelers=1,
        cabin_class="economy",
    )


@pytest.fixture
def scraper():
    return GoogleFlightsScraper(max_retries=0)


# ── URL building tests (no browser needed) ──────────────────────


def test_build_url_round_trip(scraper, query):
    """URL contains origin, destination, both dates."""
    url = scraper._build_search_url(query)
    assert "JFK" in url
    assert "LAX" in url
    assert "2026-06-15" in url
    assert "2026-06-22" in url


def test_build_url_one_way(scraper):
    """URL omits return date for one-way trips."""
    q = ScrapeQuery(
        origin="SFO",
        destination="ORD",
        departure_date=date(2026, 8, 1),
        return_date=None,
        travelers=1,
    )
    url = scraper._build_search_url(q)
    assert "SFO" in url
    assert "ORD" in url
    assert "2026-08-01" in url


def test_build_url_includes_travelers(scraper):
    """URL includes tfa parameter when travelers > 1."""
    q = ScrapeQuery(
        origin="JFK",
        destination="LAX",
        departure_date=date(2026, 6, 15),
        travelers=3,
    )
    url = scraper._build_search_url(q)
    assert "tfa=3" in url


def test_build_url_omits_travelers_for_single(scraper):
    """URL omits tfa parameter when travelers is 1."""
    q = ScrapeQuery(
        origin="JFK",
        destination="LAX",
        departure_date=date(2026, 6, 15),
        travelers=1,
    )
    url = scraper._build_search_url(q)
    assert "tfa=" not in url


def test_build_url_includes_cabin_class(scraper):
    """URL includes tfc parameter for non-economy cabin classes."""
    q = ScrapeQuery(
        origin="JFK",
        destination="LAX",
        departure_date=date(2026, 6, 15),
        cabin_class="business",
    )
    url = scraper._build_search_url(q)
    assert "tfc=3" in url


def test_build_url_omits_cabin_for_economy(scraper):
    """URL omits tfc parameter for economy (default)."""
    q = ScrapeQuery(
        origin="JFK",
        destination="LAX",
        departure_date=date(2026, 6, 15),
        cabin_class="economy",
    )
    url = scraper._build_search_url(q)
    assert "tfc=" not in url


def test_build_url_both_travelers_and_cabin(scraper):
    """URL includes both tfa and tfc when both are non-default."""
    q = ScrapeQuery(
        origin="JFK",
        destination="LAX",
        departure_date=date(2026, 6, 15),
        return_date=date(2026, 6, 22),
        travelers=4,
        cabin_class="first",
    )
    url = scraper._build_search_url(q)
    assert "tfa=4" in url
    assert "tfc=4" in url


# ── scrape_page() tests with mocked Playwright page ─────────────


async def test_scrape_page_extracts_flight_results(scraper, query, mock_playwright_page):
    """scrape_page() extracts structured results from page.evaluate()."""
    mock_playwright_page.evaluate = AsyncMock(return_value=[
        {"price": "234", "airline": "Delta", "stops": 0, "departureTime": "7:10 AM", "arrivalTime": "10:30 AM"},
        {"price": "350", "airline": "United", "stops": 1, "departureTime": "9:00 AM", "arrivalTime": "2:15 PM"},
    ])

    results = await scraper.scrape_page(mock_playwright_page, query)

    assert len(results) == 2
    assert results[0].price == 23400
    assert results[0].airline == "Delta"
    assert results[0].stops == 0
    assert results[0].provider == "google_flights"
    assert results[1].price == 35000
    assert results[1].airline == "United"
    assert results[1].stops == 1


async def test_scrape_page_empty_results(scraper, query, mock_playwright_page):
    """scrape_page() returns empty list when no results."""
    mock_playwright_page.evaluate = AsyncMock(return_value=[])

    results = await scraper.scrape_page(mock_playwright_page, query)
    assert results == []


async def test_scrape_page_skips_invalid_prices(scraper, query, mock_playwright_page):
    """scrape_page() skips items with unparseable prices."""
    mock_playwright_page.evaluate = AsyncMock(return_value=[
        {"price": "abc", "airline": "Bad", "stops": None, "departureTime": None, "arrivalTime": None},
        {"price": "199", "airline": "Good", "stops": 0, "departureTime": None, "arrivalTime": None},
    ])

    results = await scraper.scrape_page(mock_playwright_page, query)
    assert len(results) == 1
    assert results[0].airline == "Good"
    assert results[0].price == 19900


async def test_scrape_page_navigates_to_correct_url(scraper, query, mock_playwright_page):
    """scrape_page() navigates to the correct Google Flights URL."""
    mock_playwright_page.evaluate = AsyncMock(return_value=[])

    await scraper.scrape_page(mock_playwright_page, query)

    mock_playwright_page.goto.assert_called_once()
    url = mock_playwright_page.goto.call_args[0][0]
    assert "google.com/travel/flights" in url
    assert "JFK" in url
    assert "LAX" in url


async def test_scrape_page_handles_comma_prices(scraper, query, mock_playwright_page):
    """scrape_page() handles prices with commas like '1,234'."""
    mock_playwright_page.evaluate = AsyncMock(return_value=[
        {"price": "1234", "airline": "Delta", "stops": 0, "departureTime": None, "arrivalTime": None},
    ])

    results = await scraper.scrape_page(mock_playwright_page, query)
    assert len(results) == 1
    assert results[0].price == 123400


async def test_scrape_page_handles_null_airline_and_stops(scraper, query, mock_playwright_page):
    """scrape_page() handles results with null airline/stops."""
    mock_playwright_page.evaluate = AsyncMock(return_value=[
        {"price": "200", "airline": None, "stops": None, "departureTime": None, "arrivalTime": None},
    ])

    results = await scraper.scrape_page(mock_playwright_page, query)
    assert len(results) == 1
    assert results[0].airline is None
    assert results[0].stops is None
    assert results[0].price == 20000


async def test_scrape_page_sets_cabin_class_from_query(scraper, mock_playwright_page):
    """scrape_page() sets cabin_class on results from the query."""
    q = ScrapeQuery(
        origin="JFK",
        destination="LAX",
        departure_date=date(2026, 6, 15),
        cabin_class="business",
    )
    mock_playwright_page.evaluate = AsyncMock(return_value=[
        {"price": "500", "airline": "Delta", "stops": 0, "departureTime": None, "arrivalTime": None},
    ])

    results = await scraper.scrape_page(mock_playwright_page, q)
    assert results[0].cabin_class == "business"


async def test_dismiss_consent_catches_timeout(scraper, mock_playwright_page):
    """Consent dismissal silently handles timeout/missing dialog."""
    # is_visible raises timeout — should not propagate
    locator_mock = MagicMock()
    first_mock = AsyncMock()
    first_mock.is_visible = AsyncMock(side_effect=Exception("Timeout"))
    locator_mock.first = first_mock
    mock_playwright_page.locator = MagicMock(return_value=locator_mock)

    # Should not raise
    await scraper._dismiss_consent(mock_playwright_page)


# ── Price parsing unit tests ────────────────────────────────────


def test_parse_price_text_integer(scraper):
    """Parses simple integer price."""
    assert scraper._parse_price_text("234") == 23400


def test_parse_price_text_with_dollar_sign(scraper):
    """Parses price with $ prefix."""
    assert scraper._parse_price_text("$234") == 23400


def test_parse_price_text_with_commas(scraper):
    """Parses price with commas."""
    assert scraper._parse_price_text("1,234") == 123400


def test_parse_price_text_decimal(scraper):
    """Parses price with decimal."""
    assert scraper._parse_price_text("234.50") == 23450


def test_parse_price_text_invalid(scraper):
    """Returns None for unparseable text."""
    assert scraper._parse_price_text("abc") is None


def test_parse_price_text_empty(scraper):
    """Returns None for empty string."""
    assert scraper._parse_price_text("") is None
