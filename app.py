import os
import sys
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

# Try to load environment variables from .env file for local development
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

# Add the current directory to sys.path so sub-modules can be found
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Add parent's database-backend directory to sys.path so database-backend sub-modules can be imported
db_backend_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "database-backend"))
if db_backend_path not in sys.path:
    sys.path.append(db_backend_path)

# Helper function to import sub-services individually and safely
def import_service(module_name, app_name="app"):
    try:
        from importlib import import_module
        module = import_module(module_name)
        return getattr(module, app_name)
    except Exception as e:
        print(f"⚠️ Error importing service '{module_name}': {e}")
        # Provide a descriptive fallback app so the rest of the API Gateway works
        fallback_app = FastAPI(title=f"NEPSE Hub {module_name} (Fallback)")
        @fallback_app.get("/")
        def fallback_root():
            return {
                "status": "offline",
                "error": f"Service failed to load: {str(e)}"
            }
        return fallback_app

# Import individual sub-services safely
core_app = import_service("core_service.main")
tech_app = import_service("technical_service.main")
charts_app = import_service("charts_service.main")
market_app = import_service("market_info_service.main")
stock_profile_app = import_service("stock_profile_service.main")
auth_app = import_service("auth_service.main")

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
app.mount("/stock-profile", stock_profile_app)
app.mount("/api/auth", auth_app)

@app.get("/")
def read_root():
    return {
        "message": "Welcome to NEPSE HUB Master API Gateway",
        "status": "online",
        "services": {
            "core": "LIVE - Market data, indices, and summary",
            "technical": "LIVE - RSI, Moving Averages, and Momentum",
            "charts": "LIVE - Historical and intraday charting data",
            "market-info": "LIVE - Company fundamentals and floorsheet",
            "stock-profile": "LIVE - Detailed stock profile data"
        },
        "docs": "/docs"
    }

if __name__ == "__main__":
    import uvicorn
    # Use PORT environment variable for Render compatibility
    port = int(os.environ.get("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)
