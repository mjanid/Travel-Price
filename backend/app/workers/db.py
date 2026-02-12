"""Async database session factory for Celery workers."""

from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.core.config import get_settings

_engine = None
_session_factory = None


def _get_session_factory() -> async_sessionmaker[AsyncSession]:
    """Lazily create engine and session factory (singleton)."""
    global _engine, _session_factory
    if _session_factory is None:
        settings = get_settings()
        _engine = create_async_engine(
            settings.database_url, echo=False, pool_pre_ping=True
        )
        _session_factory = async_sessionmaker(
            _engine, class_=AsyncSession, expire_on_commit=False
        )
    return _session_factory


async def dispose_worker_db() -> None:
    """Dispose the global engine, releasing all pooled connections."""
    global _engine, _session_factory
    if _engine is not None:
        await _engine.dispose()
        _engine = None
        _session_factory = None


@asynccontextmanager
async def get_worker_db() -> AsyncGenerator[AsyncSession, None]:
    """Yield an async session with commit/rollback semantics for workers."""
    factory = _get_session_factory()
    async with factory() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
