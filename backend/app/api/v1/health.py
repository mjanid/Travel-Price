"""Health and readiness probe endpoints."""

import redis.asyncio as aioredis
from fastapi import APIRouter, Depends, Request
from fastapi.responses import JSONResponse
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import get_settings
from app.core.database import get_db
from app.core.limiter import limiter

router = APIRouter(tags=["health"])


@router.get("/health")
@limiter.exempt
async def health(request: Request) -> dict:
    """Liveness probe. Returns 200 with no external dependency checks.

    Args:
        request: The incoming HTTP request (required by slowapi exempt decorator).

    Returns:
        A simple status dict indicating the service is alive.
    """
    return {"status": "ok"}


@router.get("/ready")
@limiter.exempt
async def readiness(
    request: Request, session: AsyncSession = Depends(get_db)
) -> JSONResponse:
    """Readiness probe. Checks Postgres and Redis connectivity.

    Args:
        request: The incoming HTTP request (required by slowapi exempt decorator).
        session: Async database session injected by FastAPI.

    Returns:
        200 with all checks passing, or 503 if any dependency is unreachable.
    """
    settings = get_settings()
    checks: dict[str, str] = {}
    all_ok = True

    # Check Postgres
    try:
        await session.execute(text("SELECT 1"))
        checks["postgres"] = "ok"
    except Exception:
        checks["postgres"] = "error"
        all_ok = False

    # Check Redis
    try:
        r = aioredis.from_url(settings.redis_url)
        try:
            await r.ping()
            checks["redis"] = "ok"
        finally:
            await r.aclose()
    except Exception:
        checks["redis"] = "error"
        all_ok = False

    status_code = 200 if all_ok else 503
    return JSONResponse(
        status_code=status_code,
        content={"status": "ready" if all_ok else "degraded", "checks": checks},
    )
