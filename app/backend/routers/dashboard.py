"""Consolidated farmer dashboard endpoint."""

from __future__ import annotations

from fastapi import APIRouter, Depends

from app.backend.database import UserStore, get_user_store
from app.backend.schemas import DashboardResponse
from app.backend.services import market_service, satellite_service, weather_service
from app.security.auth import get_current_user

router = APIRouter(prefix="/dashboard", tags=["dashboard"])


@router.get("", response_model=DashboardResponse)
async def dashboard(
    current_user: dict = Depends(get_current_user),
    store: UserStore = Depends(get_user_store),
    weather_svc: weather_service.WeatherService = Depends(weather_service.get_weather_service),
):
    profile = store.get_profile(current_user["user_id"]) or {}
    district = profile.get("district") or "Lahore"
    crop = profile.get("crop") or "wheat"

    scans = store.list_scans(current_user["user_id"])
    latest_scan = scans[0] if scans else None
    farm_health = {
        "status": latest_scan["predicted_class"] if latest_scan else "no_recent_scan",
        "confidence": latest_scan["confidence"] if latest_scan else None,
        "uncertain": latest_scan["uncertain"] if latest_scan else False,
        "model_version": latest_scan["model_version"] if latest_scan else None,
        "last_scanned_at": latest_scan["scanned_at"] if latest_scan else None,
    }

    return DashboardResponse(
        user={
            "user_id": current_user["user_id"],
            "role": current_user["role"].value,
            "name": profile.get("name"),
            "district": district,
            "crop": crop,
            "language": profile.get("language", "en"),
        },
        weather=weather_svc.current(district),
        farm_health=farm_health,
        market=market_service.market_summary(crop, district),
        satellite=satellite_service.satellite_summary(district, crop),
        quick_actions=[
            {"label": "Scan crop", "href": "/scan.html", "icon": "camera"},
            {"label": "Weather", "href": "/weather.html", "icon": "cloud"},
            {"label": "Pest alerts", "href": "/pest-alerts.html", "icon": "alert"},
            {"label": "Market rates", "href": "/market.html", "icon": "trend"},
        ],
    )
