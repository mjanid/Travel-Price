"""Integration tests for auth API endpoints."""

import pytest

pytestmark = pytest.mark.integration


async def test_register_success(pg_client):
    """POST /register returns 201 with user data in envelope."""
    response = await pg_client.post(
        "/api/v1/auth/register",
        json={
            "email": "new@example.com",
            "password": "securepassword",
            "full_name": "New User",
        },
    )
    assert response.status_code == 201
    body = response.json()
    assert "data" in body
    assert body["data"]["email"] == "new@example.com"
    assert body["data"]["full_name"] == "New User"
    assert "id" in body["data"]


async def test_register_duplicate_email(pg_client):
    """POST /register with existing email returns 409."""
    payload = {
        "email": "dup@example.com",
        "password": "securepassword",
        "full_name": "First User",
    }
    await pg_client.post("/api/v1/auth/register", json=payload)
    response = await pg_client.post("/api/v1/auth/register", json=payload)
    assert response.status_code == 409


async def test_register_invalid_email(pg_client):
    """POST /register with invalid email returns 422."""
    response = await pg_client.post(
        "/api/v1/auth/register",
        json={
            "email": "not-an-email",
            "password": "securepassword",
            "full_name": "Bad Email",
        },
    )
    assert response.status_code == 422


async def test_register_short_password(pg_client):
    """POST /register with short password returns 422."""
    response = await pg_client.post(
        "/api/v1/auth/register",
        json={
            "email": "short@example.com",
            "password": "short",
            "full_name": "Short PW",
        },
    )
    assert response.status_code == 422


async def test_login_success(pg_client):
    """POST /login returns tokens in envelope."""
    await pg_client.post(
        "/api/v1/auth/register",
        json={
            "email": "login@example.com",
            "password": "securepassword",
            "full_name": "Login User",
        },
    )
    response = await pg_client.post(
        "/api/v1/auth/login",
        json={"email": "login@example.com", "password": "securepassword"},
    )
    assert response.status_code == 200
    body = response.json()
    assert body["data"]["access_token"]
    assert body["data"]["refresh_token"]
    assert body["data"]["token_type"] == "bearer"


async def test_login_bad_credentials(pg_client):
    """POST /login with wrong password returns 401."""
    await pg_client.post(
        "/api/v1/auth/register",
        json={
            "email": "bad@example.com",
            "password": "securepassword",
            "full_name": "Bad Creds",
        },
    )
    response = await pg_client.post(
        "/api/v1/auth/login",
        json={"email": "bad@example.com", "password": "wrongpassword"},
    )
    assert response.status_code == 401


async def test_refresh_success(pg_client):
    """POST /refresh with valid refresh token returns new tokens."""
    await pg_client.post(
        "/api/v1/auth/register",
        json={
            "email": "refresh@example.com",
            "password": "securepassword",
            "full_name": "Refresh User",
        },
    )
    login_resp = await pg_client.post(
        "/api/v1/auth/login",
        json={"email": "refresh@example.com", "password": "securepassword"},
    )
    refresh_token = login_resp.json()["data"]["refresh_token"]

    response = await pg_client.post(
        "/api/v1/auth/refresh",
        json={"refresh_token": refresh_token},
    )
    assert response.status_code == 200
    assert response.json()["data"]["access_token"]


async def test_refresh_invalid_token(pg_client):
    """POST /refresh with invalid token returns 401."""
    response = await pg_client.post(
        "/api/v1/auth/refresh",
        json={"refresh_token": "garbage"},
    )
    assert response.status_code == 401


async def test_me_authenticated(pg_client):
    """GET /me with valid token returns user data."""
    await pg_client.post(
        "/api/v1/auth/register",
        json={
            "email": "me@example.com",
            "password": "securepassword",
            "full_name": "Me User",
        },
    )
    login_resp = await pg_client.post(
        "/api/v1/auth/login",
        json={"email": "me@example.com", "password": "securepassword"},
    )
    access_token = login_resp.json()["data"]["access_token"]

    response = await pg_client.get(
        "/api/v1/auth/me",
        headers={"Authorization": f"Bearer {access_token}"},
    )
    assert response.status_code == 200
    assert response.json()["data"]["email"] == "me@example.com"


async def test_me_unauthenticated(pg_client):
    """GET /me without token returns 401."""
    response = await pg_client.get("/api/v1/auth/me")
    assert response.status_code == 401


