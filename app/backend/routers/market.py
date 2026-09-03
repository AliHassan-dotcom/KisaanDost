"""Market rate endpoints serving official AMIS Punjab market prices."""

from __future__ import annotations

import re
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status

from app.backend.schemas import (
    MarketCommoditiesResponse,
    MarketHistoryResponse,
    MarketLatestResponse,
    MarketMoversResponse,
)
from app.backend.services.market_service import MarketService, get_market_service
from app.security.auth import get_current_user_optional

router = APIRouter(prefix="/market", tags=["market"])


def _validate_date_param(d: Optional[str]) -> Optional[str]:
    if not d:
        return None
    if not re.match(r"^\d{4}-\d{2}-\d{2}$", d.strip()):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid date format: '{d}'. Expected YYYY-MM-DD.",
        )
    return d.strip()


@router.get("/commodities")
async def get_commodities(
    current_user: Optional[dict] = Depends(get_current_user_optional),
    service: MarketService = Depends(get_market_service),
) -> dict:
    """Return allowlisted AMIS commodities catalog."""
    resp = service.get_commodities()
    return {"success": True, "data": resp.model_dump()}


@router.get("/latest")
async def get_latest(
    commodity: str = Query(..., min_length=1, max_length=100),
    market: Optional[str] = Query(None, max_length=100),
    current_user: Optional[dict] = Depends(get_current_user_optional),
    service: MarketService = Depends(get_market_service),
) -> dict:
    """Return latest official AMIS wholesale price records for a commodity."""
    resp = service.get_latest(commodity=commodity, market=market)
    return {"success": True, "data": resp.model_dump()}


@router.get("/movers")
async def get_movers(
    current_user: Optional[dict] = Depends(get_current_user_optional),
    service: MarketService = Depends(get_market_service),
) -> dict:
    """Return observed price movers across tracked AMIS commodities (no prediction)."""
    resp = service.get_movers()
    return {"success": True, "data": resp.model_dump()}


@router.get("/history")
async def get_history(
    commodity: str = Query(..., min_length=1, max_length=100),
    market: Optional[str] = Query(None, max_length=100),
    start: Optional[str] = Query(None),
    end: Optional[str] = Query(None),
    current_user: Optional[dict] = Depends(get_current_user_optional),
    service: MarketService = Depends(get_market_service),
) -> dict:
    """Return historical official AMIS wholesale prices for a commodity."""
    valid_start = _validate_date_param(start)
    valid_end = _validate_date_param(end)
    resp = service.get_history(
        commodity=commodity,
        market=market,
        start_date=valid_start,
        end_date=valid_end,
    )
    return {"success": True, "data": resp.model_dump()}


@router.get("/summary")
async def summary(
    crop: str = Query(..., min_length=1, max_length=100),
    district: Optional[str] = Query("Lahore", max_length=100),
    current_user: Optional[dict] = Depends(get_current_user_optional),
    service: MarketService = Depends(get_market_service),
) -> dict:
    """Legacy summary endpoint returning official AMIS or clean status."""
    return {"success": True, "data": service.market_summary(crop, district or "Lahore")}
