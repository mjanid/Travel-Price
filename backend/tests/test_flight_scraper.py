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
    assert "through" not in url


def test_build_url_includes_travelers(scraper):
    """URL includes passengers when travelers > 1."""
    q = ScrapeQuery(
        origin="JFK",
        destination="LAX",
        departure_date=date(2026, 6, 15),
        travelers=3,
    )
    url = scraper._build_search_url(q)
    assert "3+passengers" in url


def test_build_url_omits_travelers_for_single(scraper):
    """URL omits passengers when travelers is 1."""
    q = ScrapeQuery(
        origin="JFK",
        destination="LAX",
        departure_date=date(2026, 6, 15),
        travelers=1,
    )
    url = scraper._build_search_url(q)
    assert "passengers" not in url


def test_build_url_includes_currency_and_lang(scraper, query):
    """URL includes curr=USD and hl=en."""
    url = scraper._build_search_url(query)
    assert "curr=USD" in url
    assert "hl=en" in url


def test_build_url_uses_q_parameter(scraper, query):
    """URL uses q= query parameter format."""
    url = scraper._build_search_url(query)
    assert "?q=Flights+to+LAX+from+JFK" in url


# ── _parse_flight_text() unit tests ────────────────────────────


def test_parse_nonstop_flight(scraper):
    """Parses a nonstop flight card text correctly."""
    text = (
        "7:10\u202fAM\n\xa0–\xa0\n8:25\u202fAM\n"
        "Austrian\n1 hr 15 min\nVIE–BER\nNonstop\n"
        "221 kg CO2e\nAvg emissions\n$616\nround trip"
    )
    result = scraper._parse_flight_text(text)
    assert result is not None
    assert result["price_cents"] == 61600
    assert result["airline"] == "Austrian"
    assert result["stops"] == 0
    assert result["departure_time"] == "7:10\u202fAM"
    assert result["arrival_time"] == "8:25\u202fAM"
    assert result["duration"] == "1 hr 15 min"


def test_parse_flight_with_stops(scraper):
    """Parses a flight with 1 stop correctly."""
    text = (
        "1:55 PM\n\xa0–\xa0\n5:50 PM\n"
        "Austrian, Lufthansa\n3 hr 55 min\nVIE–BER\n1 stop\n"
        "1 hr 20 min FRA\n151 kg CO2e\n+113% emissions\n$293\nround trip"
    )
    result = scraper._parse_flight_text(text)
    assert result is not None
    assert result["price_cents"] == 29300
    assert result["airline"] == "Austrian, Lufthansa"
    assert result["stops"] == 1


def test_parse_flight_comma_price(scraper):
    """Parses a price with commas like $1,234."""
    text = (
        "7:10 AM\n\xa0–\xa0\n8:25 AM\n"
        "Delta\n5 hr 30 min\nJFK–LAX\nNonstop\n"
        "100 kg CO2e\nAvg emissions\n$1,234\nround trip"
    )
    result = scraper._parse_flight_text(text)
    assert result is not None
    assert result["price_cents"] == 123400


def test_parse_flight_combined_times_line(scraper):
    """Parses Format B where dep and arr times are on a single line.

    Google Flights sometimes renders the dep–arr range as a single
    line ``"3:05 PM\\xa0–\\xa04:20 PM"`` instead of putting the dash
    on its own line.
    """
    text = (
        "3:05\u202fPM\xa0–\xa04:20\u202fPM\n"
        "Austrian\n1 hr 15 min\nVIE–BER\nNonstop\n"
        "76 kg CO2e\n+7% emissions\n$315\nround trip"
    )
    result = scraper._parse_flight_text(text)
    assert result is not None
    assert result["price_cents"] == 31500
    assert result["airline"] == "Austrian"
    assert result["stops"] == 0
    assert result["departure_time"] == "3:05\u202fPM"
    assert result["arrival_time"] == "4:20\u202fPM"
    assert result["duration"] == "1 hr 15 min"


