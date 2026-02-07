"""Security utilities: password hashing, JWT tokens, and auth dependencies."""

import uuid
from datetime import datetime, timedelta, timezone

from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError, jwt
from passlib.context import CryptContext
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import Settings, get_settings
from app.core.database import get_db
from app.models.user import User

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/auth/login")


def hash_password(password: str) -> str:
    """Hash a plain-text password using bcrypt.

    Args:
        password: The plain-text password.

    Returns:
        The bcrypt hash string.
    """
    return pwd_context.hash(password)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify a plain-text password against a bcrypt hash.

    Args:
        plain_password: The plain-text password to check.
        hashed_password: The stored bcrypt hash.

    Returns:
        True if the password matches, False otherwise.
    """
    return pwd_context.verify(plain_password, hashed_password)


def create_access_token(
    subject: uuid.UUID,
    settings: Settings | None = None,
) -> str:
    """Create a short-lived JWT access token.

    Args:
        subject: The user ID to encode as the token subject.
        settings: Application settings. Uses default if None.

    Returns:
        Encoded JWT string.
    """
    if settings is None:
        settings = get_settings()
    expire = datetime.now(timezone.utc) + timedelta(
        minutes=settings.access_token_expire_minutes
    )
    payload = {
        "sub": str(subject),
        "exp": expire,
        "type": "access",
    }
    return jwt.encode(payload, settings.secret_key, algorithm=settings.jwt_algorithm)


def create_refresh_token(
    subject: uuid.UUID,
    settings: Settings | None = None,
) -> str:
    """Create a long-lived JWT refresh token.

    Args:
        subject: The user ID to encode as the token subject.
        settings: Application settings. Uses default if None.

    Returns:
        Encoded JWT string.
    """
    if settings is None:
        settings = get_settings()
    expire = datetime.now(timezone.utc) + timedelta(
        days=settings.refresh_token_expire_days
    )
    payload = {
        "sub": str(subject),
        "exp": expire,
        "type": "refresh",
    }
    return jwt.encode(payload, settings.secret_key, algorithm=settings.jwt_algorithm)


def decode_token(token: str, expected_type: str = "access") -> uuid.UUID:
    """Decode and validate a JWT token.

    Args:
        token: The encoded JWT string.
        expected_type: Expected token type ("access" or "refresh").

    Returns:
        The user UUID extracted from the token subject.

    Raises:
        HTTPException: If the token is invalid, expired, or wrong type.
    """
    settings = get_settings()
    try:
        payload = jwt.decode(
            token, settings.secret_key, algorithms=[settings.jwt_algorithm]
        )
        user_id: str | None = payload.get("sub")
        token_type: str | None = payload.get("type")
        if user_id is None or token_type != expected_type:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid token",
            )
        return uuid.UUID(user_id)
    except JWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token",
        )


async def get_current_user(
    token: str = Depends(oauth2_scheme),
    db: AsyncSession = Depends(get_db),
) -> User:
    """FastAPI dependency that extracts the current user from a JWT.

    Args:
        token: The bearer token extracted by OAuth2PasswordBearer.
        db: The async database session.

    Returns:
        The authenticated User ORM instance.

    Raises:
        HTTPException: 401 if token invalid or user not found/inactive.
    """
    user_id = decode_token(token, expected_type="access")
    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()
    if user is None or not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found or inactive",
        )
    return user
