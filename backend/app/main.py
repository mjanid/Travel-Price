"""FastAPI application entry point."""

from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded
from slowapi.util import get_remote_address

from fastapi.responses import JSONResponse

from app.api.v1 import api_v1_router
from app.core.config import get_settings


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Manage application startup and shutdown lifecycle."""
    yield
    # Shutdown: close Playwright browser pool
    from app.scrapers.playwright_base import _BrowserPool
    await _BrowserPool.reset()


def create_app() -> FastAPI:
    """Create and configure the FastAPI application.

    Returns:
        The configured FastAPI instance.
    """
    settings = get_settings()

    limiter = Limiter(key_func=get_remote_address, default_limits=["60/minute"])

    app = FastAPI(
        title=settings.app_name,
        debug=settings.debug,
        lifespan=lifespan,
    )
    app.state.limiter = limiter
    app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

    app.add_middleware(
        CORSMiddleware,
        allow_origins=[o.strip() for o in settings.cors_origins.split(",")],
        allow_credentials=True,
        allow_methods=["GET", "POST", "PATCH", "DELETE", "OPTIONS"],
        allow_headers=["Content-Type", "Authorization"],
    )

    app.include_router(api_v1_router)

    @app.get("/health")
    async def health_check() -> JSONResponse:
        return JSONResponse({"status": "healthy"})

    return app


app = create_app()
