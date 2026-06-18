"""
Simple, robust auth tests.
"""
import pytest
from httpx import AsyncClient

pytestmark = pytest.mark.asyncio


async def test_register_user(client: AsyncClient):
    response = await client.post(
        "/api/auth/register",
        json={
            "email": "newuser@test.com",
            "username": "newuser",
            "password": "Password123",
            "full_name": "New User",
        },
    )
    assert response.status_code == 201, response.text
    data = response.json()
    # Accept either flat or nested user object
    user = data.get("user", data)
    assert user.get("email") == "newuser@test.com"
    assert "id" in user


async def test_register_duplicate_email(client: AsyncClient, test_user):
    response = await client.post(
        "/api/auth/register",
        json={
            "email": "test@tradeai.com",  # same as test_user
            "username": "another",
            "password": "Password123",
        },
    )
    assert response.status_code == 409, response.text


async def test_login_success(client: AsyncClient, test_user):
    response = await client.post(
        "/api/auth/login",
        json={"email": "test@tradeai.com", "password": "TestPass123"},
    )
    assert response.status_code == 200, response.text
    data = response.json()
    assert "access_token" in data
    assert "refresh_token" in data


async def test_login_invalid_password(client: AsyncClient, test_user):
    response = await client.post(
        "/api/auth/login",
        json={"email": "test@tradeai.com", "password": "wrongpassword"},
    )
    assert response.status_code == 401, response.text


async def test_get_me(client: AsyncClient, auth_headers):
    response = await client.get("/api/auth/me", headers=auth_headers)
    assert response.status_code == 200, response.text
    assert response.json()["email"] == "test@tradeai.com"
