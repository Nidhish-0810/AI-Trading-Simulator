"""
AI router: technical signals, sentiment, backtesting, market overview.
"""
import logging
from datetime import date
from typing import Optional

import yfinance as yf
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.ai.backtesting import run_backtest, STRATEGIES
from app.ai.sentiment import analyze_news_sentiment, get_overall_market_sentiment
from app.ai.signals import generate_signal
from app.auth.models import User
from app.core.database import get_db
from app.core.redis_client import Redis, get_redis, get_cache, set_cache, CacheKeys
from app.core.security import get_current_active_user

logger = logging.getLogger(__name__)
router = APIRouter()


@router.get("/signals/{symbol}", summary="Get AI trading signals for a stock")
async def get_signals(
    symbol: str,
    current_user: User = Depends(get_current_active_user),
    redis: Redis = Depends(get_redis),
):
    """
    Generate AI trading signals using technical analysis.

    Returns RSI, MACD, SMA crossovers, Bollinger Bands combined into
    a single signal: STRONG_BUY, BUY, NEUTRAL, SELL, or STRONG_SELL.
    """
    symbol = symbol.upper()
    cache_key = CacheKeys.ai_signals(symbol)

    cached = await get_cache(redis, cache_key)
    if cached:
        return cached

    try:
        ticker = yf.Ticker(symbol)
        hist = ticker.history(period="1y", interval="1d")

        if hist is None or len(hist) < 20:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Insufficient data for {symbol}"
            )

        result = generate_signal(symbol, hist)
        response = {
            "symbol": result.symbol,
            "signal": result.signal,
            "signal_label": result.signal_label,
            "signal_color": result.signal_color,
            "confidence": result.confidence,
            "score": result.score,
            "current_price": result.current_price,
            "rsi": result.rsi,
            "macd": result.macd,
            "sma_50": result.sma_50,
            "sma_200": result.sma_200,
            "bollinger_position": result.bollinger_position,
            "volatility_score": result.volatility_score,
            "support_level": result.support_level,
            "resistance_level": result.resistance_level,
            "indicators": result.indicators,
            "reasoning": result.reasoning,
        }

        await set_cache(redis, cache_key, response, ttl=300)
        return response

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Signal generation failed for {symbol}: {e}")
        raise HTTPException(status_code=500, detail=f"Signal generation failed: {str(e)}")


@router.get("/sentiment/{symbol}", summary="Get news sentiment for a stock")
async def get_sentiment(
    symbol: str,
    current_user: User = Depends(get_current_active_user),
    redis: Redis = Depends(get_redis),
):
    """
    Analyze news sentiment for a stock using keyword-based NLP.
    Returns overall sentiment score and headline-level breakdown.
    """
    symbol = symbol.upper()
    cache_key = f"sentiment:{symbol}"

    cached = await get_cache(redis, cache_key)
    if cached:
        return cached

    try:
        ticker = yf.Ticker(symbol)
        news = ticker.news or []

        news_items = []
        for item in news[:15]:
            news_items.append({
                "title": item.get("title", ""),
                "publisher": item.get("publisher", ""),
                "link": item.get("link", ""),
                "published": item.get("providerPublishTime", 0),
            })

        result = analyze_news_sentiment(news_items)
        await set_cache(redis, cache_key, result, ttl=600)
        return result

    except Exception as e:
        logger.error(f"Sentiment analysis failed for {symbol}: {e}")
        return {
            "symbol": symbol,
            "score": 0.0,
            "label": "Neutral",
            "news_count": 0,
            "scored_news": [],
            "error": str(e)
        }


