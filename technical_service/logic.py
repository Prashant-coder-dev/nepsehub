import pandas as pd
import numpy as np
from io import StringIO
import httpx
from shared.constants import (
    RSI_PERIOD, MA_PERIOD, MA_50, MA_200
)

def calculate_rsi(close: pd.Series, period: int = 14):
    delta = close.diff()
    gain = delta.where(delta > 0, 0.0)
    loss = -delta.where(delta < 0, 0.0)
    avg_gain = gain.ewm(alpha=1 / period, min_periods=period).mean()
    avg_loss = loss.ewm(alpha=1 / period, min_periods=period).mean()
    rs = avg_gain / avg_loss
    return 100 - (100 / (1 + rs))

def calculate_ma(close: pd.Series, period: int = 20):
    return close.rolling(window=period).mean()

def detect_candlestick(df):
    if len(df) < 2: return "Neutral"
    curr = df.iloc[-1]
    prev = df.iloc[-2]
    o, h, l, c = curr['open'], curr['high'], curr['low'], curr['close']
    body = abs(c - o)
    candle_range = h - l
    if candle_range == 0: return "Neutral"
    body_percent = body / candle_range
    upper_wick = h - max(o, c)
    lower_wick = min(o, c) - l
    if lower_wick > (2 * body) and upper_wick < (0.1 * candle_range) and body_percent < 0.4:
        return "Hammer (Bullish)"
    if upper_wick > (2 * body) and lower_wick < (0.1 * candle_range) and body_percent < 0.4:
        return "Shooting Star (Bearish)"
    if c > o and prev['close'] < prev['open'] and c > prev['open'] and o < prev['close']:
        return "Bullish Engulfing"
    if c < o and prev['close'] > prev['open'] and c < prev['open'] and o > prev['close']:
        return "Bearish Engulfing"
    return "Neutral"


def detect_volume_shocker(df, vol_avg_20):
    """
    Detects volume shockers - when today's volume significantly exceeds 20-day average.
    Returns shock_level and vol_ratio
    - vol_ratio: today's volume / 20-day average volume
    - shock_level: "Extreme" (>3x), "High" (>2.5x), "Moderate" (>2x), "Normal"
    """
    if len(df) < 2 or pd.isna(vol_avg_20) or vol_avg_20 == 0:
        return "Normal", 0
    
    curr_volume = df.iloc[-1]["volume"]
    if pd.isna(curr_volume):
        return "Normal", 0
    
    vol_ratio = curr_volume / vol_avg_20
    
    if vol_ratio >= 3.0:
        shock_level = "Extreme"
    elif vol_ratio >= 2.5:
        shock_level = "High"
    elif vol_ratio >= 2.0:
        shock_level = "Moderate"
    else:
        shock_level = "Normal"
    
    return shock_level, round(vol_ratio, 2)
