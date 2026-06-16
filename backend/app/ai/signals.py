"""
AI signal generation for stocks.
Combines multiple technical indicators into a single trading signal.
"""
import logging
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Tuple

import pandas as pd

from app.ai.indicators import (
    calculate_rsi,
    calculate_macd,
    calculate_sma,
    calculate_ema,
    calculate_bollinger_bands,
    calculate_atr,
    calculate_stochastic,
    calculate_williams_r,
    get_price_position_in_bands,
)

logger = logging.getLogger(__name__)

# ─── Signal Level Enum ────────────────────────────────────────────────────────
SIGNAL_LEVELS = {
    "STRONG_BUY": {"label": "STRONG BUY", "color": "#00d4aa", "min_score": 4},
    "BUY": {"label": "BUY", "color": "#10b981", "min_score": 2},
    "NEUTRAL": {"label": "NEUTRAL", "color": "#6b7280", "min_score": -1},
    "SELL": {"label": "SELL", "color": "#f59e0b", "min_score": -3},
    "STRONG_SELL": {"label": "STRONG SELL", "color": "#ff4757", "min_score": -100},
}


@dataclass
class IndicatorResult:
    """Individual indicator result with signal."""
    name: str
    value: float
    signal: str  # bullish | bearish | neutral
    score: int   # contribution to overall score
    description: str


@dataclass
class SignalResult:
    """Complete AI signal analysis for a stock."""
    symbol: str
    signal: str  # STRONG_BUY | BUY | NEUTRAL | SELL | STRONG_SELL
    signal_label: str
    signal_color: str
    confidence: float  # 0-100
    score: int
    indicators: Dict[str, dict] = field(default_factory=dict)
    reasoning: List[str] = field(default_factory=list)
    volatility_score: float = 0.0
    support_level: Optional[float] = None
    resistance_level: Optional[float] = None
    current_price: float = 0.0
    rsi: float = 50.0
    macd: float = 0.0
    sma_50: float = 0.0
    sma_200: float = 0.0
    bollinger_position: float = 0.0


def _score_to_signal(score: int) -> Tuple[str, str, str]:
    """
    Map a numeric score to a signal level.

    Score range: typically -6 to +6

    Returns:
        (signal_key, label, color)
    """
    if score >= 4:
        return "STRONG_BUY", "STRONG BUY", "#00d4aa"
    elif score >= 2:
        return "BUY", "BUY", "#10b981"
    elif score >= -1:
        return "NEUTRAL", "NEUTRAL", "#6b7280"
    elif score >= -3:
        return "SELL", "SELL", "#f59e0b"
    else:
        return "STRONG_SELL", "STRONG SELL", "#ff4757"


def _score_to_confidence(score: int, max_score: int = 6) -> float:
    """Convert score to confidence percentage (0-100)."""
    abs_score = abs(score)
    confidence = min(100.0, (abs_score / max_score) * 100.0)
    # Neutral = low confidence
    if abs(score) <= 1:
        confidence = max(30.0, confidence)
    return round(confidence, 1)


