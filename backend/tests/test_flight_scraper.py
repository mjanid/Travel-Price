"""Tests for GoogleFlightsScraper with mocked HTTP responses."""

import json
from datetime import date, datetime, timezone

import httpx
import pytest
import respx

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


def _json_ld_html(offers: list[dict]) -> str:
    """Build HTML with JSON-LD script tags for testing."""
    scripts = ""
    for offer in offers:
        scripts += f'<script type="application/ld+json">{json.dumps(offer)}</script>\n'
    return f"<html><head>{scripts}</head><body></body></html>"


def _card_html(cards: list[dict]) -> str:
    """Build HTML with flight card elements for testing."""
    items = ""
    for card in cards:
        price = card.get("price", "$250")
        airline = card.get("airline", "Test Air")
        stops = card.get("stops", "Nonstop")
        items += f'''
        <li role="listitem">
            <div data-airline="{airline}">{airline}</div>
            <span>${price}</span>
            <span>{stops}</span>
        </li>
        '''
    return f"<html><body><ul>{items}</ul></body></html>"


@respx.mock
async def test_parse_json_ld_single_offer(scraper, query):
    """Scraper parses a single JSON-LD Offer correctly."""
    html = _json_ld_html([
        {
            "@type": "Offer",
            "price": "234.50",
            "priceCurrency": "USD",
            "airline": {"name": "Delta"},
            "cabinClass": "economy",
        }
    ])
    respx.get(url__startswith="https://www.google.com/travel/flights").mock(
        return_value=httpx.Response(200, text=html)
    )

    results = await scraper.execute(query)
    assert len(results) == 1
    assert results[0].price == 23450
    assert results[0].currency == "USD"
    assert results[0].airline == "Delta"
    assert results[0].provider == "google_flights"


@respx.mock
async def test_parse_json_ld_multiple_offers(scraper, query):
    """Scraper parses multiple JSON-LD offers."""
    html = _json_ld_html([
        {"@type": "Offer", "price": "200", "priceCurrency": "USD"},
        {"@type": "Offer", "price": "350", "priceCurrency": "USD"},
    ])
    respx.get(url__startswith="https://www.google.com/travel/flights").mock(
        return_value=httpx.Response(200, text=html)
    )

    results = await scraper.execute(query)
    assert len(results) == 2
    assert results[0].price == 20000
    assert results[1].price == 35000


@respx.mock
async def test_parse_json_ld_list_format(scraper, query):
    """Scraper handles JSON-LD as a list."""
    offers = [
        {"@type": "Offer", "price": "150", "priceCurrency": "EUR"},
        {"@type": "Offer", "price": "180", "priceCurrency": "EUR"},
    ]
    html = f'<html><head><script type="application/ld+json">{json.dumps(offers)}</script></head><body></body></html>'
    respx.get(url__startswith="https://www.google.com/travel/flights").mock(
        return_value=httpx.Response(200, text=html)
    )

    results = await scraper.execute(query)
    assert len(results) == 2
    assert results[0].currency == "EUR"


@respx.mock
async def test_parse_flight_cards_fallback(scraper, query):
    """Scraper falls back to HTML card parsing when no JSON-LD."""
    html = _card_html([
        {"price": "299", "airline": "United", "stops": "1 stop"},
        {"price": "199", "airline": "JetBlue", "stops": "Nonstop"},
    ])
    respx.get(url__startswith="https://www.google.com/travel/flights").mock(
        return_value=httpx.Response(200, text=html)
    )

    results = await scraper.execute(query)
    assert len(results) == 2
    prices = sorted([r.price for r in results])
    assert prices == [19900, 29900]


@respx.mock
async def test_parse_nonstop_stops(scraper, query):
    """Scraper correctly parses 'Nonstop' as 0 stops."""
    html = _card_html([{"price": "250", "airline": "Delta", "stops": "Nonstop"}])
    respx.get(url__startswith="https://www.google.com/travel/flights").mock(
        return_value=httpx.Response(200, text=html)
    )

    results = await scraper.execute(query)
    assert len(results) == 1
    assert results[0].stops == 0


@respx.mock
async def test_empty_page_returns_empty_list(scraper, query):
    """Scraper returns empty list for a page with no flight data."""
    html = "<html><body><p>No flights found</p></body></html>"
    respx.get(url__startswith="https://www.google.com/travel/flights").mock(
        return_value=httpx.Response(200, text=html)
    )

    results = await scraper.execute(query)
    assert results == []


@respx.mock
async def test_http_error_raises(scraper, query):
    """Scraper raises on HTTP errors (caught by retry logic)."""
    respx.get(url__startswith="https://www.google.com/travel/flights").mock(
        return_value=httpx.Response(500, text="Server Error")
    )

    with pytest.raises(Exception):
        await scraper.execute(query)


