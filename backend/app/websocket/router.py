"""
WebSocket router: live price feeds, user notifications, order book.
"""
import asyncio
import json
import logging
from typing import List

import yfinance as yf
from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Query

from app.core.redis_client import get_redis_pool, get_cache, set_cache, CacheKeys
from app.core.security import get_user_id_from_token
from app.websocket.manager import manager

logger = logging.getLogger(__name__)
router = APIRouter()

_price_update_task = None
_tracked_symbols: set = set()


async def _price_update_loop():
    while True:
        try:
            if _tracked_symbols:
                redis = await get_redis_pool()
                for symbol in list(_tracked_symbols):
                    try:
                        cached = await get_cache(redis, CacheKeys.stock_quote(symbol))
                        if cached:
                            price_data = {"price": cached.get("price", 0), "change": cached.get("change", 0), "change_pct": cached.get("change_pct", 0)}
                        else:
                            info = yf.Ticker(symbol).fast_info
                            price = float(getattr(info, "last_price", 0) or 0)
                            prev_close = float(getattr(info, "previous_close", price) or price)
                            change = price - prev_close
                            change_pct = (change / prev_close * 100) if prev_close else 0
                            price_data = {"price": round(price, 2), "change": round(change, 2), "change_pct": round(change_pct, 2)}
                            await set_cache(redis, CacheKeys.stock_quote(symbol), {**price_data, "symbol": symbol}, ttl=60)
                        await manager.broadcast_price_update(symbol, price_data)
                    except Exception as e:
                        logger.debug(f"Price fetch error for {symbol}: {e}")
        except Exception as e:
            logger.error(f"Price update loop error: {e}")
        await asyncio.sleep(5)


@router.websocket("/ws/prices")
async def websocket_prices(websocket: WebSocket, symbols: str = Query("AAPL,MSFT,GOOGL"), token: str = Query(None)):
    global _price_update_task
    symbol_list = [s.strip().upper() for s in symbols.split(",") if s.strip()] or ["AAPL", "MSFT"]
    await manager.connect_price_room(websocket, symbol_list)
    for sym in symbol_list:
        _tracked_symbols.add(sym)
    if _price_update_task is None or _price_update_task.done():
        _price_update_task = asyncio.create_task(_price_update_loop())
    redis = await get_redis_pool()
    for symbol in symbol_list:
        cached = await get_cache(redis, CacheKeys.stock_quote(symbol))
        if cached:
            await websocket.send_text(json.dumps({"type": "price_update", "symbol": symbol, "price": cached.get("price", 0), "change": cached.get("change", 0), "change_pct": cached.get("change_pct", 0)}))
    try:
        while True:
            data = await websocket.receive_text()
            try:
                msg = json.loads(data)
                if msg.get("action") == "subscribe" and "symbols" in msg:
                    new_syms = [s.upper() for s in msg["symbols"]]
                    for sym in new_syms:
                        _tracked_symbols.add(sym)
                    await manager.connect_price_room(websocket, new_syms)
                elif msg.get("action") == "unsubscribe" and "symbols" in msg:
                    manager.disconnect_from_price_room(websocket, msg["symbols"])
            except json.JSONDecodeError:
                pass
    except WebSocketDisconnect:
        manager.disconnect_from_price_room(websocket, symbol_list)


@router.websocket("/ws/user/{user_id}")
async def websocket_user(websocket: WebSocket, user_id: str, token: str = Query(None)):
    if token:
        token_user_id = get_user_id_from_token(token)
        if not token_user_id or str(token_user_id) != user_id:
            await websocket.close(code=4001, reason="Unauthorized")
            return
    await manager.connect_user(websocket, user_id)
    await websocket.send_text(json.dumps({"type": "connected", "message": "Personal channel connected", "user_id": user_id}))
    try:
        while True:
            data = await websocket.receive_text()
            try:
                msg = json.loads(data)
                if msg.get("type") == "ping":
                    await websocket.send_text(json.dumps({"type": "pong"}))
            except json.JSONDecodeError:
                pass
    except WebSocketDisconnect:
        manager.disconnect_user(user_id)


@router.websocket("/ws/orderbook/{symbol}")
async def websocket_orderbook(websocket: WebSocket, symbol: str):
    import random
    symbol = symbol.upper()
    await manager.connect_orderbook_room(websocket, symbol)
    async def send_orderbook():
        redis = await get_redis_pool()
        cached = await get_cache(redis, CacheKeys.stock_quote(symbol))
        price = cached.get("price", 100.0) if cached else 100.0
        spread = price * 0.001
        bids = [{"price": round(price - spread - (i * price * 0.0005), 2), "size": round(random.uniform(100, 5000), 0)} for i in range(8)]
        asks = [{"price": round(price + spread + (i * price * 0.0005), 2), "size": round(random.uniform(100, 5000), 0)} for i in range(8)]
        return {"symbol": symbol, "bids": bids, "asks": asks, "spread": round(asks[0]["price"] - bids[0]["price"], 4), "mid_price": round((asks[0]["price"] + bids[0]["price"]) / 2, 2)}
    try:
        while True:
            orderbook = await send_orderbook()
            await websocket.send_text(json.dumps({"type": "orderbook_update", **orderbook}))
            await asyncio.sleep(2)
    except WebSocketDisconnect:
        manager.disconnect_from_orderbook_room(websocket, symbol)
