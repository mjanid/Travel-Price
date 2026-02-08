"""Test data factories."""

import uuid

from app.core.security import hash_password
from app.models.price_watch import PriceWatch
from app.models.user import User


def build_user(**overrides: object) -> User:
    """Build a User ORM instance with sensible defaults.

    Args:
        **overrides: Keyword arguments to override default field values.

    Returns:
        A User instance (not yet persisted).
    """
    defaults: dict[str, object] = {
        "email": "test@example.com",
        "hashed_password": hash_password("testpassword123"),
        "full_name": "Test User",
        "is_active": True,
    }
    defaults.update(overrides)
    return User(**defaults)


def build_price_watch(
    user_id: uuid.UUID, trip_id: uuid.UUID, **overrides: object
) -> PriceWatch:
    """Build a PriceWatch ORM instance with sensible defaults.

    Args:
        user_id: The watch owner's ID.
        trip_id: The trip to watch.
        **overrides: Keyword arguments to override default field values.

    Returns:
        A PriceWatch instance (not yet persisted).
    """
    defaults: dict[str, object] = {
        "user_id": user_id,
        "trip_id": trip_id,
        "provider": "google_flights",
        "target_price": 30000,
        "currency": "USD",
        "is_active": True,
        "alert_cooldown_hours": 6,
    }
    defaults.update(overrides)
    return PriceWatch(**defaults)
