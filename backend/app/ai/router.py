"""
AI router: technical signals, sentiment, backtesting, market overview.
"""
import logging
from datetime import date
from typing import Optional

import yfinance as yf
from fastapi import APIRouter, Depends, HTTPException, Query

from app.ai.backtesting import run_backtest, STRATEGIES
from app.ai.sentiment import analyze_news_sentiment, get_overall_market_sentiment
from app.ai.signals import generate_signal
from app.auth.models import User
from app.core.redis_client import get_redis, get_cache, set_cache, CacheKeys
from app.core.security import get_current_active_user

logger = logging.getLogger(__name__)
router = APIRouter()


@router.get("/signals/{symbol}")
async def get_signals(symbol: str, current_user: User = Depends(get_current_active_user), redis=Depends(get_redis)):
    symbol = symbol.upper()
    cache_key = CacheKeys.ai_signals(symbol)
    cached = await get_cache(redis, cache_key)
    if cached:
        return cached
    try:
        hist = yf.Ticker(symbol).history(period="1y", interval="1d")
        if hist is None or len(hist) < 20:
            raise HTTPException(status_code=404, detail=f"Insufficient data for {symbol}")
        result = generate_signal(symbol, hist)
        response = {"symbol": result.symbol, "signal": result.signal, "signal_label": result.signal_label, "signal_color": result.signal_color, "confidence": result.confidence, "score": result.score, "current_price": result.current_price, "rsi": result.rsi, "macd": result.macd, "sma_50": result.sma_50, "sma_200": result.sma_200, "bollinger_position": result.bollinger_position, "volatility_score": result.volatility_score, "support_level": result.support_level, "resistance_level": result.resistance_level, "indicators": result.indicators, "reasoning": result.reasoning}
        await set_cache(redis, cache_key, response, ttl=300)
        return response
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Signal generation failed for {symbol}: {e}")
        raise HTTPException(status_code=500, detail=f"Signal generation failed: {str(e)}")


@router.get("/sentiment/{symbol}")
async def get_sentiment(symbol: str, current_user: User = Depends(get_current_active_user), redis=Depends(get_redis)):
    symbol = symbol.upper()
    cache_key = f"sentiment:{symbol}"
    cached = await get_cache(redis, cache_key)
    if cached:
        return cached
    try:
        news = yf.Ticker(symbol).news or []
        news_items = [{"title": item.get("title", ""), "summary": item.get("summary", "")} for item in news[:15]]
        result = analyze_news_sentiment(news_items)
        await set_cache(redis, cache_key, result, ttl=600)
        return result
    except Exception as e:
        logger.error(f"Sentiment failed for {symbol}: {e}")
        return {"symbol": symbol, "sentiment_score": 0.0, "label": "Neutral", "article_scores": [], "error": str(e)}


@router.get("/backtest")
async def backtest(symbol: str = Query(...), strategy: str = Query("sma_crossover"), start_date: str = Query("2022-01-01"), end_date: Optional[str] = Query(None), capital: float = Query(10000.0, ge=100), fast_period: Optional[int] = Query(None), slow_period: Optional[int] = Query(None), oversold: Optional[float] = Query(None), overbought: Optional[float] = Query(None), current_user: User = Depends(get_current_active_user)):
    if strategy not in STRATEGIES:
        raise HTTPException(status_code=400, detail=f"Invalid strategy. Choose from: {list(STRATEGIES.keys())}")
    params = {}
    if fast_period: params["fast_period"] = fast_period
    if slow_period: params["slow_period"] = slow_period
    if oversold: params["oversold"] = oversold
    if overbought: params["overbought"] = overbought
    result = run_backtest(symbol=symbol.upper(), strategy_name=strategy, start_date=start_date, end_date=end_date or date.today().isoformat(), initial_capital=capital, strategy_params=params)
    if result.error:
        raise HTTPException(status_code=400, detail=result.error)
    return {"symbol": result.symbol, "strategy": result.strategy, "start_date": result.start_date, "end_date": result.end_date, "initial_capital": result.initial_capital, "final_value": result.final_value, "total_return": result.total_return, "total_return_pct": result.total_return_pct, "sharpe_ratio": result.sharpe_ratio, "max_drawdown": result.max_drawdown, "max_drawdown_pct": result.max_drawdown_pct, "win_rate": result.win_rate, "total_trades": result.total_trades, "winning_trades": result.winning_trades, "losing_trades": result.losing_trades, "best_trade_pct": result.best_trade_pct, "worst_trade_pct": result.worst_trade_pct, "equity_curve": result.equity_curve, "trades": result.trades[-50:]}


@router.post("/backtest")
async def backtest_post(body: dict, current_user: User = Depends(get_current_active_user)):
    strategy = body.get("strategy", "sma_crossover")
    if strategy not in STRATEGIES:
        raise HTTPException(status_code=400, detail=f"Invalid strategy: {strategy}")
    params = {k: body[k] for k in ["fast_period", "slow_period", "oversold", "overbought"] if body.get(k)}
    result = run_backtest(symbol=body.get("symbol", "AAPL").upper(), strategy_name=strategy, start_date=body.get("start_date", "2022-01-01"), end_date=body.get("end_date") or date.today().isoformat(), initial_capital=float(body.get("capital", 10000)), strategy_params=params)
    if result.error:
        raise HTTPException(status_code=400, detail=result.error)
    return {"symbol": result.symbol, "strategy": result.strategy, "total_return_pct": result.total_return_pct, "final_value": result.final_value, "sharpe_ratio": result.sharpe_ratio, "win_rate": result.win_rate, "total_trades": result.total_trades, "equity_curve": result.equity_curve, "trades": result.trades[-50:]}


@router.get("/market-overview")
async def market_overview(current_user: User = Depends(get_current_active_user), redis=Depends(get_redis)):
    cache_key = "ai:market_overview"
    cached = await get_cache(redis, cache_key)
    if cached:
        return cached
    OVERVIEW_SYMBOLS = ["AAPL", "MSFT", "GOOGL", "AMZN", "NVDA", "TSLA", "META", "JPM", "V", "BRK-B"]
    signals = []
    for sym in OVERVIEW_SYMBOLS:
        try:
            hist = yf.Ticker(sym).history(period="3mo", interval="1d")
            if hist is not None and len(hist) >= 20:
                r = generate_signal(sym, hist)
                signals.append({"symbol": sym, "signal": r.signal, "signal_label": r.signal_label, "signal_color": r.signal_color, "confidence": r.confidence, "rsi": r.rsi, "current_price": r.current_price})
        except Exception as e:
            logger.warning(f"Could not get signal for {sym}: {e}")
    response = {"signals": signals, "count": len(signals)}
    await set_cache(redis, cache_key, response, ttl=300)
    return response
