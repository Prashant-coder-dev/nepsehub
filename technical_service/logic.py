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

def calculate_confluence_score(rsi, ma_dist_pct, sma50, sma200):
    score = 50
    breakdown = {"baseline": 50, "rsi": 0, "ma": 0, "trend": 0}
    if not pd.isna(rsi):
        if rsi < 30: 
            score += 25
            breakdown["rsi"] = 25
        elif rsi < 40: 
            score += 15
            breakdown["rsi"] = 15
        elif rsi > 70: 
            score -= 20
            breakdown["rsi"] = -20
        elif rsi > 60: 
            score -= 10
            breakdown["rsi"] = -10
    if not pd.isna(ma_dist_pct):
        if ma_dist_pct > 0: 
            score += 10
            breakdown["ma"] += 10
        if ma_dist_pct > 5: 
            score += 5
            breakdown["ma"] += 5
    if not pd.isna(sma50) and not pd.isna(sma200):
        if sma50 > sma200: 
            score += 15
            breakdown["trend"] = 15
    final_score = max(0, min(100, score))
    return final_score, breakdown