def test_parse_flight_combined_times_with_stops(scraper):
    """Format B with stops — dep and arr on one line, 1 stop."""
    text = (
        "6:00\u202fAM\xa0–\xa012:45\u202fPM\n"
        "Condor\n5 hr 45 min\nVIE–BER\n1 stop\n"
        "2 hr FRA\n200 kg CO2e\n+50% emissions\n$285\nround trip"
    )
    result = scraper._parse_flight_text(text)
    assert result is not None
    assert result["price_cents"] == 28500
    assert result["airline"] == "Condor"
    assert result["stops"] == 1
    assert result["departure_time"] == "6:00\u202fAM"
    assert result["arrival_time"] == "12:45\u202fPM"
    assert result["duration"] == "5 hr 45 min"


def test_parse_flight_no_price(scraper):
    """Returns None when text has no price."""
    text = "Some random text\nwithout a price"
    assert scraper._parse_flight_text(text) is None


def test_parse_flight_too_few_lines(scraper):
    """Returns None when text has too few lines."""
    text = "$200\nshort"
    assert scraper._parse_flight_text(text) is None


# ── scrape_page() tests with mocked Playwright page ─────────────


async def test_scrape_page_extracts_flight_results(scraper, query, mock_playwright_page):
    """scrape_page() extracts structured results from page.evaluate()."""
    mock_playwright_page.evaluate = AsyncMock(return_value=[
        "7:10 AM\n\xa0–\xa0\n10:30 AM\nDelta\n5 hr 20 min\nJFK–LAX\nNonstop\n100 kg CO2e\nAvg emissions\n$234\nround trip",
        "9:00 AM\n\xa0–\xa0\n2:15 PM\nUnited\n5 hr 15 min\nJFK–LAX\n1 stop\n1 hr ORD\n150 kg CO2e\n+50% emissions\n$350\nround trip",
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


async def test_scrape_page_skips_invalid_entries(scraper, query, mock_playwright_page):
    """scrape_page() skips entries that can't be parsed."""
    mock_playwright_page.evaluate = AsyncMock(return_value=[
        "Some random junk",
        "7:10 AM\n\xa0–\xa0\n8:25 AM\nGood Airline\n1 hr\nJFK–LAX\nNonstop\n100 kg\nAvg\n$199\nround trip",
    ])

    results = await scraper.scrape_page(mock_playwright_page, query)
    assert len(results) == 1
    assert results[0].airline == "Good Airline"
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


async def test_scrape_page_sets_cabin_class_from_query(scraper, mock_playwright_page):
    """scrape_page() sets cabin_class on results from the query."""
    q = ScrapeQuery(
        origin="JFK",
        destination="LAX",
        departure_date=date(2026, 6, 15),
        cabin_class="business",
    )
    mock_playwright_page.evaluate = AsyncMock(return_value=[
        "7:10 AM\n\xa0–\xa0\n8:25 AM\nDelta\n5 hr\nJFK–LAX\nNonstop\n100 kg\nAvg\n$500\nround trip",
    ])

    results = await scraper.scrape_page(mock_playwright_page, q)
    assert results[0].cabin_class == "business"


async def test_scrape_page_stores_raw_data(scraper, query, mock_playwright_page):
    """scrape_page() stores departure/arrival times in raw_data."""
    mock_playwright_page.evaluate = AsyncMock(return_value=[
        "7:10 AM\n\xa0–\xa0\n10:30 AM\nDelta\n5 hr 20 min\nJFK–LAX\nNonstop\n100 kg CO2e\nAvg\n$234\nround trip",
    ])

    results = await scraper.scrape_page(mock_playwright_page, query)
    assert results[0].raw_data["departure_time"] == "7:10 AM"
    assert results[0].raw_data["arrival_time"] == "10:30 AM"
    assert results[0].raw_data["duration"] == "5 hr 20 min"


async def test_dismiss_consent_no_consent_frame(scraper, mock_playwright_page):
    """Consent dismissal does nothing when no consent frame present."""
    # frames only has main page frame (no consent.google.com)
    await scraper._dismiss_consent(mock_playwright_page)
    # Should complete without error


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
