"""Business logic for user authentication."""

from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import (
    create_access_token,
    create_refresh_token,
    decode_token,
    hash_password,
    verify_password,
)
from app.models.user import User
from app.schemas.auth import (
    TokenResponse,
    UserRegisterRequest,
    UserResponse,
    UserUpdateRequest,
)


class AuthService:
    """Service handling user registration, login, and token refresh.

    Args:
        db: The async database session.
    """

    def __init__(self, db: AsyncSession) -> None:
        self.db = db

    async def register(self, payload: UserRegisterRequest) -> UserResponse:
        """Register a new user account.

        Args:
            payload: Registration data (email, password, full_name).

        Returns:
            The created user's public data.

        Raises:
            HTTPException: 409 if email already exists.
        """
        result = await self.db.execute(
            select(User).where(User.email == payload.email)
        )
        if result.scalar_one_or_none() is not None:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Email already registered",
            )

        user = User(
            email=payload.email,
            hashed_password=hash_password(payload.password),
            full_name=payload.full_name,
        )
        self.db.add(user)
        await self.db.flush()
        await self.db.refresh(user)
        return UserResponse.model_validate(user)

    async def login(self, email: str, password: str) -> TokenResponse:
        """Authenticate a user and return JWT tokens.

        Args:
            email: The user's email.
            password: The plain-text password.

        Returns:
            A TokenResponse with access and refresh tokens.

        Raises:
            HTTPException: 401 if credentials are invalid, 403 if inactive.
        """
        result = await self.db.execute(select(User).where(User.email == email))
        user = result.scalar_one_or_none()

        if user is None or not verify_password(password, user.hashed_password):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid email or password",
            )

        if not user.is_active:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Account is deactivated",
            )

        return TokenResponse(
            access_token=create_access_token(user.id),
            refresh_token=create_refresh_token(user.id),
        )

    async def refresh(self, refresh_token: str) -> TokenResponse:
        """Issue new tokens using a valid refresh token.

        Args:
            refresh_token: The JWT refresh token.

        Returns:
            A new TokenResponse with fresh access and refresh tokens.

        Raises:
            HTTPException: 401 if refresh token is invalid or user not found.
        """
        user_id = decode_token(refresh_token, expected_type="refresh")

        result = await self.db.execute(select(User).where(User.id == user_id))
        user = result.scalar_one_or_none()

        if user is None or not user.is_active:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="User not found or inactive",
            )

        return TokenResponse(
            access_token=create_access_token(user.id),
            refresh_token=create_refresh_token(user.id),
        )

    async def update_profile(
        self, user: User, payload: UserUpdateRequest
    ) -> UserResponse:
        """Update the current user's profile.

        Args:
            user: The authenticated User ORM instance.
            payload: Fields to update (only non-None fields are applied).

        Returns:
            The updated user's public data.
        """
        if payload.full_name is not None:
            user.full_name = payload.full_name
        if payload.password is not None:
            user.hashed_password = hash_password(payload.password)

        self.db.add(user)
        await self.db.flush()
        await self.db.refresh(user)
        return UserResponse.model_validate(user)
