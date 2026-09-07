"""Authenticated satellite data API endpoints for Kisaan Dost."""

from __future__ import annotations

from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status

from app.backend.database import UserStore, get_user_store
from app.backend.schemas import (
    SatelliteCoverageResponse,
    SatelliteDistrictItem,
    SatelliteDistrictsResponse,
    SatelliteHistoryResponse,
    SatelliteRecord,
)
from app.backend.services.satellite_service import SatelliteService, get_satellite_service
from app.security.auth import get_current_user

router = APIRouter(prefix="/satellite", tags=["satellite"])


def _resolve_district(
    requested_district: Optional[str],
    current_user: dict,
    store: UserStore,
) -> str:
    if requested_district and requested_district.strip():
        return requested_district.strip()
    profile = store.get_profile(current_user["user_id"]) or {}
    return profile.get("district") or "Lahore"


@router.get("/districts", response_model=SatelliteDistrictsResponse)
async def list_districts(
    current_user: dict = Depends(get_current_user),
    service: SatelliteService = Depends(get_satellite_service),
):
    """List all 34 master districts and their satellite coverage status."""
    districts = service.list_districts()
    return SatelliteDistrictsResponse(
        total_districts=len(districts),
        districts=[SatelliteDistrictItem(**d) for d in districts],
    )


@router.get("/latest", response_model=SatelliteRecord)
async def get_latest_satellite(
    district: Optional[str] = Query(None, description="Punjab district name"),
    current_user: dict = Depends(get_current_user),
    store: UserStore = Depends(get_user_store),
    service: SatelliteService = Depends(get_satellite_service),
):
    """Retrieve the latest historical satellite observation and attention status for a district."""
    target_district = _resolve_district(district, current_user, store)
    try:
        record = service.get_latest(target_district)
        return SatelliteRecord(**record)
    except ValueError as err:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(err)) from err


@router.get("/history", response_model=SatelliteHistoryResponse)
async def get_satellite_history(
    district: Optional[str] = Query(None, description="Punjab district name"),
    start: Optional[str] = Query(None, description="Start period (YYYY-MM)", pattern=r"^\d{4}-\d{2}$"),
    end: Optional[str] = Query(None, description="End period (YYYY-MM)", pattern=r"^\d{4}-\d{2}$"),
    current_user: dict = Depends(get_current_user),
    store: UserStore = Depends(get_user_store),
    service: SatelliteService = Depends(get_satellite_service),
):
    """Retrieve monthly satellite history for trend analysis and chart rendering."""
    target_district = _resolve_district(district, current_user, store)
    try:
        norm_d = service.normalize_district(target_district)
        records = service.get_history(target_district, start_period=start, end_period=end)
        return SatelliteHistoryResponse(
            district=norm_d.replace(" District", ""),
            normalized_district=norm_d,
            total_records=len(records),
            start_period=start,
            end_period=end,
            records=[SatelliteRecord(**r) for r in records],
        )
    except ValueError as err:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(err)) from err


@router.get("/coverage", response_model=SatelliteCoverageResponse)
async def get_satellite_coverage(
    district: Optional[str] = Query(None, description="Punjab district name"),
    current_user: dict = Depends(get_current_user),
    store: UserStore = Depends(get_user_store),
    service: SatelliteService = Depends(get_satellite_service),
):
    """Retrieve geospatial boundary and historical coverage metadata for a district."""
    target_district = _resolve_district(district, current_user, store)
    try:
        cov = service.get_coverage(target_district)
        return SatelliteCoverageResponse(**cov)
    except ValueError as err:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(err)) from err


@router.get("/ndvi/timeseries")
async def get_ndvi_timeseries(
    district: Optional[str] = Query(None, description="Punjab district name"),
    lat: Optional[float] = Query(None, description="Farm GPS Latitude"),
    lng: Optional[float] = Query(None, description="Farm GPS Longitude"),
    current_user: dict = Depends(get_current_user),
    store: UserStore = Depends(get_user_store),
    service: SatelliteService = Depends(get_satellite_service),
):
    """Retrieve 56-month full Sentinel-2 NDVI vegetative timeline with seasonal stages."""
    target_district = _resolve_district(district, current_user, store)
    try:
        data = service.get_ndvi_timeseries(target_district)
        if lat is not None and lng is not None:
            data["farm_coordinates"] = {"latitude": lat, "longitude": lng}
        return {"success": True, "data": data}
    except ValueError as err:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(err)) from err


@router.get("/heatmap")
async def get_satellite_heatmap(
    district: Optional[str] = Query(None, description="Punjab district name"),
    grid_size: int = Query(12, ge=8, le=32),
    lat: Optional[float] = Query(None, description="Farm GPS Latitude"),
    lng: Optional[float] = Query(None, description="Farm GPS Longitude"),
    current_user: dict = Depends(get_current_user),
    store: UserStore = Depends(get_user_store),
    service: SatelliteService = Depends(get_satellite_service),
):
    """Retrieve localized spatial raster grid matrix with NDVI/NDWI and color gradient bounds."""
    target_district = _resolve_district(district, current_user, store)
    try:
        data = service.get_heatmap_matrix(target_district, grid_size=grid_size, lat=lat, lng=lng)
        return {"success": True, "data": data}
    except ValueError as err:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(err)) from err


@router.get("/tiles/{district}/{z}/{x}/{y}.png")
async def get_satellite_tile(
    district: str,
    z: int = 10,
    x: int = 0,
    y: int = 0,
    service: SatelliteService = Depends(get_satellite_service),
):
    """Generate and serve an interpolated PNG RGB heatmap tile."""
    from fastapi.responses import Response
    try:
        png_bytes = service.generate_tile_png(district, z=z, x=x, y=y)
        return Response(content=png_bytes, media_type="image/png")
    except ValueError as err:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(err)) from err


@router.get("/field-3d")
async def get_field_3d(
    district: Optional[str] = Query(None, description="Punjab district name"),
    size: int = Query(16, ge=8, le=32),
    lat: Optional[float] = Query(None, description="Farm GPS Latitude"),
    lng: Optional[float] = Query(None, description="Farm GPS Longitude"),
    current_user: dict = Depends(get_current_user),
    store: UserStore = Depends(get_user_store),
    service: SatelliteService = Depends(get_satellite_service),
):
    """Retrieve 3D elevation mesh heightmap and multi-layer canopy telemetry."""
    target_district = _resolve_district(district, current_user, store)
    try:
        data = service.get_field_3d_mesh(target_district, size=size, lat=lat, lng=lng)
        return {"success": True, "data": data}
    except ValueError as err:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(err)) from err

