# -------------------------------------------------
# API URLs
# -------------------------------------------------
NEPSELYTICS_URL = "https://sharehubnepal.com/live/api/v2/nepselive/home-page-data"
NEPSE_TURNOVER_URL = "https://tms59.nepsetms.com.np/tmsapi/rtApi/admin/vCache/marketTurnover"
NEPSELYTICS_FLOORSHEET_URL = "https://nepselytics-6d61dea19f30.herokuapp.com/api/nepselytics/floorsheet"

NEPALIPAISA_INDEX_URL = "https://nepalipaisa.com/api/GetIndexLive"
NEPALIPAISA_SUBINDEX_URL = "https://nepalipaisa.com/api/GetSubIndexLive"

SHAREHUB_ANNOUNCEMENT_URL = "https://sharehubnepal.com/data/api/v1/announcement"
SHAREHUB_OFFERING_URL = "https://sharehubnepal.com/data/api/v1/public-offering"

GOOGLE_SHEET_CSV = (
    "https://docs.google.com/spreadsheets/d/"
    "1Q_En7VGGfifDmn5xuiF-t_02doPpwl4PLzxb4TBCW0Q"
    "/export?format=csv"
)

# Technical Periods
RSI_PERIOD = 14
MA_PERIOD = 20
MA_50 = 50
MA_200 = 200

# Common Headers
DEFAULT_HEADERS = {
    "User-Agent": "Mozilla/5.0",
    "Accept": "application/json"
}
