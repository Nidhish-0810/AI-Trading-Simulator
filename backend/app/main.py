"""
TradeAI — FastAPI Application Entry Point
"""
import asyncio
import logging
from contextlib import asynccontextmanager
from typing import AsyncGenerator

from fastapi import FastAPI, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded

from app.core.config import settings
from app.core.database import create_tables
from app.core.redis_client import get_redis_pool, close_redis_pool
from app.core.exceptions import (
    NotFoundError, UnauthorizedError, InsufficientFundsError,
    InsufficientSharesError, InvalidOrderError
)

# ─── Import Routers ───────────────────────────────────────────────────────────
from app.auth.router import router as auth_router
from app.market.router import router as market_router
from app.trading.router import router as trading_router
from app.portfolio.router import router as portfolio_router
from app.ai.router import router as ai_router
from app.notifications.router import router as notifications_router
from app.leaderboard.router import router as leaderboard_router
from app.websocket.router import router as websocket_router

logger = logging.getLogger(__name__)

# ─── Rate Limiter ─────────────────────────────────────────────────────────────
limiter = Limiter(key_func=get_remote_address)


# ─── Lifespan ─────────────────────────────────────────────────────────────────
@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator:
    """Application lifespan: startup and shutdown events."""
    # Startup
    logger.info("🚀 Starting TradeAI backend...")
    await create_tables()
    await get_redis_pool()
    logger.info("✅ Database tables created")
    logger.info("✅ Redis connection established")
    logger.info(f"✅ TradeAI running in {settings.ENVIRONMENT} mode")

    yield

    # Shutdown
    logger.info("🛑 Shutting down TradeAI backend...")
    await close_redis_pool()
    logger.info("✅ Redis connection closed")


# ─── FastAPI App ──────────────────────────────────────────────────────────────
app = FastAPI(
    title="TradeAI — AI-Powered Stock Trading Simulator",
    description="""
## TradeAI REST API

A production-grade stock trading simulator with real market data, AI signals, 
advanced order execution, portfolio analytics, and gamification.

### Features
- 🔐 JWT Authentication (access + refresh tokens)
- 📊 Real-time market data via yfinance
- ⚡ WebSocket price feeds
- 🤖 AI trading signals (RSI, MACD, Bollinger Bands)
- 📈 Advanced portfolio analytics (Sharpe, Beta, Alpha, Drawdown)
- 🎮 Leaderboard + Achievements

### Authentication
All protected endpoints require `Authorization: Bearer <access_token>` header.
Get your token via `POST /api/auth/login`.
    """,
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json",
    lifespan=lifespan,
)

# ─── Rate Limiting ────────────────────────────────────────────────────────────
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

# ─── CORS ─────────────────────────────────────────────────────────────────────
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ─── Exception Handlers ───────────────────────────────────────────────────────
@app.exception_handler(NotFoundError)
async def not_found_handler(request: Request, exc: NotFoundError) -> JSONResponse:
    return JSONResponse(
        status_code=status.HTTP_404_NOT_FOUND,
        content={"detail": str(exc), "error": "NOT_FOUND"}
    )


@app.exception_handler(UnauthorizedError)
async def unauthorized_handler(request: Request, exc: UnauthorizedError) -> JSONResponse:
    return JSONResponse(
        status_code=status.HTTP_401_UNAUTHORIZED,
        content={"detail": str(exc), "error": "UNAUTHORIZED"}
    )


@app.exception_handler(InsufficientFundsError)
async def insufficient_funds_handler(request: Request, exc: InsufficientFundsError) -> JSONResponse:
    return JSONResponse(
        status_code=status.HTTP_400_BAD_REQUEST,
        content={"detail": str(exc), "error": "INSUFFICIENT_FUNDS"}
    )


@app.exception_handler(InsufficientSharesError)
async def insufficient_shares_handler(request: Request, exc: InsufficientSharesError) -> JSONResponse:
    return JSONResponse(
        status_code=status.HTTP_400_BAD_REQUEST,
        content={"detail": str(exc), "error": "INSUFFICIENT_SHARES"}
    )


@app.exception_handler(InvalidOrderError)
async def invalid_order_handler(request: Request, exc: InvalidOrderError) -> JSONResponse:
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content={"detail": str(exc), "error": "INVALID_ORDER"}
    )


@app.exception_handler(Exception)
async def generic_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    logger.error(f"Unhandled exception: {exc}", exc_info=True)
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={"detail": "Internal server error", "error": "SERVER_ERROR"}
    )


# ─── Include Routers ─────────────────────────────────────────────────────────
app.include_router(auth_router, prefix="/api/auth", tags=["Authentication"])
app.include_router(market_router, prefix="/api/market", tags=["Market Data"])
app.include_router(trading_router, prefix="/api/trading", tags=["Trading"])
app.include_router(portfolio_router, prefix="/api/portfolio", tags=["Portfolio"])
app.include_router(ai_router, prefix="/api/ai", tags=["AI & Analytics"])
app.include_router(notifications_router, prefix="/api/notifications", tags=["Notifications"])
app.include_router(leaderboard_router, prefix="/api", tags=["Leaderboard & Social"])
app.include_router(websocket_router, tags=["WebSocket"])


# ─── Health Check ────────────────────────────────────────────────────────────
@app.get("/health", tags=["Health"])
async def health_check() -> dict:
    """Health check endpoint for load balancers and monitoring."""
    return {
        "status": "healthy",
        "service": "tradeai-backend",
        "version": "1.0.0",
        "environment": settings.ENVIRONMENT,
    }


@app.get("/", tags=["Root"])
async def root() -> dict:
    """Root endpoint — redirect to docs."""
    return {
        "message": "Welcome to TradeAI API",
        "docs": "/docs",
        "health": "/health",
        "version": "1.0.0",
    }
