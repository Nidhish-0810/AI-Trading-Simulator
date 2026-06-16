"""
Technical indicators for AI signal generation.
All functions accept pandas Series and return scalar float values.
"""
import logging
from typing import Optional, Tuple

import numpy as np
import pandas as pd

logger = logging.getLogger(__name__)


def calculate_rsi(prices: pd.Series, period: int = 14) -> float:
    """
    Calculate Relative Strength Index (RSI).

    RSI < 30 = oversold (potential buy signal)
    RSI > 70 = overbought (potential sell signal)

    Args:
        prices: Closing price series (oldest first)
        period: Lookback period (default 14)

    Returns:
        RSI value (0-100), or 50.0 if insufficient data
    """
    if len(prices) < period + 1:
        return 50.0

    delta = prices.diff()
    gain = delta.clip(lower=0)
    loss = -delta.clip(upper=0)

    avg_gain = gain.rolling(window=period, min_periods=period).mean()
    avg_loss = loss.rolling(window=period, min_periods=period).mean()

    # Smooth using Wilder's method
    for i in range(period, len(prices)):
        if i > period:
            avg_gain.iloc[i] = (avg_gain.iloc[i - 1] * (period - 1) + gain.iloc[i]) / period
            avg_loss.iloc[i] = (avg_loss.iloc[i - 1] * (period - 1) + loss.iloc[i]) / period

    rs = avg_gain / avg_loss.replace(0, np.finfo(float).eps)
    rsi = 100 - (100 / (1 + rs))

    current = rsi.iloc[-1]
    return float(round(current, 2)) if not np.isnan(current) else 50.0


def calculate_macd(
    prices: pd.Series,
    fast: int = 12,
    slow: int = 26,
    signal: int = 9,
) -> Tuple[float, float, float]:
    """
    Calculate MACD (Moving Average Convergence Divergence).

    Returns:
        (macd_line, signal_line, histogram)
        Bullish when macd_line > signal_line (positive histogram)
    """
    if len(prices) < slow + signal:
        return 0.0, 0.0, 0.0

    ema_fast = prices.ewm(span=fast, adjust=False).mean()
    ema_slow = prices.ewm(span=slow, adjust=False).mean()
    macd_line = ema_fast - ema_slow
    signal_line = macd_line.ewm(span=signal, adjust=False).mean()
    histogram = macd_line - signal_line

    ml = float(macd_line.iloc[-1])
    sl = float(signal_line.iloc[-1])
    hist = float(histogram.iloc[-1])

    if any(np.isnan(v) for v in [ml, sl, hist]):
        return 0.0, 0.0, 0.0

    return round(ml, 4), round(sl, 4), round(hist, 4)


def calculate_sma(prices: pd.Series, period: int) -> float:
    """
    Calculate Simple Moving Average for the most recent period.

    Returns:
        Current SMA value, or current price if insufficient data
    """
    if len(prices) < period:
        return float(prices.iloc[-1]) if len(prices) > 0 else 0.0

    sma = prices.rolling(window=period).mean().iloc[-1]
    return float(round(sma, 2)) if not np.isnan(sma) else float(prices.iloc[-1])


def calculate_ema(prices: pd.Series, period: int) -> float:
    """
    Calculate Exponential Moving Average.

    Returns:
        Current EMA value, or current price if insufficient data
    """
    if len(prices) < 2:
        return float(prices.iloc[-1]) if len(prices) > 0 else 0.0

    ema = prices.ewm(span=period, adjust=False).mean().iloc[-1]
    return float(round(ema, 2)) if not np.isnan(ema) else float(prices.iloc[-1])


