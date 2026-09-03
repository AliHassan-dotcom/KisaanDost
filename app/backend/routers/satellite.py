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
