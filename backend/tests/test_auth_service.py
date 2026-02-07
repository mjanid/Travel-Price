"""Unit tests for AuthService."""

import pytest
from fastapi import HTTPException

from app.core.security import create_access_token, create_refresh_token
from app.schemas.auth import UserRegisterRequest
from app.services.auth_service import AuthService
from tests.factories import build_user


async def test_register_success(db_session):
    """Registration with valid data returns user response."""
    service = AuthService(db_session)
    payload = UserRegisterRequest(
        email="new@example.com",
        password="securepassword",
        full_name="New User",
    )
    result = await service.register(payload)
    assert result.email == "new@example.com"
    assert result.full_name == "New User"
    assert result.is_active is True
    assert result.id is not None


async def test_register_duplicate_email(db_session):
    """Registration with existing email raises 409."""
    user = build_user(email="dup@example.com")
    db_session.add(user)
    await db_session.flush()

    service = AuthService(db_session)
    payload = UserRegisterRequest(
        email="dup@example.com",
        password="securepassword",
        full_name="Duplicate",
    )
    with pytest.raises(HTTPException) as exc_info:
        await service.register(payload)
    assert exc_info.value.status_code == 409


async def test_login_success(db_session):
    """Login with valid credentials returns tokens."""
    service = AuthService(db_session)
    await service.register(
        UserRegisterRequest(
            email="login@example.com",
            password="securepassword",
            full_name="Login User",
        )
    )
    tokens = await service.login("login@example.com", "securepassword")
    assert tokens.access_token
    assert tokens.refresh_token
    assert tokens.token_type == "bearer"


async def test_login_wrong_password(db_session):
    """Login with wrong password raises 401."""
    service = AuthService(db_session)
    await service.register(
        UserRegisterRequest(
            email="wrong@example.com",
            password="securepassword",
            full_name="Wrong PW User",
        )
    )
    with pytest.raises(HTTPException) as exc_info:
        await service.login("wrong@example.com", "badpassword")
    assert exc_info.value.status_code == 401


async def test_login_nonexistent_email(db_session):
    """Login with nonexistent email raises 401."""
    service = AuthService(db_session)
    with pytest.raises(HTTPException) as exc_info:
        await service.login("nobody@example.com", "whatever")
    assert exc_info.value.status_code == 401


async def test_login_inactive_user(db_session):
    """Login with inactive user raises 403."""
    user = build_user(email="inactive@example.com", is_active=False)
    db_session.add(user)
    await db_session.flush()

    service = AuthService(db_session)
    with pytest.raises(HTTPException) as exc_info:
        await service.login("inactive@example.com", "testpassword123")
    assert exc_info.value.status_code == 403


async def test_refresh_success(db_session):
    """Refresh with valid token returns new tokens."""
    service = AuthService(db_session)
    reg = await service.register(
        UserRegisterRequest(
            email="refresh@example.com",
            password="securepassword",
            full_name="Refresh User",
        )
    )
    refresh_token = create_refresh_token(reg.id)
    tokens = await service.refresh(refresh_token)
    assert tokens.access_token
    assert tokens.refresh_token


async def test_refresh_with_access_token_fails(db_session):
    """Using an access token for refresh raises 401."""
    service = AuthService(db_session)
    reg = await service.register(
        UserRegisterRequest(
            email="badrefresh@example.com",
            password="securepassword",
            full_name="Bad Refresh User",
        )
    )
    access_token = create_access_token(reg.id)
    with pytest.raises(HTTPException) as exc_info:
        await service.refresh(access_token)
    assert exc_info.value.status_code == 401


async def test_refresh_invalid_token(db_session):
    """Refresh with garbage token raises 401."""
    service = AuthService(db_session)
    with pytest.raises(HTTPException) as exc_info:
        await service.refresh("not-a-real-token")
    assert exc_info.value.status_code == 401
