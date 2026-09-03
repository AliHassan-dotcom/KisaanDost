"""Weather endpoints backed by Open-Meteo live API and NASA POWER monthly aggregates."""

from __future__ import annotations

from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, Request, status

from app.backend.database import UserStore, get_user_store
from app.backend.schemas import (
    DistrictListResponse,
    WeatherCurrentData,
    WeatherForecastResponse,
)
from app.backend.services import weather_service
from app.security.auth import get_current_user_optional

router = APIRouter(prefix="/weather", tags=["weather"])


@router.get("/districts", response_model=DistrictListResponse)
async def list_districts(
    svc: weather_service.WeatherService = Depends(weather_service.get_weather_service),
):
    return DistrictListResponse(districts=svc.districts())


@router.get("/current")
async def current_weather(
    request: Request,
    district: Optional[str] = Query(None, min_length=2),
    current_user: Optional[dict] = Depends(get_current_user_optional),
    store: UserStore = Depends(get_user_store),
    svc: weather_service.WeatherService = Depends(weather_service.get_weather_service),
):
    # Security check: client must not pass arbitrary lat/lon coordinates directly
    if "latitude" in request.query_params or "longitude" in request.query_params or "lat" in request.query_params or "lon" in request.query_params:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Direct coordinates are disallowed. Supply a validated Punjab district name.",
        )

    target_district = district
    if not target_district and current_user:
        profile = store.get_profile(current_user["user_id"]) or {}
        target_district = profile.get("district")
    if not target_district:
        target_district = "Lahore"

    try:
        data = svc.current(target_district)
        return {"success": True, "data": data}
    except weather_service.DistrictNotFoundError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(exc),
        )


@router.get("/forecast")
async def forecast_weather(
    request: Request,
    district: Optional[str] = Query(None, min_length=2),
    days: int = Query(7, ge=1, le=10),
    current_user: Optional[dict] = Depends(get_current_user_optional),
    store: UserStore = Depends(get_user_store),
    svc: weather_service.WeatherService = Depends(weather_service.get_weather_service),
):
    # Security check: client must not pass arbitrary lat/lon coordinates directly
    if "latitude" in request.query_params or "longitude" in request.query_params or "lat" in request.query_params or "lon" in request.query_params:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Direct coordinates are disallowed. Supply a validated Punjab district name.",
        )

    target_district = district
    if not target_district and current_user:
        profile = store.get_profile(current_user["user_id"]) or {}
        target_district = profile.get("district")
    if not target_district:
        target_district = "Lahore"

    try:
        data = svc.forecast(target_district, days=days)
        return {"success": True, "data": data}
    except weather_service.DistrictNotFoundError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(exc),
        )


@router.get("/historical")
async def historical_weather(
    request: Request,
    district: Optional[str] = Query(None, min_length=2),
    current_user: Optional[dict] = Depends(get_current_user_optional),
    store: UserStore = Depends(get_user_store),
    svc: weather_service.WeatherService = Depends(weather_service.get_weather_service),
):
    target_district = district
    if not target_district and current_user:
        profile = store.get_profile(current_user["user_id"]) or {}
        target_district = profile.get("district")
    if not target_district:
        target_district = "Lahore"

    return {"success": True, "data": svc.historical(target_district)}