@router.get("/backtest", summary="Run a strategy backtest (GET)")
async def backtest(
    symbol: str = Query(..., description="Stock ticker symbol"),
    strategy: str = Query("sma_crossover", description="Strategy: sma_crossover, rsi, macd, bollinger"),
    start_date: str = Query("2022-01-01", description="Start date (YYYY-MM-DD)"),
    end_date: Optional[str] = Query(None, description="End date (YYYY-MM-DD, defaults to today)"),
    capital: float = Query(10000.0, description="Starting capital in USD", ge=100),
    fast_period: Optional[int] = Query(None, description="SMA fast period (SMA strategy)"),
    slow_period: Optional[int] = Query(None, description="SMA slow period (SMA strategy)"),
    oversold: Optional[float] = Query(None, description="RSI oversold level"),
    overbought: Optional[float] = Query(None, description="RSI overbought level"),
    current_user: User = Depends(get_current_active_user),
):
    """
    Run a historical backtest for the given symbol and strategy.

    Available strategies:
    - **sma_crossover**: Fast SMA crosses above/below slow SMA
    - **rsi**: Buy oversold (<30), sell overbought (>70)
    - **macd**: Trade on MACD/signal line crossovers
    - **bollinger**: Mean reversion on band touches
    """
    if strategy not in STRATEGIES:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid strategy. Choose from: {list(STRATEGIES.keys())}"
        )

    params = {}
    if strategy == "sma_crossover":
        if fast_period:
            params["fast_period"] = fast_period
        if slow_period:
            params["slow_period"] = slow_period
    elif strategy == "rsi":
        if oversold:
            params["oversold"] = oversold
        if overbought:
            params["overbought"] = overbought

    result = run_backtest(
        symbol=symbol.upper(),
        strategy_name=strategy,
        start_date=start_date,
        end_date=end_date or date.today().isoformat(),
        initial_capital=capital,
        strategy_params=params,
    )

    if result.error:
        raise HTTPException(status_code=400, detail=result.error)

    return {
        "symbol": result.symbol,
        "strategy": result.strategy,
        "start_date": result.start_date,
        "end_date": result.end_date,
        "initial_capital": result.initial_capital,
        "final_value": result.final_value,
        "total_return": result.total_return,
        "total_return_pct": result.total_return_pct,
        "sharpe_ratio": result.sharpe_ratio,
        "max_drawdown": result.max_drawdown,
        "max_drawdown_pct": result.max_drawdown_pct,
        "win_rate": result.win_rate,
        "total_trades": result.total_trades,
        "winning_trades": result.winning_trades,
        "losing_trades": result.losing_trades,
        "best_trade_pct": result.best_trade_pct,
        "worst_trade_pct": result.worst_trade_pct,
        "equity_curve": result.equity_curve,
        "trades": result.trades[-50:],
    }


@router.post("/backtest", summary="Run a strategy backtest (POST)")
async def backtest_post(
    body: dict,
    current_user: User = Depends(get_current_active_user),
):
    """
    POST version of backtest — accepts JSON body:
    { symbol, strategy, start_date, end_date, capital, fast_period, slow_period, oversold, overbought }
    """
    strategy = body.get("strategy", "sma_crossover")
    if strategy not in STRATEGIES:
        raise HTTPException(status_code=400, detail=f"Invalid strategy: {strategy}")

    params = {}
    if body.get("fast_period"): params["fast_period"] = body["fast_period"]
    if body.get("slow_period"): params["slow_period"] = body["slow_period"]
    if body.get("oversold"): params["oversold"] = body["oversold"]
    if body.get("overbought"): params["overbought"] = body["overbought"]

    result = run_backtest(
        symbol=body.get("symbol", "AAPL").upper(),
        strategy_name=strategy,
        start_date=body.get("start_date", "2022-01-01"),
        end_date=body.get("end_date") or date.today().isoformat(),
        initial_capital=float(body.get("capital", 10000)),
        strategy_params=params,
    )

    if result.error:
        raise HTTPException(status_code=400, detail=result.error)

    return {
        "symbol": result.symbol,
        "strategy": result.strategy,
        "start_date": result.start_date,
        "end_date": result.end_date,
        "initial_capital": result.initial_capital,
        "final_value": result.final_value,
        "total_return": result.total_return,
        "total_return_pct": result.total_return_pct,
        "sharpe_ratio": result.sharpe_ratio,
        "max_drawdown": result.max_drawdown,
        "max_drawdown_pct": result.max_drawdown_pct,
        "win_rate": result.win_rate,
        "total_trades": result.total_trades,
        "winning_trades": result.winning_trades,
        "losing_trades": result.losing_trades,
        "best_trade_pct": result.best_trade_pct,
        "worst_trade_pct": result.worst_trade_pct,
        "equity_curve": result.equity_curve,
        "trades": result.trades[-50:],
    }


@router.get("/market-overview", summary="Get AI signals for major stocks")
async def market_overview(
    current_user: User = Depends(get_current_active_user),
    redis: Redis = Depends(get_redis),
):
    """
    Get AI signals for the top 10 major stocks for market overview widget.
    """
    cache_key = "ai:market_overview"
    cached = await get_cache(redis, cache_key)
    if cached:
        return cached

    OVERVIEW_SYMBOLS = ["AAPL", "MSFT", "GOOGL", "AMZN", "NVDA", "TSLA", "META", "JPM", "V", "BRK-B"]
    signals = []

    for sym in OVERVIEW_SYMBOLS:
        try:
            ticker = yf.Ticker(sym)
            hist = ticker.history(period="3mo", interval="1d")
            if hist is not None and len(hist) >= 20:
                result = generate_signal(sym, hist)
                signals.append({
                    "symbol": sym,
                    "signal": result.signal,
                    "signal_label": result.signal_label,
                    "signal_color": result.signal_color,
                    "confidence": result.confidence,
                    "rsi": result.rsi,
                    "current_price": result.current_price,
                })
        except Exception as e:
            logger.warning(f"Could not get signal for {sym}: {e}")

    response = {"signals": signals, "count": len(signals)}
    await set_cache(redis, cache_key, response, ttl=300)
    return response
