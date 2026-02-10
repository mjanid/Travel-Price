#!/bin/sh
set -e

echo "Running database migrations..."
if ! alembic upgrade head; then
    echo "ERROR: Database migration failed" >&2
    exit 1
fi

echo "Starting $@"
exec "$@"