def calculate_bollinger_bands(
    prices: pd.Series,
    period: int = 20,
    num_std: float = 2.0,
) -> Tuple[float, float, float]:
    """
    Calculate Bollinger Bands.

    Returns:
        (upper_band, middle_band, lower_band)
        Price near lower band → potential buy
        Price near upper band → potential sell
    """
    if len(prices) < period:
        price = float(prices.iloc[-1]) if len(prices) > 0 else 0.0
        return price * 1.02, price, price * 0.98

    sma = prices.rolling(window=period).mean()
    std = prices.rolling(window=period).std()

    upper = sma + (num_std * std)
    lower = sma - (num_std * std)

    u = float(upper.iloc[-1])
    m = float(sma.iloc[-1])
    l = float(lower.iloc[-1])

    if any(np.isnan(v) for v in [u, m, l]):
        price = float(prices.iloc[-1])
        return price * 1.02, price, price * 0.98

    return round(u, 2), round(m, 2), round(l, 2)


def calculate_atr(
    high: pd.Series,
    low: pd.Series,
    close: pd.Series,
    period: int = 14,
) -> float:
    """
    Calculate Average True Range (ATR) — volatility measure.

    Higher ATR = higher volatility
    """
    if len(close) < period + 1:
        return float((high.iloc[-1] - low.iloc[-1])) if len(high) > 0 else 0.0

    hl = high - low
    hc = (high - close.shift(1)).abs()
    lc = (low - close.shift(1)).abs()

    tr = pd.concat([hl, hc, lc], axis=1).max(axis=1)
    atr = tr.rolling(window=period).mean().iloc[-1]

    return float(round(atr, 4)) if not np.isnan(atr) else 0.0


def calculate_stochastic(
    high: pd.Series,
    low: pd.Series,
    close: pd.Series,
    k_period: int = 14,
    d_period: int = 3,
) -> Tuple[float, float]:
    """
    Calculate Stochastic Oscillator (%K and %D).

    %K < 20 = oversold
    %K > 80 = overbought

    Returns:
        (%K, %D)
    """
    if len(close) < k_period:
        return 50.0, 50.0

    lowest_low = low.rolling(window=k_period).min()
    highest_high = high.rolling(window=k_period).max()

    k = 100 * ((close - lowest_low) / (highest_high - lowest_low + np.finfo(float).eps))
    d = k.rolling(window=d_period).mean()

    k_val = float(k.iloc[-1])
    d_val = float(d.iloc[-1])

    if np.isnan(k_val):
        k_val = 50.0
    if np.isnan(d_val):
        d_val = 50.0

    return round(k_val, 2), round(d_val, 2)


def calculate_obv(close: pd.Series, volume: pd.Series) -> float:
    """
    Calculate On-Balance Volume (OBV) trend.

    Returns the current OBV value (normalized to thousands).
    Rising OBV with rising price = bullish confirmation.
    """
    if len(close) < 2:
        return 0.0

    direction = close.diff().apply(lambda x: 1 if x > 0 else (-1 if x < 0 else 0))
    obv = (direction * volume).cumsum()

    current = float(obv.iloc[-1])
    return round(current / 1000, 2) if not np.isnan(current) else 0.0


def get_price_position_in_bands(
    current_price: float,
    upper: float,
    lower: float,
    middle: float,
) -> float:
    """
    Calculate where the current price sits within Bollinger Bands.

    Returns:
        -1.0 (at lower band) to +1.0 (at upper band)
        0.0 = at middle band
    """
    band_width = upper - lower
    if band_width <= 0:
        return 0.0

    position = (current_price - middle) / (band_width / 2)
    return max(-1.0, min(1.0, position))


def calculate_williams_r(
    high: pd.Series,
    low: pd.Series,
    close: pd.Series,
    period: int = 14,
) -> float:
    """
    Calculate Williams %R oscillator.

    Range: -100 to 0
    -80 to -100 = oversold (buy signal)
    -20 to 0 = overbought (sell signal)
    """
    if len(close) < period:
        return -50.0

    highest_high = high.rolling(window=period).max()
    lowest_low = low.rolling(window=period).min()

    wr = -100 * ((highest_high - close) / (highest_high - lowest_low + np.finfo(float).eps))
    current = float(wr.iloc[-1])

    return round(current, 2) if not np.isnan(current) else -50.0
