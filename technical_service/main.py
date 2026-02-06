from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import httpx
import pandas as pd
import asyncio
import json
import os
import uvicorn
import sys
from io import StringIO

# Add shared directory to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from shared.constants import (
    GOOGLE_SHEET_CSV, RSI_PERIOD, MA_PERIOD, MA_50, MA_200
)
from technical_service.logic import (
    calculate_rsi, calculate_ma, detect_candlestick, calculate_confluence_score
)

app = FastAPI(title="NEPSE Technical Service")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Global Cache
CACHE = {
    "raw": pd.DataFrame(),
    "rsi": pd.DataFrame(),
    "ma": pd.DataFrame(),
    "crossover": pd.DataFrame(),
    "confluence": pd.DataFrame(),
    "candlestick": pd.DataFrame(),
    "momentum": pd.DataFrame(),
    "last_updated": None
}

async def load_technical_data():
    try:
        print("🔄 Fetching Technical data from Google Sheets...")
        async with httpx.AsyncClient(timeout=60, follow_redirects=True) as client:
            resp = await client.get(GOOGLE_SHEET_CSV)

        if resp.status_code != 200:
            return

        df = pd.read_csv(StringIO(resp.text))
        df.columns = df.columns.str.strip().str.lower()
        
        required = {"date", "symbol", "open", "high", "low", "close", "volume"}
        if not required.issubset(df.columns):
            return

        df["date"] = pd.to_datetime(df["date"], errors="coerce")
        for col in ["open", "high", "low", "close", "volume"]:
            df[col] = pd.to_numeric(df[col], errors="coerce")
        
        df = df.dropna(subset=["date", "symbol", "close"])
        df = df.sort_values(["symbol", "date"])
        CACHE["raw"] = df.copy()

        rsi_list, ma_list, cross_list, conf_list, candle_list, momentum_list = [], [], [], [], [], []

        for symbol, g in df.groupby("symbol"):
            symbol_str = str(symbol).upper()
            if any(char.isdigit() for char in symbol_str): continue
            g = g.copy()
            if len(g) < 2: continue
            
            g["rsi"] = calculate_rsi(g["close"], RSI_PERIOD)
            g["ma20"] = calculate_ma(g["close"], MA_PERIOD)
            g["sma50"] = calculate_ma(g["close"], MA_50)
            g["sma200"] = calculate_ma(g["close"], MA_200)
            g["vol_avg20"] = calculate_ma(g["volume"], 20)
            
            last = g.iloc[-1]
            prev = g.iloc[-2]
            
            if not pd.isna(last["rsi"]):
                rsi_list.append({"symbol": symbol_str, "close": float(last["close"]), "rsi": round(float(last["rsi"]), 2)})

            ma_dist_pct = 0
            if not pd.isna(last["ma20"]):
                ma_dist_pct = (last["close"] - last["ma20"]) / last["ma20"] * 100
                ma_list.append({
                    "symbol": symbol_str, "close": float(last["close"]),
                    "ma": round(float(last["ma20"]), 2), "percent_diff": round(float(ma_dist_pct), 2)
                })

            if len(g) >= MA_200 and not pd.isna(last["sma200"]):
                signal = "Golden Cross" if (prev["sma50"] <= prev["sma200"] and last["sma50"] > last["sma200"]) else \
                         "Death Cross" if (prev["sma50"] >= prev["sma200"] and last["sma50"] < last["sma200"]) else \
                         "Bullish Alignment" if last["sma50"] > last["sma200"] else "Bearish Alignment"
                cross_list.append({
                    "symbol": symbol_str, "close": float(last["close"]),
                    "sma50": round(float(last["sma50"]), 2), "sma200": round(float(last["sma200"]), 2),
                    "signal": signal, "is_cross": ("Cross" in signal)
                })

            pattern = detect_candlestick(g)
            if pattern != "Neutral":
                candle_list.append({"symbol": symbol_str, "close": float(last["close"]), "pattern": pattern})

            score, breakdown = calculate_confluence_score(last["rsi"], ma_dist_pct, last["sma50"], last["sma200"])
            conf_list.append({
                "symbol": symbol_str, "close": float(last["close"]), "score": int(score),
                "breakdown": breakdown, "rsi": round(float(last["rsi"]), 2) if not pd.isna(last["rsi"]) else None,
                "trend": "Bullish" if score > 60 else "Bearish" if score < 40 else "Neutral"
            })

            v_avg = last["vol_avg20"] if not pd.isna(last["vol_avg20"]) else 0
            vol_ratio = last["volume"] / v_avg if v_avg > 0 else 0
            win_52 = g.tail(250)
            h52 = win_52["high"].max()
            l52 = win_52["low"].min()
            rs_score = (last["close"] / g.iloc[-250]["close"] * 100) if len(g) >= 250 else 0

            momentum_list.append({
                "symbol": symbol_str, "close": float(last["close"]), "vol_ratio": round(float(vol_ratio), 2),
                "high_52": float(h52), "low_52": float(l52), "rs_score": round(float(rs_score), 2),
                "breakout": "High" if last["close"] >= h52 else "Low" if last["close"] <= l52 else "Neutral"
            })

        CACHE["rsi"] = pd.DataFrame(rsi_list)
        CACHE["ma"] = pd.DataFrame(ma_list)
        CACHE["crossover"] = pd.DataFrame(cross_list)
        CACHE["confluence"] = pd.DataFrame(conf_list)
        CACHE["candlestick"] = pd.DataFrame(candle_list)
        CACHE["momentum"] = pd.DataFrame(momentum_list)
        CACHE["last_updated"] = time.time()
        print("✅ Technical Data Updated")
    except Exception as e:
        print(f"❌ Load Error: {e}")

async def auto_refresh():
    while True:
        await asyncio.sleep(600) # Refresh every 10 mins as requested
        await load_technical_data()

@app.on_event("startup")
async def startup():
    await load_technical_data()
    asyncio.create_task(auto_refresh())

@app.get("/rsi/all")
def rsi_all():
    return CACHE["rsi"].to_dict(orient="records")

@app.get("/ma/all")
def ma_all():
    return CACHE["ma"].to_dict(orient="records")

@app.get("/momentum/all")
def momentum_all():
    return CACHE["momentum"].to_dict(orient="records")

@app.get("/confluence/all")
def confluence_all():
    return CACHE["confluence"].sort_values("score", ascending=False).to_dict(orient="records")

@app.get("/crossovers/all")
def crossovers_all():
    return CACHE["crossover"].to_dict(orient="records")

@app.get("/candlesticks/all")
def candlesticks_all():
    return CACHE["candlestick"].to_dict(orient="records")

@app.get("/rsi/filter")
def rsi_filter(min: float = None, max: float = None):
    df = CACHE["rsi"].copy()
    if min is not None: df = df[df["rsi"] >= min]
    if max is not None: df = df[df["rsi"] <= max]
    return df.sort_values("rsi").to_dict(orient="records")

@app.get("/rsi/status")
def rsi_status():
    return {"status": "ready" if not CACHE["rsi"].empty else "not_ready", "symbols": len(CACHE["rsi"])}

@app.get("/ma/status")
def ma_status():
    return {"status": "ready" if not CACHE["ma"].empty else "not_ready", "symbols": len(CACHE["ma"])}

@app.get("/refresh-technical")
async def refresh():
    await load_technical_data()
    return {"status": "success"}

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8002))
    uvicorn.run("main:app", host="0.0.0.0", port=port)
import time
