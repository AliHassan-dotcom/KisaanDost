"""Agricultural statistics endpoints for Land Utilization and Water Availability."""

from __future__ import annotations

from typing import Optional

from fastapi import APIRouter, Depends, Query

from app.backend.services.agri_stats_service import AgriStatsService, get_agri_stats_service
from app.security.auth import get_current_user_optional

router = APIRouter(prefix="/agri", tags=["agricultural-statistics"])


@router.get("/land-utilization")
async def get_land_utilization(
    district: Optional[str] = Query(None, max_length=100),
    current_user: Optional[dict] = Depends(get_current_user_optional),
    service: AgriStatsService = Depends(get_agri_stats_service),
) -> dict:
    """Return district-level agricultural land utilization and crop acreage statistics."""
    resp = service.get_land_utilization(district=district)
    return {"success": True, "data": resp.model_dump()}


@router.get("/water-availability")
async def get_water_availability(
    district: Optional[str] = Query(None, max_length=100),
    current_user: Optional[dict] = Depends(get_current_user_optional),
    service: AgriStatsService = Depends(get_agri_stats_service),
) -> dict:
    """Return district-level irrigation sources, water reliance, and provincial water benchmarks."""
    resp = service.get_water_availability(district=district)
    return {"success": True, "data": resp.model_dump()}


@router.get("/gdp")
async def get_agri_gdp(
    province: Optional[str] = Query(None, max_length=100),
    current_user: Optional[dict] = Depends(get_current_user_optional),
    service: AgriStatsService = Depends(get_agri_stats_service),
) -> dict:
    """Return historical and provisional Agricultural GDP share time series."""
    resp = service.get_gdp(province=province)
    return {"success": True, "data": resp.model_dump()}


@router.get("/exports")
async def get_agri_exports(
    commodity: Optional[str] = Query(None, max_length=100),
    current_user: Optional[dict] = Depends(get_current_user_optional),
    service: AgriStatsService = Depends(get_agri_stats_service),
) -> dict:
    """Return major agricultural exports with trade values, quantities, and shares."""
    resp = service.get_exports(commodity=commodity)
    return {"success": True, "data": resp.model_dump()}


@router.get("/imports")
async def get_agri_imports(
    commodity: Optional[str] = Query(None, max_length=100),
    current_user: Optional[dict] = Depends(get_current_user_optional),
    service: AgriStatsService = Depends(get_agri_stats_service),
) -> dict:
    """Return major agricultural imports with trade values, quantities, and shares."""
    resp = service.get_imports(commodity=commodity)
    return {"success": True, "data": resp.model_dump()}


@router.get("/trade-summary")
async def get_agri_trade_summary(
    current_user: Optional[dict] = Depends(get_current_user_optional),
    service: AgriStatsService = Depends(get_agri_stats_service),
) -> dict:
    """Return overall agricultural trade balance and national trade share summary."""
    resp = service.get_trade_summary()
    return {"success": True, "data": resp.model_dump()}

