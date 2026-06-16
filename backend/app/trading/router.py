"""
Trading router: order placement, management, trade history, order book.
"""
import logging
import uuid
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.exceptions import InsufficientFundsError, InsufficientSharesError, InvalidOrderError, NotFoundError
from app.core.redis_client import get_redis
from app.core.security import get_current_active_user
from app.trading import service as trading_service
from app.trading.schemas import CreateOrder, OrderBook, OrderResponse, TradeResponse

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/trading", tags=["Trading"])


@router.post("/order", response_model=OrderResponse, status_code=status.HTTP_201_CREATED)
async def place_order(schema: CreateOrder, current_user=Depends(get_current_active_user), db: AsyncSession = Depends(get_db), redis=Depends(get_redis)) -> OrderResponse:
    try:
        order = await trading_service.place_order(db, redis, current_user, schema)
        return OrderResponse.model_validate(order)
    except (InsufficientFundsError, InsufficientSharesError, InvalidOrderError) as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=exc.message) from exc
    except Exception as exc:
        logger.error("Unexpected error placing order: %s", exc, exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to place order.") from exc


@router.get("/orders", response_model=List[OrderResponse])
async def list_orders(status_filter: Optional[str] = Query(None, alias="status"), symbol: Optional[str] = Query(None), skip: int = Query(0, ge=0), limit: int = Query(50, ge=1, le=200), current_user=Depends(get_current_active_user), db: AsyncSession = Depends(get_db)) -> List[OrderResponse]:
    orders = await trading_service.get_user_orders(db, user_id=current_user.id, status_filter=status_filter, symbol_filter=symbol, skip=skip, limit=limit)
    return [OrderResponse.model_validate(o) for o in orders]


@router.get("/orders/{order_id}", response_model=OrderResponse)
async def get_order(order_id: uuid.UUID, current_user=Depends(get_current_active_user), db: AsyncSession = Depends(get_db)) -> OrderResponse:
    order = await trading_service.get_order_by_id(db, current_user.id, order_id)
    if order is None:
        raise HTTPException(status_code=404, detail=f"Order '{order_id}' not found.")
    return OrderResponse.model_validate(order)


@router.delete("/orders/{order_id}", status_code=200)
async def cancel_order(order_id: uuid.UUID, current_user=Depends(get_current_active_user), db: AsyncSession = Depends(get_db)) -> Dict[str, Any]:
    try:
        order = await trading_service.cancel_user_order(db, current_user.id, order_id)
        return {"message": "Order cancelled.", "order_id": str(order.id)}
    except NotFoundError as exc:
        raise HTTPException(status_code=404, detail=exc.message)
    except InvalidOrderError as exc:
        raise HTTPException(status_code=400, detail=exc.message)


@router.get("/trades", response_model=List[TradeResponse])
async def list_trades(symbol: Optional[str] = Query(None), skip: int = Query(0, ge=0), limit: int = Query(50, ge=1, le=200), current_user=Depends(get_current_active_user), db: AsyncSession = Depends(get_db)) -> List[TradeResponse]:
    trades = await trading_service.get_user_trades(db, current_user.id, symbol_filter=symbol, skip=skip, limit=limit)
    return [TradeResponse.model_validate(t) for t in trades]


@router.get("/orderbook/{symbol}", response_model=OrderBook)
async def get_order_book(symbol: str, depth: int = Query(10, ge=1, le=50), current_user=Depends(get_current_active_user), db: AsyncSession = Depends(get_db)) -> OrderBook:
    return await trading_service.get_virtual_order_book(db, symbol.upper(), depth)
