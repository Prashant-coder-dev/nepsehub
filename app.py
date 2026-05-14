import os
import sys
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

# Add the current directory to sys.path so sub-modules can be found
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Import the individual service apps
try:
    from core_service.main import app as core_app
    from technical_service.main import app as tech_app
    from charts_service.main import app as charts_app
    from market_info_service.main import app as market_app
except ImportError as e:
    print(f"Error importing sub-services: {e}")
    # Provide dummy apps if any fail to import
    core_app = tech_app = charts_app = market_app = FastAPI()

# Create the Master App
app = FastAPI(
    title="NEPSE HUB Master API",
    description="Unified API Gateway for NEPSE HUB microservices",
    version="1.0.0"
)

# Enable Global CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount the sub-apps under their respective prefixes
# Note: A request to /core/homepage-data will be routed to core_service.main's /homepage-data
app.mount("/core", core_app)
app.mount("/technical", tech_app)
app.mount("/charts", charts_app)
app.mount("/market-info", market_app)

@app.get("/")
def read_root():
    return {
        "message": "Welcome to NEPSE HUB Master API Gateway",
        "status": "online",
        "services": {
            "core": "LIVE - Market data, indices, and summary",
            "technical": "LIVE - RSI, Moving Averages, and Momentum",
            "charts": "LIVE - Historical and intraday charting data",
            "market-info": "LIVE - Company fundamentals and floorsheet"
        },
        "docs": "/docs"
    }

if __name__ == "__main__":
    import uvicorn
    # Use PORT environment variable for Render compatibility
    port = int(os.environ.get("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)
