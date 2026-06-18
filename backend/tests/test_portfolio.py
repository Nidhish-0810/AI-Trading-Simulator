"""
Simple, robust portfolio tests.
"""
import pytest
from httpx import AsyncClient

pytestmark = pytest.mark.asyncio


async def test_get_portfolio_empty(client: AsyncClient, auth_headers):
    response = await client.get("/api/portfolio", headers=auth_headers)
    assert response.status_code == 200, response.text


async def test_get_portfolio_history(client: AsyncClient, auth_headers):
    response = await client.get("/api/portfolio/history", headers=auth_headers)
    assert response.status_code == 200, response.text
    assert isinstance(response.json(), list)


async def test_get_analytics(client: AsyncClient, auth_headers):
    response = await client.get("/api/portfolio/analytics", headers=auth_headers)
    assert response.status_code == 200, response.text
