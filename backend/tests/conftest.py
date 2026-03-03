"""Shared test fixtures."""

import os
from unittest.mock import AsyncMock, MagicMock, patch

# Set test environment variables before importing app modules so that
# config validation passes (the default secret key is rejected in non-debug mode).
os.environ.setdefault("DEBUG", "true")

import pytest
from httpx import ASGITransport, AsyncClient
from sqlalchemy import event
from sqlalchemy.engine import make_url
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.core.database import Base, get_db
from app.main import app

# Ensure every ORM model is registered on Base.metadata (used by both
# the SQLite unit-test engine and the Postgres integration-test engine).
from app import models as _models  # noqa: F401

TEST_DATABASE_URL = "sqlite+aiosqlite:///:memory:"


# ---------------------------------------------------------------------------
# SQLite fixtures — used by service / unit tests
# ---------------------------------------------------------------------------


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


# ---------------------------------------------------------------------------
# PostgreSQL fixtures — used by route / integration tests
# ---------------------------------------------------------------------------


@pytest.fixture(scope="session")
def postgres_url():
    """Return an asyncpg PostgreSQL connection URL.

    In CI the ``DATABASE_URL`` environment variable already points to the
    PostgreSQL service container provisioned by the GitHub Actions workflow,
    so we reuse it directly.  Locally (when ``DATABASE_URL`` is unset or
    points at SQLite) we fall back to spinning up a disposable container
    via *testcontainers*.
    """
    env_url = os.environ.get("DATABASE_URL", "")
    if env_url and "postgresql" in env_url:
        # CI — reuse the pre-provisioned PostgreSQL service.
        url = make_url(env_url)
        yield str(url.set(drivername="postgresql+asyncpg"))
        return

    # Local development — start a throwaway PostgreSQL container.
    from testcontainers.postgres import PostgresContainer

    with PostgresContainer("postgres:16-alpine") as pg:
        sync_url = pg.get_connection_url()
        url = make_url(sync_url)
        yield str(url.set(drivername="postgresql+asyncpg"))


@pytest.fixture(scope="session")
async def pg_engine(postgres_url):
    """Create tables once per session and yield the async engine."""
    engine = create_async_engine(postgres_url, echo=False)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield engine
    await engine.dispose()


@pytest.fixture
async def pg_session(pg_engine):
    """Yield a transactional session that is rolled back after each test.

    Uses the SAVEPOINT (nested transaction) pattern so that
    ``session.commit()`` inside ``get_db`` releases a savepoint instead
    of issuing a real COMMIT.  The outer transaction is rolled back at
    the end, keeping tests fully isolated.
    """
    async with pg_engine.connect() as conn:
        transaction = await conn.begin()
        session = AsyncSession(
            bind=conn, expire_on_commit=False, join_transaction_block=True
        )

        # When the inner SAVEPOINT ends, automatically start a new one
        # so that successive commit() calls within the same test work.
        @event.listens_for(session.sync_session, "after_transaction_end")
        def _restart_savepoint(sync_session, trans):
            if trans.nested and not trans._parent.nested:
                sync_session.begin_nested()

        yield session
        await session.close()
        await transaction.rollback()


@pytest.fixture
async def pg_client(pg_session):
    """Async HTTP test client wired to the transactional Postgres session.

    Overrides FastAPI's ``get_db`` dependency so that route handlers use
    the same rolled-back session, keeping integration tests isolated.
    """
    async def _override_get_db():
        yield pg_session

    app.dependency_overrides[get_db] = _override_get_db
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac
    app.dependency_overrides.clear()


# ---------------------------------------------------------------------------
# Shared utility fixtures
# ---------------------------------------------------------------------------


@pytest.fixture
def mock_playwright_page():
    """Create a mock Playwright Page for unit-testing scrape_page().

    The mock page supports goto, wait_for_selector, wait_for_function,
    evaluate, frames, set_default_timeout, and close.
    """
    page = AsyncMock()
    page.goto = AsyncMock()
    page.wait_for_selector = AsyncMock()
    page.wait_for_function = AsyncMock()
    page.evaluate = AsyncMock(return_value=[])
    page.close = AsyncMock()
    page.set_default_timeout = MagicMock()

    # frames — used by consent dismissal (no consent frames by default)
    page.frames = [MagicMock(url="https://www.google.com/travel/flights")]

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
