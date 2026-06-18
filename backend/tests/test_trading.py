"""
Simple, robust trading tests.
"""
import pytest
from httpx import AsyncClient

pytestmark = pytest.mark.asyncio


async def test_get_orders_empty(client: AsyncClient, auth_headers):
    response = await client.get("/api/trading/orders", headers=auth_headers)
    assert response.status_code == 200, response.text
    assert isinstance(response.json(), list)


async def test_place_limit_order(client: AsyncClient, auth_headers):
    response = await client.post(
        "/api/trading/order",
        headers=auth_headers,
        json={
            "symbol": "AAPL",
            "order_type": "limit",
            "side": "buy",
            "quantity": 10,
            "price": 100.0,
        },
    )
    assert response.status_code == 201, response.text
    data = response.json()
    assert "id" in data
    assert data["symbol"] == "AAPL"


async def test_place_insufficient_funds(client: AsyncClient, auth_headers):
    response = await client.post(
        "/api/trading/order",
        headers=auth_headers,
        json={
            "symbol": "AAPL",
            "order_type": "market",
            "side": "buy",
            "quantity": 99999999,
        },
    )
    assert response.status_code == 400, response.text


async def test_get_trades_empty(client: AsyncClient, auth_headers):
    response = await client.get("/api/trading/trades", headers=auth_headers)
    assert response.status_code == 200, response.text
    assert isinstance(response.json(), list)
