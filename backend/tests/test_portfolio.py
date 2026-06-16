"""
Test portfolio routes.
"""
import pytest
from httpx import AsyncClient

pytestmark = pytest.mark.asyncio

async def test_get_portfolio_empty(client: AsyncClient, auth_headers):
    response = await client.get("/api/portfolio", headers=auth_headers)
    assert response.status_code == 200
    data = response.json()
    assert "holdings" in data
    assert "summary" in data
    assert len(data["holdings"]) == 0
    assert data["summary"]["cash_balance"] == 100000.0

async def test_get_portfolio_history(client: AsyncClient, auth_headers):
    response = await client.get("/api/portfolio/history", headers=auth_headers)
    assert response.status_code == 200
    assert isinstance(response.json(), list)
    assert len(response.json()) > 0

async def test_get_analytics(client: AsyncClient, auth_headers):
    response = await client.get("/api/portfolio/analytics", headers=auth_headers)
    assert response.status_code == 200
    data = response.json()
    assert "win_rate" in data
    assert "sector_allocation" in data
