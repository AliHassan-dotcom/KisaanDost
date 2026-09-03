from fastapi import APIRouter

from app.api.v1.endpoints import alerts, auth, dashboard, farms, prices, weather

api_router = APIRouter()
api_router.include_router(auth.router, prefix="/auth", tags=["auth"])
api_router.include_router(farms.router, prefix="/farms", tags=["farms"])
api_router.include_router(dashboard.router, prefix="/dashboard", tags=["dashboard"])
api_router.include_router(weather.router, prefix="/weather", tags=["weather"])
api_router.include_router(prices.router, prefix="/prices", tags=["prices"])
api_router.include_router(alerts.router, prefix="/alerts", tags=["alerts"])
