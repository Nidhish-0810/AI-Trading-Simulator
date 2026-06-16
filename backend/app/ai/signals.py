"""
AI signals module: generate trading signals from technical indicators.
"""
import logging
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Tuple

import pandas as pd

from app.ai.indicators import (
    calculate_rsi, calculate_macd, calculate_sma, calculate_bollinger_bands,
    calculate_stochastic, get_price_position_in_bands
)

logger = logging.getLogger(__name__)


@dataclass
class SignalResult:
    symbol: str
    signal: str
    signal_label: str
    signal_color: str
    confidence: float
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
    if score >= 4: return "STRONG_BUY", "STRONG BUY", "#00d4aa"
    elif score >= 2: return "BUY", "BUY", "#10b981"
    elif score >= -1: return "NEUTRAL", "NEUTRAL", "#6b7280"
    elif score >= -3: return "SELL", "SELL", "#f59e0b"
    else: return "STRONG_SELL", "STRONG SELL", "#ff4757"


def _score_to_confidence(score: int, max_score: int = 6) -> float:
    confidence = min(100.0, (abs(score) / max_score) * 100.0)
    if abs(score) <= 1:
        confidence = max(30.0, confidence)
    return round(confidence, 1)


def generate_signal(symbol: str, history_df: pd.DataFrame) -> SignalResult:
    if history_df is None or len(history_df) < 20:
        return SignalResult(symbol=symbol, signal="NEUTRAL", signal_label="NEUTRAL", signal_color="#6b7280", confidence=30.0, score=0, reasoning=["Insufficient data"])

    close = history_df["Close"].astype(float)
    high = history_df["High"].astype(float)
    low = history_df["Low"].astype(float)
    current_price = float(close.iloc[-1])
    score, reasoning, indicators = 0, [], {}

    # RSI
    rsi = calculate_rsi(close)
    rsi_score = 0
    if rsi < 30: rsi_score = 2; reasoning.append(f"RSI oversold at {rsi:.1f} — potential bounce")
    elif rsi < 40: rsi_score = 1; reasoning.append(f"RSI mildly oversold at {rsi:.1f}")
    elif rsi > 70: rsi_score = -2; reasoning.append(f"RSI overbought at {rsi:.1f} — pullback risk")
    elif rsi > 60: rsi_score = -1; reasoning.append(f"RSI approaching overbought at {rsi:.1f}")
    else: reasoning.append(f"RSI neutral at {rsi:.1f}")
    score += rsi_score
    indicators["rsi"] = {"value": rsi, "signal": "bullish" if rsi_score > 0 else ("bearish" if rsi_score < 0 else "neutral"), "description": f"RSI(14): {rsi:.1f}"}

    # MACD
    macd_line, signal_line, histogram = calculate_macd(close)
    macd_score = 0
    if macd_line > signal_line: macd_score = 2 if histogram > 0 else 1; reasoning.append("MACD bullish — above signal line")
    elif macd_line < signal_line: macd_score = -2 if histogram < 0 else -1; reasoning.append("MACD bearish — below signal line")
    score += macd_score
    indicators["macd"] = {"value": macd_line, "signal_line": signal_line, "histogram": histogram, "signal": "bullish" if macd_score > 0 else ("bearish" if macd_score < 0 else "neutral"), "description": f"MACD: {macd_line:.3f} | Signal: {signal_line:.3f}"}

    # SMA 50
    sma_50 = calculate_sma(close, 50)
    sma_50_score = 0
    if len(close) >= 50:
        if current_price > sma_50: sma_50_score = 1; reasoning.append(f"Price {((current_price - sma_50) / sma_50 * 100):.1f}% above 50-day SMA")
        else: sma_50_score = -1; reasoning.append(f"Price below 50-day SMA — bearish pressure")
    score += sma_50_score
    indicators["sma_50"] = {"value": sma_50, "signal": "bullish" if sma_50_score > 0 else ("bearish" if sma_50_score < 0 else "neutral"), "description": f"SMA(50): ${sma_50:.2f}"}

    # SMA 200
    sma_200 = calculate_sma(close, 200)
    sma_200_score = 0
    if len(close) >= 200:
        if current_price > sma_200:
            sma_200_score = 2 if sma_50 > sma_200 else 1
            reasoning.append("Golden Cross" if sma_50 > sma_200 else "Price above 200-day SMA")
        else:
            sma_200_score = -2 if sma_50 < sma_200 else -1
            reasoning.append("Death Cross" if sma_50 < sma_200 else "Price below 200-day SMA")
    score += sma_200_score
    indicators["sma_200"] = {"value": sma_200, "signal": "bullish" if sma_200_score > 0 else ("bearish" if sma_200_score < 0 else "neutral"), "description": f"SMA(200): ${sma_200:.2f}"}

    # Bollinger Bands
    bb_upper, bb_middle, bb_lower = calculate_bollinger_bands(close)
    bb_score = 0
    bb_position = get_price_position_in_bands(current_price, bb_upper, bb_lower, bb_middle)
    if current_price < bb_lower: bb_score = 1; reasoning.append(f"Price below lower Bollinger Band (${bb_lower:.2f}) — mean reversion likely")
    elif current_price > bb_upper: bb_score = -1; reasoning.append(f"Price above upper Bollinger Band (${bb_upper:.2f}) — potential reversal")
    score += bb_score
    indicators["bollinger"] = {"upper": bb_upper, "middle": bb_middle, "lower": bb_lower, "position": bb_position, "signal": "bullish" if bb_score > 0 else ("bearish" if bb_score < 0 else "neutral"), "description": f"BB: ${bb_lower:.2f} — ${bb_upper:.2f}"}

    # Stochastic
    stoch_k, stoch_d = calculate_stochastic(high, low, close)
    stoch_score = 0
    if stoch_k < 20 and stoch_d < 20: stoch_score = 1; reasoning.append(f"Stochastic oversold ({stoch_k:.0f})")
    elif stoch_k > 80 and stoch_d > 80: stoch_score = -1; reasoning.append(f"Stochastic overbought ({stoch_k:.0f})")
    score += stoch_score
    indicators["stochastic"] = {"k": stoch_k, "d": stoch_d, "signal": "bullish" if stoch_score > 0 else ("bearish" if stoch_score < 0 else "neutral"), "description": f"Stoch %K: {stoch_k:.1f}"}

    signal_key, signal_label, signal_color = _score_to_signal(score)
    confidence = _score_to_confidence(score)
    volatility_score = calculate_volatility_score(history_df)
    support, resistance = detect_support_resistance(history_df)

    return SignalResult(symbol=symbol, signal=signal_key, signal_label=signal_label, signal_color=signal_color, confidence=confidence, score=score, indicators=indicators, reasoning=reasoning, volatility_score=volatility_score, support_level=support, resistance_level=resistance, current_price=current_price, rsi=rsi, macd=macd_line, sma_50=sma_50, sma_200=sma_200, bollinger_position=bb_position)


def calculate_volatility_score(history_df: pd.DataFrame, period: int = 20) -> float:
    if history_df is None or len(history_df) < period:
        return 30.0
    close = history_df["Close"].astype(float)
    log_returns = close.pct_change().dropna()
    if len(log_returns) < 2:
        return 30.0
    annualized_vol = log_returns.std() * (252 ** 0.5)
    return round(float(min(100.0, max(0.0, (annualized_vol * 100 - 10) / 90 * 100))), 1)


def detect_support_resistance(history_df: pd.DataFrame, window: int = 20) -> Tuple[Optional[float], Optional[float]]:
    if history_df is None or len(history_df) < window:
        return None, None
    close = history_df["Close"].astype(float)
    low = history_df["Low"].astype(float)
    high = history_df["High"].astype(float)
    support = float(low.rolling(window=window).min().iloc[-1])
    resistance = float(high.rolling(window=window).max().iloc[-1])
    return round(support, 2), round(resistance, 2)