@respx.mock
async def test_one_way_trip_url(scraper):
    """URL is built correctly for one-way trips (no return_date)."""
    query = ScrapeQuery(
        origin="SFO",
        destination="ORD",
        departure_date=date(2026, 8, 1),
        return_date=None,
        travelers=2,
    )
    html = "<html><body></body></html>"
    route = respx.get(url__startswith="https://www.google.com/travel/flights").mock(
        return_value=httpx.Response(200, text=html)
    )

    await scraper.execute(query)
    request_url = str(route.calls[0].request.url)
    assert "SFO" in request_url
    assert "ORD" in request_url
    assert "2026-08-01" in request_url
    assert "tfa=2" in request_url


@respx.mock
async def test_url_includes_travelers(scraper):
    """URL includes tfa parameter when travelers > 1."""
    query = ScrapeQuery(
        origin="JFK",
        destination="LAX",
        departure_date=date(2026, 6, 15),
        travelers=3,
    )
    html = "<html><body></body></html>"
    route = respx.get(url__startswith="https://www.google.com/travel/flights").mock(
        return_value=httpx.Response(200, text=html)
    )

    await scraper.execute(query)
    request_url = str(route.calls[0].request.url)
    assert "tfa=3" in request_url


@respx.mock
async def test_url_omits_travelers_for_single(scraper):
    """URL omits tfa parameter when travelers is 1 (default)."""
    query = ScrapeQuery(
        origin="JFK",
        destination="LAX",
        departure_date=date(2026, 6, 15),
        travelers=1,
    )
    html = "<html><body></body></html>"
    route = respx.get(url__startswith="https://www.google.com/travel/flights").mock(
        return_value=httpx.Response(200, text=html)
    )

    await scraper.execute(query)
    request_url = str(route.calls[0].request.url)
    assert "tfa=" not in request_url


@respx.mock
async def test_url_includes_cabin_class(scraper):
    """URL includes tfc parameter for non-economy cabin classes."""
    query = ScrapeQuery(
        origin="JFK",
        destination="LAX",
        departure_date=date(2026, 6, 15),
        cabin_class="business",
    )
    html = "<html><body></body></html>"
    route = respx.get(url__startswith="https://www.google.com/travel/flights").mock(
        return_value=httpx.Response(200, text=html)
    )

    await scraper.execute(query)
    request_url = str(route.calls[0].request.url)
    assert "tfc=3" in request_url


@respx.mock
async def test_url_omits_cabin_for_economy(scraper):
    """URL omits tfc parameter for economy (default)."""
    query = ScrapeQuery(
        origin="JFK",
        destination="LAX",
        departure_date=date(2026, 6, 15),
        cabin_class="economy",
    )
    html = "<html><body></body></html>"
    route = respx.get(url__startswith="https://www.google.com/travel/flights").mock(
        return_value=httpx.Response(200, text=html)
    )

    await scraper.execute(query)
    request_url = str(route.calls[0].request.url)
    assert "tfc=" not in request_url


@respx.mock
async def test_url_includes_both_travelers_and_cabin(scraper):
    """URL includes both tfa and tfc when both are non-default."""
    query = ScrapeQuery(
        origin="JFK",
        destination="LAX",
        departure_date=date(2026, 6, 15),
        return_date=date(2026, 6, 22),
        travelers=4,
        cabin_class="first",
    )
    html = "<html><body></body></html>"
    route = respx.get(url__startswith="https://www.google.com/travel/flights").mock(
        return_value=httpx.Response(200, text=html)
    )

    await scraper.execute(query)
    request_url = str(route.calls[0].request.url)
    assert "tfa=4" in request_url
    assert "tfc=4" in request_url


@respx.mock
async def test_json_ld_skips_non_offer_types(scraper, query):
    """Scraper ignores JSON-LD entries that aren't Offer/Flight types."""
    html = _json_ld_html([
        {"@type": "BreadcrumbList", "items": []},
        {"@type": "Offer", "price": "300", "priceCurrency": "USD"},
    ])
    respx.get(url__startswith="https://www.google.com/travel/flights").mock(
        return_value=httpx.Response(200, text=html)
    )

    results = await scraper.execute(query)
    assert len(results) == 1
    assert results[0].price == 30000


@respx.mock
async def test_json_ld_with_offers_array(scraper, query):
    """Scraper handles offers nested inside an offers array."""
    html = _json_ld_html([
        {
            "@type": "Offer",
            "offers": [{"price": "425"}],
            "priceCurrency": "USD",
        }
    ])
    respx.get(url__startswith="https://www.google.com/travel/flights").mock(
        return_value=httpx.Response(200, text=html)
    )

    results = await scraper.execute(query)
    assert len(results) == 1
    assert results[0].price == 42500
