"""Unit tests for BaseScraper retry logic, rate limiting, and proxy rotation."""

import asyncio
from unittest.mock import AsyncMock, MagicMock

import pytest

from app.scrapers.base import BaseScraper
from app.scrapers.types import PriceResult, ScrapeError, ScrapeQuery


class DummyScraper(BaseScraper):
    """Concrete scraper for testing."""

    provider_name = "test_provider"

    def __init__(self, results=None, fail_times=0, **kwargs):
        super().__init__(**kwargs)
        self._results = results or []
        self._fail_times = fail_times
        self._call_count = 0

    async def scrape(self, query: ScrapeQuery) -> list[PriceResult]:
        self._call_count += 1
        if self._call_count <= self._fail_times:
            raise RuntimeError(f"Simulated failure #{self._call_count}")
        return self._results


@pytest.fixture
def sample_query():
    from datetime import date

    return ScrapeQuery(
        origin="JFK",
        destination="LAX",
        departure_date=date(2026, 6, 15),
        return_date=date(2026, 6, 22),
        travelers=1,
    )


@pytest.fixture
def sample_results():
    from datetime import datetime, timezone

    return [
        PriceResult(
            provider="test_provider",
            price=25000,
            currency="USD",
            airline="Test Air",
            scraped_at=datetime.now(timezone.utc),
        )
    ]


async def test_execute_success(sample_query, sample_results):
    """execute() returns results on first try."""
    scraper = DummyScraper(results=sample_results)
    results = await scraper.execute(sample_query)
    assert len(results) == 1
    assert results[0].price == 25000
    assert scraper._call_count == 1


async def test_retry_on_failure(sample_query, sample_results):
    """execute() retries and succeeds after transient failures."""
    scraper = DummyScraper(
        results=sample_results, fail_times=2, base_delay=0.01
    )
    results = await scraper.execute(sample_query)
    assert len(results) == 1
    assert scraper._call_count == 3  # 2 failures + 1 success


async def test_retry_exhausted(sample_query):
    """execute() raises ScrapeError after max retries."""
    scraper = DummyScraper(fail_times=10, max_retries=2, base_delay=0.01)
    with pytest.raises(ScrapeError) as exc_info:
        await scraper.execute(sample_query)
    assert exc_info.value.provider == "test_provider"
    assert exc_info.value.retries == 2
    assert scraper._call_count == 3  # initial + 2 retries


async def test_rate_limit_passes(sample_query, sample_results):
    """execute() passes rate limit check when under threshold."""
    mock_redis = AsyncMock()
    mock_redis.incr.return_value = 1
    mock_redis.expire.return_value = True

    scraper = DummyScraper(results=sample_results, redis_client=mock_redis)
    results = await scraper.execute(sample_query)
    assert len(results) == 1
    mock_redis.incr.assert_called_once()


async def test_rate_limit_exceeded(sample_query, sample_results):
    """execute() raises ScrapeError when rate limit exceeded."""
    mock_redis = AsyncMock()
    mock_redis.incr.return_value = 100  # Over default limit of 10
    mock_redis.ttl.return_value = 45

    scraper = DummyScraper(results=sample_results, redis_client=mock_redis)
    with pytest.raises(ScrapeError) as exc_info:
        await scraper.execute(sample_query)
    assert "Rate limit exceeded" in str(exc_info.value)


async def test_rate_limit_redis_failure_proceeds(sample_query, sample_results):
    """execute() proceeds gracefully if Redis is unavailable."""
    mock_redis = AsyncMock()
    mock_redis.incr.side_effect = ConnectionError("Redis down")

    scraper = DummyScraper(results=sample_results, redis_client=mock_redis)
    results = await scraper.execute(sample_query)
    assert len(results) == 1


async def test_proxy_rotation():
    """_get_proxy() cycles through proxies round-robin."""
    proxies = ["http://proxy1:8080", "http://proxy2:8080", "http://proxy3:8080"]
    scraper = DummyScraper(proxies=proxies)
    results = [scraper._get_proxy() for _ in range(6)]
    assert results == proxies + proxies


async def test_no_proxy_returns_none():
    """_get_proxy() returns None when no proxies configured."""
    scraper = DummyScraper()
    assert scraper._get_proxy() is None


async def test_headers_contain_user_agent():
    """_get_headers() returns dict with User-Agent."""
    scraper = DummyScraper()
    headers = scraper._get_headers()
    assert "User-Agent" in headers
    assert "Mozilla" in headers["User-Agent"]


async def test_custom_max_retries(sample_query):
    """Constructor override for max_retries is respected."""
    scraper = DummyScraper(fail_times=5, max_retries=4, base_delay=0.01)
    with pytest.raises(ScrapeError) as exc_info:
        await scraper.execute(sample_query)
    assert exc_info.value.retries == 4
    assert scraper._call_count == 5
