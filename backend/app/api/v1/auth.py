"""Authentication route handlers."""

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.security import get_current_user
from app.models.user import User
from app.schemas.auth import (
    TokenRefreshRequest,
    TokenResponse,
    UserLoginRequest,
    UserRegisterRequest,
    UserResponse,
    UserUpdateRequest,
)
from app.schemas.common import ApiResponse
from app.services.auth_service import AuthService

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/register", response_model=ApiResponse[UserResponse], status_code=201)
async def register(
    payload: UserRegisterRequest,
    db: AsyncSession = Depends(get_db),
) -> ApiResponse[UserResponse]:
    """Register a new user account."""
    service = AuthService(db)
    user = await service.register(payload)
    return ApiResponse(data=user)


@router.post("/login", response_model=ApiResponse[TokenResponse])
async def login(
    payload: UserLoginRequest,
    db: AsyncSession = Depends(get_db),
) -> ApiResponse[TokenResponse]:
    """Authenticate and receive JWT tokens."""
    service = AuthService(db)
    tokens = await service.login(payload.email, payload.password)
    return ApiResponse(data=tokens)


@router.post("/refresh", response_model=ApiResponse[TokenResponse])
async def refresh(
    payload: TokenRefreshRequest,
    db: AsyncSession = Depends(get_db),
) -> ApiResponse[TokenResponse]:
    """Refresh JWT tokens using a valid refresh token."""
    service = AuthService(db)
    tokens = await service.refresh(payload.refresh_token)
    return ApiResponse(data=tokens)


@router.get("/me", response_model=ApiResponse[UserResponse])
async def get_me(
    current_user: User = Depends(get_current_user),
) -> ApiResponse[UserResponse]:
    """Get the currently authenticated user's profile."""
    return ApiResponse(data=UserResponse.model_validate(current_user))


@router.patch("/me", response_model=ApiResponse[UserResponse])
async def update_me(
    payload: UserUpdateRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> ApiResponse[UserResponse]:
    """Update the currently authenticated user's profile."""
    service = AuthService(db)
    user = await service.update_profile(current_user, payload)
    return ApiResponse(data=user)