def generate_signal(symbol: str, history_df: pd.DataFrame) -> SignalResult:
    """
    Generate a comprehensive trading signal for a stock.

    Algorithm:
    1. Calculate all technical indicators
    2. Score each indicator (-2 to +2 contribution)
    3. Sum scores → map to signal level
    4. Generate human-readable reasoning

    Args:
        symbol: Stock ticker
        history_df: DataFrame with columns: Open, High, Low, Close, Volume

    Returns:
        SignalResult with full analysis
    """
    if history_df is None or len(history_df) < 20:
        return SignalResult(
            symbol=symbol,
            signal="NEUTRAL",
            signal_label="NEUTRAL",
            signal_color="#6b7280",
            confidence=30.0,
            score=0,
            reasoning=["Insufficient historical data for analysis"],
        )

    close = history_df["Close"].astype(float)
    high = history_df["High"].astype(float)
    low = history_df["Low"].astype(float)
    volume = history_df["Volume"].astype(float)

    current_price = float(close.iloc[-1])
    score = 0
    reasoning = []
    indicators = {}

    # ─── RSI Analysis ─────────────────────────────────────────────────────────
    rsi = calculate_rsi(close, period=14)
    rsi_score = 0
    if rsi < 30:
        rsi_score = 2
        reasoning.append(f"RSI is oversold at {rsi:.1f} — potential bounce expected")
    elif rsi < 40:
        rsi_score = 1
        reasoning.append(f"RSI at {rsi:.1f} — mildly oversold, cautious bullish")
    elif rsi > 70:
        rsi_score = -2
        reasoning.append(f"RSI is overbought at {rsi:.1f} — potential pullback risk")
    elif rsi > 60:
        rsi_score = -1
        reasoning.append(f"RSI at {rsi:.1f} — approaching overbought territory")
    else:
        reasoning.append(f"RSI neutral at {rsi:.1f}")

    score += rsi_score
    indicators["rsi"] = {
        "value": rsi,
        "signal": "bullish" if rsi_score > 0 else ("bearish" if rsi_score < 0 else "neutral"),
        "description": f"RSI({14}): {rsi:.1f}",
    }

    # ─── MACD Analysis ────────────────────────────────────────────────────────
    macd_line, signal_line, histogram = calculate_macd(close)
    macd_score = 0

    if macd_line > signal_line:
        if histogram > 0:
            # Check if histogram is growing (increasing momentum)
            hist_series = close.ewm(span=12, adjust=False).mean() - close.ewm(span=26, adjust=False).mean()
            if len(hist_series) >= 2 and hist_series.iloc[-1] > hist_series.iloc[-2]:
                macd_score = 2
                reasoning.append("MACD bullish crossover with increasing momentum")
            else:
                macd_score = 1
                reasoning.append("MACD above signal line — bullish bias")
        else:
            macd_score = 1
            reasoning.append("MACD above signal line — bullish bias")
    elif macd_line < signal_line:
        if histogram < 0:
            macd_score = -2
            reasoning.append("MACD bearish crossover — downward momentum building")
        else:
            macd_score = -1
            reasoning.append("MACD below signal line — bearish bias")

    score += macd_score
    indicators["macd"] = {
        "value": macd_line,
        "signal_line": signal_line,
        "histogram": histogram,
        "signal": "bullish" if macd_score > 0 else ("bearish" if macd_score < 0 else "neutral"),
        "description": f"MACD: {macd_line:.3f} | Signal: {signal_line:.3f} | Hist: {histogram:.3f}",
    }

    # ─── SMA 50 Analysis ──────────────────────────────────────────────────────
    sma_50 = calculate_sma(close, 50)
    sma_50_score = 0
    if len(close) >= 50:
        if current_price > sma_50:
            sma_50_score = 1
            pct_above = ((current_price - sma_50) / sma_50) * 100
            reasoning.append(f"Price is {pct_above:.1f}% above 50-day SMA — bullish trend")
        else:
            sma_50_score = -1
            pct_below = ((sma_50 - current_price) / sma_50) * 100
            reasoning.append(f"Price is {pct_below:.1f}% below 50-day SMA — bearish pressure")

    score += sma_50_score
    indicators["sma_50"] = {
        "value": sma_50,
        "signal": "bullish" if sma_50_score > 0 else ("bearish" if sma_50_score < 0 else "neutral"),
        "description": f"SMA(50): ${sma_50:.2f} | Current: ${current_price:.2f}",
    }

    # ─── SMA 200 (Golden/Death Cross) ────────────────────────────────────────
    sma_200 = calculate_sma(close, 200)
    sma_200_score = 0
    if len(close) >= 200:
        if current_price > sma_200:
            sma_200_score = 1
            reasoning.append("Price above 200-day SMA — long-term bullish trend intact")
            if sma_50 > sma_200:
                sma_200_score = 2
                reasoning.append("Golden Cross confirmed (SMA50 > SMA200) — strong buy signal")
        else:
            sma_200_score = -1
            reasoning.append("Price below 200-day SMA — long-term bearish trend")
            if sma_50 < sma_200:
                sma_200_score = -2
                reasoning.append("Death Cross detected (SMA50 < SMA200) — strong sell signal")

    score += sma_200_score
    indicators["sma_200"] = {
        "value": sma_200,
        "signal": "bullish" if sma_200_score > 0 else ("bearish" if sma_200_score < 0 else "neutral"),
        "description": f"SMA(200): ${sma_200:.2f}",
    }

    # ─── Bollinger Bands Analysis ─────────────────────────────────────────────
    bb_upper, bb_middle, bb_lower = calculate_bollinger_bands(close)
    bb_score = 0
    bb_position = get_price_position_in_bands(current_price, bb_upper, bb_lower, bb_middle)
    band_width_pct = ((bb_upper - bb_lower) / bb_middle) * 100 if bb_middle > 0 else 0

    if current_price < bb_lower:
        bb_score = 1
        reasoning.append(f"Price broke below lower Bollinger Band (${bb_lower:.2f}) — mean reversion likely")
    elif current_price > bb_upper:
        bb_score = -1
        reasoning.append(f"Price broke above upper Bollinger Band (${bb_upper:.2f}) — potential reversal")
    elif band_width_pct < 2:
        reasoning.append("Bollinger Band squeeze detected — major move incoming")

    score += bb_score
    indicators["bollinger"] = {
        "upper": bb_upper,
        "middle": bb_middle,
        "lower": bb_lower,
        "position": bb_position,
        "band_width_pct": round(band_width_pct, 2),
        "signal": "bullish" if bb_score > 0 else ("bearish" if bb_score < 0 else "neutral"),
        "description": f"BB Upper: ${bb_upper:.2f} | Middle: ${bb_middle:.2f} | Lower: ${bb_lower:.2f}",
    }

    # ─── Stochastic Oscillator ────────────────────────────────────────────────
    stoch_k, stoch_d = calculate_stochastic(high, low, close)
    stoch_score = 0
    if stoch_k < 20 and stoch_d < 20:
        stoch_score = 1
        reasoning.append(f"Stochastic oversold ({stoch_k:.0f}) — potential buy opportunity")
    elif stoch_k > 80 and stoch_d > 80:
        stoch_score = -1
        reasoning.append(f"Stochastic overbought ({stoch_k:.0f}) — potential sell signal")

    score += stoch_score
    indicators["stochastic"] = {
        "k": stoch_k,
        "d": stoch_d,
        "signal": "bullish" if stoch_score > 0 else ("bearish" if stoch_score < 0 else "neutral"),
        "description": f"Stochastic %K: {stoch_k:.1f} | %D: {stoch_d:.1f}",
    }

    # ─── Determine Final Signal ───────────────────────────────────────────────
    signal_key, signal_label, signal_color = _score_to_signal(score)
    confidence = _score_to_confidence(score)

    # ─── Volatility Score ─────────────────────────────────────────────────────
    volatility_score = calculate_volatility_score(history_df)

    # ─── Support/Resistance ───────────────────────────────────────────────────
    support, resistance = detect_support_resistance(history_df)

    return SignalResult(
        symbol=symbol,
        signal=signal_key,
        signal_label=signal_label,
        signal_color=signal_color,
        confidence=confidence,
        score=score,
        indicators=indicators,
        reasoning=reasoning,
        volatility_score=volatility_score,
        support_level=support,
        resistance_level=resistance,
        current_price=current_price,
        rsi=rsi,
        macd=macd_line,
        sma_50=sma_50,
        sma_200=sma_200,
        bollinger_position=bb_position,
    )


