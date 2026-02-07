"""Test data factories."""

from app.core.security import hash_password
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
