"""
Technical indicators for AI signal generation.
"""
import logging
from typing import Optional, Tuple

import numpy as np
import pandas as pd

logger = logging.getLogger(__name__)


def calculate_rsi(prices: pd.Series, period: int = 14) -> float:
    if len(prices) < period + 1:
        return 50.0
    delta = prices.diff()
    gain = delta.clip(lower=0)
    loss = -delta.clip(upper=0)
    avg_gain = gain.rolling(window=period, min_periods=period).mean()
    avg_loss = loss.rolling(window=period, min_periods=period).mean()
    for i in range(period, len(prices)):
        if i > period:
            avg_gain.iloc[i] = (avg_gain.iloc[i - 1] * (period - 1) + gain.iloc[i]) / period
            avg_loss.iloc[i] = (avg_loss.iloc[i - 1] * (period - 1) + loss.iloc[i]) / period
    rs = avg_gain / avg_loss.replace(0, np.finfo(float).eps)
    rsi = 100 - (100 / (1 + rs))
    current = rsi.iloc[-1]
    return float(round(current, 2)) if not np.isnan(current) else 50.0


def calculate_macd(prices: pd.Series, fast: int = 12, slow: int = 26, signal: int = 9) -> Tuple[float, float, float]:
    if len(prices) < slow + signal:
        return 0.0, 0.0, 0.0
    ema_fast = prices.ewm(span=fast, adjust=False).mean()
    ema_slow = prices.ewm(span=slow, adjust=False).mean()
    macd_line = ema_fast - ema_slow
    signal_line = macd_line.ewm(span=signal, adjust=False).mean()
    histogram = macd_line - signal_line
    ml, sl, hist = float(macd_line.iloc[-1]), float(signal_line.iloc[-1]), float(histogram.iloc[-1])
    if any(np.isnan(v) for v in [ml, sl, hist]):
        return 0.0, 0.0, 0.0
    return round(ml, 4), round(sl, 4), round(hist, 4)


def calculate_sma(prices: pd.Series, period: int) -> float:
    if len(prices) < period:
        return float(prices.iloc[-1]) if len(prices) > 0 else 0.0
    sma = prices.rolling(window=period).mean().iloc[-1]
    return float(round(sma, 2)) if not np.isnan(sma) else float(prices.iloc[-1])


def calculate_ema(prices: pd.Series, period: int) -> float:
    if len(prices) < 2:
        return float(prices.iloc[-1]) if len(prices) > 0 else 0.0
    ema = prices.ewm(span=period, adjust=False).mean().iloc[-1]
    return float(round(ema, 2)) if not np.isnan(ema) else float(prices.iloc[-1])


def calculate_bollinger_bands(prices: pd.Series, period: int = 20, num_std: float = 2.0) -> Tuple[float, float, float]:
    if len(prices) < period:
        price = float(prices.iloc[-1]) if len(prices) > 0 else 0.0
        return price * 1.02, price, price * 0.98
    sma = prices.rolling(window=period).mean()
    std = prices.rolling(window=period).std()
    upper = sma + (num_std * std)
    lower = sma - (num_std * std)
    u, m, l = float(upper.iloc[-1]), float(sma.iloc[-1]), float(lower.iloc[-1])
    if any(np.isnan(v) for v in [u, m, l]):
        price = float(prices.iloc[-1])
        return price * 1.02, price, price * 0.98
    return round(u, 2), round(m, 2), round(l, 2)


def calculate_atr(high: pd.Series, low: pd.Series, close: pd.Series, period: int = 14) -> float:
    if len(close) < period + 1:
        return float((high.iloc[-1] - low.iloc[-1])) if len(high) > 0 else 0.0
    hl = high - low
    hc = (high - close.shift(1)).abs()
    lc = (low - close.shift(1)).abs()
    tr = pd.concat([hl, hc, lc], axis=1).max(axis=1)
    atr = tr.rolling(window=period).mean().iloc[-1]
    return float(round(atr, 4)) if not np.isnan(atr) else 0.0


def calculate_stochastic(high: pd.Series, low: pd.Series, close: pd.Series, k_period: int = 14, d_period: int = 3) -> Tuple[float, float]:
    if len(close) < k_period:
        return 50.0, 50.0
    lowest_low = low.rolling(window=k_period).min()
    highest_high = high.rolling(window=k_period).max()
    k = 100 * ((close - lowest_low) / (highest_high - lowest_low + np.finfo(float).eps))
    d = k.rolling(window=d_period).mean()
    k_val = float(k.iloc[-1]) if not np.isnan(float(k.iloc[-1])) else 50.0
    d_val = float(d.iloc[-1]) if not np.isnan(float(d.iloc[-1])) else 50.0
    return round(k_val, 2), round(d_val, 2)


def calculate_williams_r(high: pd.Series, low: pd.Series, close: pd.Series, period: int = 14) -> float:
    if len(close) < period:
        return -50.0
    highest_high = high.rolling(window=period).max()
    lowest_low = low.rolling(window=period).min()
    wr = -100 * ((highest_high - close) / (highest_high - lowest_low + np.finfo(float).eps))
    current = float(wr.iloc[-1])
    return round(current, 2) if not np.isnan(current) else -50.0


def get_price_position_in_bands(current_price: float, upper: float, lower: float, middle: float) -> float:
    band_width = upper - lower
    if band_width <= 0:
        return 0.0
    return max(-1.0, min(1.0, (current_price - middle) / (band_width / 2)))


def calculate_obv(close: pd.Series, volume: pd.Series) -> float:
    if len(close) < 2:
        return 0.0
    direction = close.diff().apply(lambda x: 1 if x > 0 else (-1 if x < 0 else 0))
    obv = (direction * volume).cumsum()
    current = float(obv.iloc[-1])
    return round(current / 1000, 2) if not np.isnan(current) else 0.0