def calculate_volatility_score(history_df: pd.DataFrame, period: int = 20) -> float:
    """
    Calculate a normalized volatility score (0-100).

    0 = very low volatility
    100 = extremely high volatility

    Uses annualized standard deviation of log returns.
    """
    if history_df is None or len(history_df) < period:
        return 30.0

    close = history_df["Close"].astype(float)
    log_returns = close.pct_change().dropna()

    if len(log_returns) < 2:
        return 30.0

    # Annualized volatility
    daily_vol = log_returns.std()
    annualized_vol = daily_vol * (252 ** 0.5)

    # Map to 0-100 scale
    # 10% annualized = 0, 100%+ annualized = 100
    score = min(100.0, max(0.0, (annualized_vol * 100 - 10) / 90 * 100))
    return round(float(score), 1)


def detect_support_resistance(
    history_df: pd.DataFrame,
    window: int = 20,
) -> Tuple[Optional[float], Optional[float]]:
    """
    Detect key support and resistance levels using rolling min/max.

    Args:
        history_df: OHLCV DataFrame
        window: Lookback window (days)

    Returns:
        (support_level, resistance_level)
    """
    if history_df is None or len(history_df) < window:
        return None, None

    close = history_df["Close"].astype(float)
    low = history_df["Low"].astype(float)
    high = history_df["High"].astype(float)

    # Support: recent significant low (using 20-period rolling min)
    support = float(low.rolling(window=window).min().iloc[-1])

    # Resistance: recent significant high
    resistance = float(high.rolling(window=window).max().iloc[-1])

    return round(support, 2), round(resistance, 2)
