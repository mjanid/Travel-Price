"""Integration tests for auth API endpoints."""


async def test_register_success(client):
    """POST /register returns 201 with user data in envelope."""
    response = await client.post(
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


async def test_register_duplicate_email(client):
    """POST /register with existing email returns 409."""
    payload = {
        "email": "dup@example.com",
        "password": "securepassword",
        "full_name": "First User",
    }
    await client.post("/api/v1/auth/register", json=payload)
    response = await client.post("/api/v1/auth/register", json=payload)
    assert response.status_code == 409


async def test_register_invalid_email(client):
    """POST /register with invalid email returns 422."""
    response = await client.post(
        "/api/v1/auth/register",
        json={
            "email": "not-an-email",
            "password": "securepassword",
            "full_name": "Bad Email",
        },
    )
    assert response.status_code == 422


async def test_register_short_password(client):
    """POST /register with short password returns 422."""
    response = await client.post(
        "/api/v1/auth/register",
        json={
            "email": "short@example.com",
            "password": "short",
            "full_name": "Short PW",
        },
    )
    assert response.status_code == 422


async def test_login_success(client):
    """POST /login returns tokens in envelope."""
    await client.post(
        "/api/v1/auth/register",
        json={
            "email": "login@example.com",
            "password": "securepassword",
            "full_name": "Login User",
        },
    )
    response = await client.post(
        "/api/v1/auth/login",
        json={"email": "login@example.com", "password": "securepassword"},
    )
    assert response.status_code == 200
    body = response.json()
    assert body["data"]["access_token"]
    assert body["data"]["refresh_token"]
    assert body["data"]["token_type"] == "bearer"


async def test_login_bad_credentials(client):
    """POST /login with wrong password returns 401."""
    await client.post(
        "/api/v1/auth/register",
        json={
            "email": "bad@example.com",
            "password": "securepassword",
            "full_name": "Bad Creds",
        },
    )
    response = await client.post(
        "/api/v1/auth/login",
        json={"email": "bad@example.com", "password": "wrongpassword"},
    )
    assert response.status_code == 401


async def test_refresh_success(client):
    """POST /refresh with valid refresh token returns new tokens."""
    await client.post(
        "/api/v1/auth/register",
        json={
            "email": "refresh@example.com",
            "password": "securepassword",
            "full_name": "Refresh User",
        },
    )
    login_resp = await client.post(
        "/api/v1/auth/login",
        json={"email": "refresh@example.com", "password": "securepassword"},
    )
    refresh_token = login_resp.json()["data"]["refresh_token"]

    response = await client.post(
        "/api/v1/auth/refresh",
        json={"refresh_token": refresh_token},
    )
    assert response.status_code == 200
    assert response.json()["data"]["access_token"]


async def test_refresh_invalid_token(client):
    """POST /refresh with invalid token returns 401."""
    response = await client.post(
        "/api/v1/auth/refresh",
        json={"refresh_token": "garbage"},
    )
    assert response.status_code == 401


async def test_me_authenticated(client):
    """GET /me with valid token returns user data."""
    await client.post(
        "/api/v1/auth/register",
        json={
            "email": "me@example.com",
            "password": "securepassword",
            "full_name": "Me User",
        },
    )
    login_resp = await client.post(
        "/api/v1/auth/login",
        json={"email": "me@example.com", "password": "securepassword"},
    )
    access_token = login_resp.json()["data"]["access_token"]

    response = await client.get(
        "/api/v1/auth/me",
        headers={"Authorization": f"Bearer {access_token}"},
    )
    assert response.status_code == 200
    assert response.json()["data"]["email"] == "me@example.com"


async def test_me_unauthenticated(client):
    """GET /me without token returns 401."""
    response = await client.get("/api/v1/auth/me")
    assert response.status_code == 401


async def test_response_envelope_structure(client):
    """Responses follow the { data, meta, errors } envelope."""
    response = await client.post(
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


async def test_full_auth_flow(client):
    """Full flow: register -> login -> access /me -> refresh -> access /me."""
    # Register
    reg_resp = await client.post(
        "/api/v1/auth/register",
        json={
            "email": "flow@example.com",
            "password": "securepassword",
            "full_name": "Flow User",
        },
    )
    assert reg_resp.status_code == 201

    # Login
    login_resp = await client.post(
        "/api/v1/auth/login",
        json={"email": "flow@example.com", "password": "securepassword"},
    )
    tokens = login_resp.json()["data"]

    # Access /me
    me_resp = await client.get(
        "/api/v1/auth/me",
        headers={"Authorization": f"Bearer {tokens['access_token']}"},
    )
    assert me_resp.status_code == 200
    assert me_resp.json()["data"]["email"] == "flow@example.com"

    # Refresh
    refresh_resp = await client.post(
        "/api/v1/auth/refresh",
        json={"refresh_token": tokens["refresh_token"]},
    )
    new_tokens = refresh_resp.json()["data"]
    assert new_tokens["access_token"]
    assert new_tokens["refresh_token"]

    # Access /me with new token
    me_resp2 = await client.get(
        "/api/v1/auth/me",
        headers={"Authorization": f"Bearer {new_tokens['access_token']}"},
    )
    assert me_resp2.status_code == 200
