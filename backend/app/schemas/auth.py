"""Request and response schemas for authentication endpoints."""

import uuid
from datetime import datetime

from pydantic import BaseModel, EmailStr, Field


class UserRegisterRequest(BaseModel):
    """Schema for user registration request.

    Attributes:
        email: User's email address.
        password: Plain-text password (min 8 chars).
        full_name: User's display name.
    """

    email: EmailStr
    password: str = Field(min_length=8, max_length=128)
    full_name: str = Field(min_length=1, max_length=255)


class UserLoginRequest(BaseModel):
    """Schema for user login request."""

    email: EmailStr
    password: str


class TokenRefreshRequest(BaseModel):
    """Schema for token refresh request."""

    refresh_token: str


class TokenResponse(BaseModel):
    """Schema for JWT token pair response."""

    access_token: str
    refresh_token: str
    token_type: str = "bearer"


class UserResponse(BaseModel):
    """Schema for user data in API responses."""

    id: uuid.UUID
    email: str
    full_name: str
    is_active: bool
    created_at: datetime

    model_config = {"from_attributes": True}
