"""Application configuration loaded from environment variables."""

import warnings
from functools import lru_cache

from pydantic import field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

_INSECURE_DEFAULT_KEY = "CHANGE-ME-IN-PRODUCTION"


class Settings(BaseSettings):
    """Application configuration.

    All values can be overridden via environment variables or a .env file.

    Attributes:
        app_name: Display name of the application.
        debug: Enable debug mode.
        database_url: Async PostgreSQL connection string.
        redis_url: Redis connection string for cache/queue.
        secret_key: Secret for JWT signing. Must be changed in production.
        jwt_algorithm: Algorithm for JWT tokens.
        access_token_expire_minutes: Lifetime of access tokens in minutes.
        refresh_token_expire_days: Lifetime of refresh tokens in days.
        cors_origins: Allowed CORS origins as comma-separated string.
    """

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
    )

    app_name: str = "Travel Price Scraper"
    debug: bool = False

    database_url: str = "postgresql+asyncpg://postgres:postgres@localhost:5432/travel_price"
    redis_url: str = "redis://localhost:6379/0"

    secret_key: str = _INSECURE_DEFAULT_KEY
    jwt_algorithm: str = "HS256"
    access_token_expire_minutes: int = 30
    refresh_token_expire_days: int = 7

    cors_origins: str = "http://localhost:3000"

    # Celery / Worker settings
    celery_broker_url: str = "redis://localhost:6379/1"
    celery_result_backend: str = "redis://localhost:6379/2"
    scrape_interval_minutes: int = 60

    # Alert / Notification settings
    alert_cooldown_hours: int = 6
    smtp_host: str = ""
    smtp_port: int = 587
    smtp_user: str = ""
    smtp_password: str = ""
    smtp_from_email: str = "alerts@travelprice.local"

    # Playwright settings
    playwright_headless: bool = True
    playwright_timeout_ms: int = 45000
    playwright_screenshot_on_failure: bool = False

    @field_validator("scrape_interval_minutes")
    @classmethod
    def validate_scrape_interval(cls, v: int) -> int:
        """Ensure scrape interval is positive."""
        if v <= 0:
            raise ValueError("scrape_interval_minutes must be positive")
        return v

    def warn_if_insecure(self) -> None:
        """Emit a warning if the secret key is the insecure default."""
        if self.secret_key == _INSECURE_DEFAULT_KEY:
            if self.debug:
                warnings.warn(
                    "Using insecure default SECRET_KEY. "
                    "Set SECRET_KEY env var before deploying.",
                    UserWarning,
                    stacklevel=2,
                )
            else:
                raise ValueError(
                    "SECRET_KEY must be changed from the default value "
                    "in non-debug mode. Generate one with: "
                    'python -c "import secrets; print(secrets.token_urlsafe(32))"'
                )


@lru_cache
def get_settings() -> Settings:
    """Return a cached Settings instance."""
    settings = Settings()
    settings.warn_if_insecure()
    return settings
