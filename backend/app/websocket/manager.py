"""
WebSocket connection manager.
"""
import asyncio
import json
import logging
from typing import Dict, List, Optional, Set

from fastapi import WebSocket

logger = logging.getLogger(__name__)


class ConnectionManager:
    def __init__(self):
        self._user_connections: Dict[str, WebSocket] = {}
        self._price_rooms: Dict[str, Set[WebSocket]] = {}
        self._orderbook_rooms: Dict[str, Set[WebSocket]] = {}

    async def connect_user(self, websocket: WebSocket, user_id: str) -> None:
        await websocket.accept()
        self._user_connections[user_id] = websocket
        logger.info(f"WS: User {user_id} connected")

    def disconnect_user(self, user_id: str) -> None:
        self._user_connections.pop(user_id, None)
        logger.info(f"WS: User {user_id} disconnected")

    async def connect_price_room(self, websocket: WebSocket, symbols: List[str]) -> None:
        await websocket.accept()
        for symbol in symbols:
            symbol = symbol.upper()
            if symbol not in self._price_rooms:
                self._price_rooms[symbol] = set()
            self._price_rooms[symbol].add(websocket)

    def disconnect_from_price_room(self, websocket: WebSocket, symbols: Optional[List[str]] = None) -> None:
        if symbols:
            for symbol in symbols:
                self._price_rooms.get(symbol.upper(), set()).discard(websocket)
        else:
            for room_sockets in self._price_rooms.values():
                room_sockets.discard(websocket)

    async def connect_orderbook_room(self, websocket: WebSocket, symbol: str) -> None:
        await websocket.accept()
        symbol = symbol.upper()
        if symbol not in self._orderbook_rooms:
            self._orderbook_rooms[symbol] = set()
        self._orderbook_rooms[symbol].add(websocket)

    def disconnect_from_orderbook_room(self, websocket: WebSocket, symbol: str) -> None:
        self._orderbook_rooms.get(symbol.upper(), set()).discard(websocket)

    async def send_to_user(self, user_id: str, message: dict) -> bool:
        websocket = self._user_connections.get(str(user_id))
        if websocket:
            try:
                await websocket.send_text(json.dumps(message, default=str))
                return True
            except Exception as e:
                logger.warning(f"Failed to send to user {user_id}: {e}")
                self.disconnect_user(str(user_id))
        return False

    async def broadcast_price_update(self, symbol: str, price_data: dict) -> int:
        symbol = symbol.upper()
        sockets = self._price_rooms.get(symbol, set())
        disconnected = set()
        sent = 0
        message = json.dumps({"type": "price_update", "symbol": symbol, **price_data}, default=str)
        for socket in sockets:
            try:
                await socket.send_text(message)
                sent += 1
            except Exception:
                disconnected.add(socket)
        sockets -= disconnected
        return sent

    async def broadcast_to_all(self, message: dict) -> int:
        disconnected = []
        sent = 0
        payload = json.dumps(message, default=str)
        for user_id, socket in list(self._user_connections.items()):
            try:
                await socket.send_text(payload)
                sent += 1
            except Exception:
                disconnected.append(user_id)
        for user_id in disconnected:
            self.disconnect_user(user_id)
        return sent

    async def broadcast_orderbook_update(self, symbol: str, orderbook_data: dict) -> int:
        symbol = symbol.upper()
        sockets = self._orderbook_rooms.get(symbol, set())
        disconnected = set()
        sent = 0
        message = json.dumps({"type": "orderbook_update", "symbol": symbol, **orderbook_data}, default=str)
        for socket in sockets:
            try:
                await socket.send_text(message)
                sent += 1
            except Exception:
                disconnected.add(socket)
        sockets -= disconnected
        return sent

    @property
    def connected_users_count(self) -> int:
        return len(self._user_connections)

    @property
    def subscribed_symbols(self) -> List[str]:
        return [sym for sym, sockets in self._price_rooms.items() if sockets]

    def get_stats(self) -> dict:
        return {"connected_users": self.connected_users_count, "price_rooms": len(self._price_rooms), "subscribed_symbols": self.subscribed_symbols, "orderbook_rooms": len(self._orderbook_rooms)}


manager = ConnectionManager()
