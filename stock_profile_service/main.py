from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
import httpx
import os
import uvicorn
import sys

# Add shared directory to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from shared.constants import (
    NEPSELYTICS_STOCK_PROFILE_URL,
    NEPSELYTICS_ALPHA_BETA_URL,
    NEPSELYTICS_BROKER_TOP_HOLDING_URL,
    DEFAULT_HEADERS
)

app = FastAPI(title="NEPSE Stock Profile Service")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
async def get_stock_profile(symbol: str = Query(..., description="Stock symbol")):
    """
    Fetch detailed stock profile from NEPSElytics API.
    """
    if not symbol:
        raise HTTPException(status_code=400, detail="Symbol parameter is required")
    
    url = NEPSELYTICS_STOCK_PROFILE_URL
    params = {"symbol": symbol.upper()}
    headers = {**DEFAULT_HEADERS, "User-Agent": "Mozilla/5.0"}
    
    async with httpx.AsyncClient(timeout=30) as client:
        try:
            resp = await client.get(url, params=params, headers=headers)
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Failed to connect to stock profile server: {str(e)}")
            
    if resp.status_code != 200:
        raise HTTPException(status_code=resp.status_code, detail=f"Failed to fetch stock profile for {symbol}")
        
    return resp.json()

@app.get("/alpha-beta")
@app.get("/alphabeta")
async def get_alpha_beta(symbol: str = Query(..., description="Stock symbol")):
    """
    Fetch detailed stock alpha/beta ratios from NEPSElytics API.
    """
    if not symbol:
        raise HTTPException(status_code=400, detail="Symbol parameter is required")
    
    url = NEPSELYTICS_ALPHA_BETA_URL
    params = {"symbol": symbol.upper()}
    headers = {**DEFAULT_HEADERS, "User-Agent": "Mozilla/5.0"}
    
    async with httpx.AsyncClient(timeout=30) as client:
        try:
            resp = await client.get(url, params=params, headers=headers)
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Failed to connect to alpha-beta server: {str(e)}")
            
    if resp.status_code != 200:
        raise HTTPException(status_code=resp.status_code, detail=f"Failed to fetch alpha-beta ratios for {symbol}")
        
    return resp.json()

@app.get("/broker-top-holding")
async def get_broker_top_holding(
    symbol: str = Query(..., description="Stock symbol"),
    days: int = Query(1, description="Number of historical days to check")
):
    """
    Fetch daily broker top holdings for a specific symbol from NEPSElytics API.
    """
    if not symbol:
        raise HTTPException(status_code=400, detail="Symbol parameter is required")
    
    url = NEPSELYTICS_BROKER_TOP_HOLDING_URL
    params = {"symbol": symbol.upper(), "days": days}
    headers = {**DEFAULT_HEADERS, "User-Agent": "Mozilla/5.0"}
    
    async with httpx.AsyncClient(timeout=30) as client:
        try:
            resp = await client.get(url, params=params, headers=headers)
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Failed to connect to broker top holding server: {str(e)}")
            
    if resp.status_code != 200:
        raise HTTPException(status_code=resp.status_code, detail=f"Failed to fetch broker top holdings for {symbol}")
        
    return resp.json()

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8005))
    uvicorn.run("main:app", host="0.0.0.0", port=port)
