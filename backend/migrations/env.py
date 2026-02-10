"""Alembic environment configuration."""

from logging.config import fileConfig

from alembic import context
from sqlalchemy import engine_from_config, pool
import sqlalchemy as sa

from app.core.config import get_settings
from app.core.database import Base
from app.models import Alert, PriceSnapshot, PriceWatch, Trip, User  # noqa: F401

config = context.config

if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# Override sqlalchemy.url from app settings (convert async URL to sync)
settings = get_settings()
sync_url = settings.database_url.replace("+asyncpg", "")
config.set_main_option("sqlalchemy.url", sync_url)

target_metadata = Base.metadata


def _ensure_alembic_version_table_capacity(connection) -> None:
    """Ensure alembic_version.version_num can store our revision identifiers."""
    if connection.dialect.name != "postgresql":
        return

    connection.execute(
        sa.text(
            """
            CREATE TABLE IF NOT EXISTS alembic_version (
                version_num VARCHAR(255) NOT NULL,
                CONSTRAINT alembic_version_pkc PRIMARY KEY (version_num)
            )
            """
        )
    )
    connection.execute(
        sa.text("ALTER TABLE alembic_version ALTER COLUMN version_num TYPE VARCHAR(255)")
    )


def run_migrations_offline() -> None:
    """Run migrations in 'offline' mode."""
    url = config.get_main_option("sqlalchemy.url")
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )

    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    """Run migrations in 'online' mode."""
    connectable = engine_from_config(
        config.get_section(config.config_ini_section, {}),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )

    with connectable.connect() as connection:
        _ensure_alembic_version_table_capacity(connection)

        context.configure(
            connection=connection,
            target_metadata=target_metadata,
        )

        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
