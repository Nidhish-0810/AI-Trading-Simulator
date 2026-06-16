"""
Trading router: order placement, order management, trade history, order book.
"""

import logging
import uuid
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.exceptions import (
    InsufficientFundsError,
    InsufficientSharesError,
    InvalidOrderError,
    NotFoundError,
    UnauthorizedError,
)
from app.core.redis_client import get_redis
from app.core.security import get_current_active_user
from app.trading import service as trading_service
from app.trading.schemas import CreateOrder, OrderBook, OrderResponse, TradeResponse

logger = logging.getLogger(__name__)

router = APIRouter(tags=["Trading"])


@router.post(
    "/order",
    response_model=OrderResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Place a new trading order",
)
async def place_order(
    schema: CreateOrder,
    current_user=Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
    redis=Depends(get_redis),
) -> OrderResponse:
    """
    Place a market, limit, or stop-loss order.

    - **market**: executes immediately at current market price
    - **limit**: queued until price meets the specified limit
    - **stop_loss**: triggers when price crosses the stop price
    """
    try:
        order = await trading_service.place_order(db, redis, current_user, schema)
        return OrderResponse.model_validate(order)
    except (InsufficientFundsError, InsufficientSharesError, InvalidOrderError) as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail=exc.message
        ) from exc
    except Exception as exc:
        logger.error("Unexpected error placing order: %s", exc, exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to place order. Please try again.",
        ) from exc


@router.get(
    "/orders",
    response_model=List[OrderResponse],
    summary="List the current user's orders",
)
async def list_orders(
    status_filter: Optional[str] = Query(
        None, alias="status", description="pending | partial | filled | cancelled"
    ),
    symbol: Optional[str] = Query(None, max_length=20),
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=200),
    current_user=Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
) -> List[OrderResponse]:
    """Return orders for the authenticated user with optional filters."""
    orders = await trading_service.get_user_orders(
        db,
        user_id=current_user.id,
        status_filter=status_filter,
        symbol_filter=symbol,
        skip=skip,
        limit=limit,
    )
    return [OrderResponse.model_validate(o) for o in orders]


@router.get(
    "/orders/{order_id}",
    response_model=OrderResponse,
    summary="Get a specific order by ID",
)
async def get_order(
    order_id: uuid.UUID,
    current_user=Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
) -> OrderResponse:
    """Fetch a single order by its UUID."""
    order = await trading_service.get_order_by_id(db, current_user.id, order_id)
    if order is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Order '{order_id}' not found.",
        )
    return OrderResponse.model_validate(order)


@router.delete(
    "/orders/{order_id}",
    status_code=status.HTTP_200_OK,
    summary="Cancel a pending order",
)
async def cancel_order(
    order_id: uuid.UUID,
    current_user=Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
) -> Dict[str, Any]:
    """Cancel a PENDING or PARTIAL order. Filled/cancelled orders cannot be cancelled."""
    try:
        order = await trading_service.cancel_user_order(db, current_user.id, order_id)
        return {"message": "Order cancelled.", "order_id": str(order.id)}
    except NotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=exc.message)
    except UnauthorizedError as exc:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=exc.message)
    except InvalidOrderError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=exc.message)


@router.get(
    "/trades",
    response_model=List[TradeResponse],
    summary="Get trade execution history",
)
async def list_trades(
    symbol: Optional[str] = Query(None, max_length=20),
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=200),
    current_user=Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
) -> List[TradeResponse]:
    """Return trade history for the current user."""
    trades = await trading_service.get_user_trades(
        db, current_user.id, symbol_filter=symbol, skip=skip, limit=limit
    )
    return [TradeResponse.model_validate(t) for t in trades]


@router.get(
    "/orderbook/{symbol}",
    response_model=OrderBook,
    summary="Get the virtual order book for a symbol",
)
async def get_order_book(
    symbol: str,
    depth: int = Query(10, ge=1, le=50),
    current_user=Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
) -> OrderBook:
    """
    Return a virtual order book constructed from pending limit orders
    in the simulator database.
    """
    return await trading_service.get_virtual_order_book(db, symbol.upper(), depth)
