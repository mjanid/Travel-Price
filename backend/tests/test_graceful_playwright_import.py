"""Tests for graceful Playwright import handling.

Verifies that:
- PlaywrightBaseScraper raises RuntimeError when Playwright is unavailable
- The scraper registry excludes Playwright scrapers when unavailable
- The registry provides clear error messages for missing providers
"""

from unittest.mock import patch

import pytest

from app.scrapers.base import BaseScraper


def test_playwright_base_raises_when_not_installed():
    """PlaywrightBaseScraper.__init__() raises RuntimeError when Playwright is missing."""
    from app.scrapers.playwright_base import PlaywrightBaseScraper

    # Create a concrete subclass so ABC doesn't block instantiation
    class _ConcreteScraper(PlaywrightBaseScraper):
        provider_name = "test"

        async def scrape_page(self, page, query):
            return []

    with patch("app.scrapers.playwright_base.PLAYWRIGHT_AVAILABLE", False):
        with pytest.raises(RuntimeError, match="Playwright is not installed"):
            _ConcreteScraper()


def test_playwright_base_works_when_installed():
    """PlaywrightBaseScraper.__init__() succeeds when Playwright is available."""
    with patch("app.scrapers.playwright_base.PLAYWRIGHT_AVAILABLE", True):
        from app.scrapers.playwright_base import PlaywrightBaseScraper

        # PlaywrightBaseScraper is abstract, so we need a concrete subclass
        class _DummyScraper(PlaywrightBaseScraper):
            provider_name = "dummy"

            async def scrape_page(self, page, query):
                return []

        # Should not raise
        scraper = _DummyScraper()
        assert scraper.provider_name == "dummy"


def test_registry_excludes_playwright_scrapers_when_unavailable():
    """SCRAPER_REGISTRY omits google_flights when PLAYWRIGHT_AVAILABLE is False."""
    with patch("app.scrapers.playwright_base.PLAYWRIGHT_AVAILABLE", False):
        # Re-build the registry with Playwright unavailable
        import importlib
        import app.scrapers.registry as registry_mod

        importlib.reload(registry_mod)

        assert "google_flights" not in registry_mod.SCRAPER_REGISTRY

    # Restore the registry to its normal state
    import importlib
    import app.scrapers.registry as registry_mod

    importlib.reload(registry_mod)


def test_registry_includes_playwright_scrapers_when_available():
    """SCRAPER_REGISTRY includes google_flights when PLAYWRIGHT_AVAILABLE is True."""
    from app.scrapers.registry import SCRAPER_REGISTRY

    # In the test environment, Playwright IS installed
    assert "google_flights" in SCRAPER_REGISTRY


def test_get_scraper_clear_error_when_provider_unavailable():
    """get_scraper() provides a clear error when provider is not in registry."""
    with patch("app.scrapers.playwright_base.PLAYWRIGHT_AVAILABLE", False):
        import importlib
        import app.scrapers.registry as registry_mod

        importlib.reload(registry_mod)

        with pytest.raises(ValueError, match="not available"):
            registry_mod.get_scraper("google_flights")

    # Restore the registry
    import importlib
    import app.scrapers.registry as registry_mod

    importlib.reload(registry_mod)


def test_get_scraper_error_lists_available_when_others_exist():
    """get_scraper() lists available providers when some exist but requested one doesn't."""
    from app.scrapers.registry import get_scraper

    with pytest.raises(ValueError, match="Available:"):
        get_scraper("nonexistent_provider")


def test_playwright_available_flag_is_true():
    """PLAYWRIGHT_AVAILABLE is True in test environment (Playwright is installed)."""
    from app.scrapers.playwright_base import PLAYWRIGHT_AVAILABLE

    assert PLAYWRIGHT_AVAILABLE is True
