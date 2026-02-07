"""Application configuration loaded from environment variables."""

from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


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

    secret_key: str = "CHANGE-ME-IN-PRODUCTION"
    jwt_algorithm: str = "HS256"
    access_token_expire_minutes: int = 30
    refresh_token_expire_days: int = 7

    cors_origins: str = "http://localhost:3000"


@lru_cache
def get_settings() -> Settings:
    """Return a cached Settings instance."""
    return Settings()
