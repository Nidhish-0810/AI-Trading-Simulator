"""
Test trading engine routes.
"""
import pytest
from httpx import AsyncClient

pytestmark = pytest.mark.asyncio

async def test_place_market_order_insufficient_funds(client: AsyncClient, auth_headers):
    response = await client.post(
        "/api/trading/order",
        headers=auth_headers,
        json={
            "symbol": "AAPL",
            "order_type": "market",
            "side": "buy",
            "quantity": 1000000.0  # Too large for default 100k balance
        }
    )
    assert response.status_code == 400
    assert "INSUFFICIENT_FUNDS" in response.json().get("error", "")

async def test_place_limit_order(client: AsyncClient, auth_headers):
    response = await client.post(
        "/api/trading/order",
        headers=auth_headers,
        json={
            "symbol": "AAPL",
            "order_type": "limit",
            "side": "buy",
            "quantity": 10,
            "price": 100.0
        }
    )
    assert response.status_code == 201
    data = response.json()
    assert data["status"] == "pending"
    assert data["order_type"] == "limit"

async def test_get_orders(client: AsyncClient, auth_headers):
    response = await client.get("/api/trading/orders", headers=auth_headers)
    assert response.status_code == 200
    assert isinstance(response.json(), list)

async def test_cancel_order(client: AsyncClient, auth_headers):
    # First create an order
    order_res = await client.post(
        "/api/trading/order",
        headers=auth_headers,
        json={
            "symbol": "MSFT",
            "order_type": "limit",
            "side": "buy",
            "quantity": 5,
            "price": 200.0
        }
    )
    order_id = order_res.json().get("id")

    # Now cancel it
    cancel_res = await client.delete(f"/api/trading/orders/{order_id}", headers=auth_headers)
    assert cancel_res.status_code == 200

    # Verify status
    get_res = await client.get(f"/api/trading/orders/{order_id}", headers=auth_headers)
    assert get_res.json()["status"] == "cancelled"
