"""Shared test fixtures."""

import os
from unittest.mock import AsyncMock, MagicMock, patch

# Set test environment variables before importing app modules so that
# config validation passes (the default secret key is rejected in non-debug mode).
os.environ.setdefault("DEBUG", "true")

import pytest
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.core.database import Base, get_db
from app.main import app

TEST_DATABASE_URL = "sqlite+aiosqlite:///:memory:"


@pytest.fixture
async def db_session():
    """Create a fresh in-memory SQLite database for each test."""
    engine = create_async_engine(TEST_DATABASE_URL, echo=False)

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    session_factory = async_sessionmaker(
        engine, class_=AsyncSession, expire_on_commit=False
    )
    async with session_factory() as session:
        yield session

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
    await engine.dispose()


@pytest.fixture
async def client(db_session: AsyncSession):
    """Async HTTP test client with database dependency overridden."""

    async def override_get_db():
        yield db_session

    app.dependency_overrides[get_db] = override_get_db
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac
    app.dependency_overrides.clear()


@pytest.fixture
def mock_playwright_page():
    """Create a mock Playwright Page for unit-testing scrape_page().

    The mock page supports goto, wait_for_selector, wait_for_function,
    evaluate, locator, set_default_timeout, and close.
    """
    page = AsyncMock()
    page.goto = AsyncMock()
    page.wait_for_selector = AsyncMock()
    page.wait_for_function = AsyncMock()
    page.evaluate = AsyncMock(return_value=[])
    page.close = AsyncMock()
    page.set_default_timeout = MagicMock()

    # locator().first.is_visible() — used by consent dismissal
    locator_mock = MagicMock()
    first_mock = AsyncMock()
    first_mock.is_visible = AsyncMock(return_value=False)
    first_mock.click = AsyncMock()
    locator_mock.first = first_mock
    page.locator = MagicMock(return_value=locator_mock)

    return page


@pytest.fixture(autouse=True)
def _mock_browser_pool():
    """Prevent actual browser launches during all unit tests.

    Patches the _BrowserPool singleton so Playwright is never started.
    Tests that need a page should use the mock_playwright_page fixture
    and call scrape_page() directly.
    """
    with patch(
        "app.scrapers.playwright_base._BrowserPool.get_instance", new_callable=AsyncMock
    ) as mock_get:
        pool = AsyncMock()
        mock_get.return_value = pool
        yield pool