async def test_response_envelope_structure(pg_client):
    """Responses follow the { data, meta, errors } envelope."""
    response = await pg_client.post(
        "/api/v1/auth/register",
        json={
            "email": "envelope@example.com",
            "password": "securepassword",
            "full_name": "Envelope User",
        },
    )
    body = response.json()
    assert "data" in body
    assert "meta" in body
    assert "errors" in body


async def test_update_profile_full_name(pg_client):
    """PATCH /me updates the user's full name."""
    await pg_client.post(
        "/api/v1/auth/register",
        json={
            "email": "update@example.com",
            "password": "securepassword",
            "full_name": "Original Name",
        },
    )
    login_resp = await pg_client.post(
        "/api/v1/auth/login",
        json={"email": "update@example.com", "password": "securepassword"},
    )
    access_token = login_resp.json()["data"]["access_token"]

    response = await pg_client.patch(
        "/api/v1/auth/me",
        json={"full_name": "Updated Name"},
        headers={"Authorization": f"Bearer {access_token}"},
    )
    assert response.status_code == 200
    assert response.json()["data"]["full_name"] == "Updated Name"
    assert response.json()["data"]["email"] == "update@example.com"


async def test_update_profile_password(pg_client):
    """PATCH /me updates the password; old password no longer works."""
    await pg_client.post(
        "/api/v1/auth/register",
        json={
            "email": "pwchange@example.com",
            "password": "oldpassword1",
            "full_name": "PW User",
        },
    )
    login_resp = await pg_client.post(
        "/api/v1/auth/login",
        json={"email": "pwchange@example.com", "password": "oldpassword1"},
    )
    access_token = login_resp.json()["data"]["access_token"]

    response = await pg_client.patch(
        "/api/v1/auth/me",
        json={"password": "newpassword1"},
        headers={"Authorization": f"Bearer {access_token}"},
    )
    assert response.status_code == 200

    # Old password should fail
    old_login = await pg_client.post(
        "/api/v1/auth/login",
        json={"email": "pwchange@example.com", "password": "oldpassword1"},
    )
    assert old_login.status_code == 401

    # New password should work
    new_login = await pg_client.post(
        "/api/v1/auth/login",
        json={"email": "pwchange@example.com", "password": "newpassword1"},
    )
    assert new_login.status_code == 200


async def test_update_profile_unauthenticated(pg_client):
    """PATCH /me without token returns 401."""
    response = await pg_client.patch(
        "/api/v1/auth/me",
        json={"full_name": "Hacker"},
    )
    assert response.status_code == 401


async def test_update_profile_short_password(pg_client):
    """PATCH /me with short password returns 422."""
    await pg_client.post(
        "/api/v1/auth/register",
        json={
            "email": "shortpw@example.com",
            "password": "securepassword",
            "full_name": "Short PW",
        },
    )
    login_resp = await pg_client.post(
        "/api/v1/auth/login",
        json={"email": "shortpw@example.com", "password": "securepassword"},
    )
    access_token = login_resp.json()["data"]["access_token"]

    response = await pg_client.patch(
        "/api/v1/auth/me",
        json={"password": "short"},
        headers={"Authorization": f"Bearer {access_token}"},
    )
    assert response.status_code == 422


async def test_full_auth_flow(pg_client):
    """Full flow: register -> login -> access /me -> refresh -> access /me."""
    # Register
    reg_resp = await pg_client.post(
        "/api/v1/auth/register",
        json={
            "email": "flow@example.com",
            "password": "securepassword",
            "full_name": "Flow User",
        },
    )
    assert reg_resp.status_code == 201

    # Login
    login_resp = await pg_client.post(
        "/api/v1/auth/login",
        json={"email": "flow@example.com", "password": "securepassword"},
    )
    tokens = login_resp.json()["data"]

    # Access /me
    me_resp = await pg_client.get(
        "/api/v1/auth/me",
        headers={"Authorization": f"Bearer {tokens['access_token']}"},
    )
    assert me_resp.status_code == 200
    assert me_resp.json()["data"]["email"] == "flow@example.com"

    # Refresh
    refresh_resp = await pg_client.post(
        "/api/v1/auth/refresh",
        json={"refresh_token": tokens["refresh_token"]},
    )
    new_tokens = refresh_resp.json()["data"]
    assert new_tokens["access_token"]
    assert new_tokens["refresh_token"]

    # Access /me with new token
    me_resp2 = await pg_client.get(
        "/api/v1/auth/me",
        headers={"Authorization": f"Bearer {new_tokens['access_token']}"},
    )
    assert me_resp2.status_code == 200
