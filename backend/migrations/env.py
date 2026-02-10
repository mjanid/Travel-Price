"""Alembic environment configuration."""

from logging.config import fileConfig

from alembic import context
from sqlalchemy import engine_from_config, inspect, pool
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

LEGACY_REVISION_ID_MAP = {
    "002_price_watches_last_alerted_at": "002_last_alerted_at",
}


def _remap_legacy_revision_ids(connection) -> None:
    """Remap legacy Alembic revision IDs to current IDs before migration resolution."""
    if not inspect(connection).has_table("alembic_version"):
        return

    for old_revision_id, new_revision_id in LEGACY_REVISION_ID_MAP.items():
        connection.execute(
            sa.text(
                """
                UPDATE alembic_version
                SET version_num = :new_revision_id
                WHERE version_num = :old_revision_id
                """
            ),
            {
                "old_revision_id": old_revision_id,
                "new_revision_id": new_revision_id,
            },
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
        _remap_legacy_revision_ids(connection)

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
