"""Pest alert and pesticide advisory endpoints."""

from __future__ import annotations

from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query, Request, status

from app.backend.schemas import (
    AdvisoryRequest,
    AdvisoryResponse,
    PestAlertsResponse,
    PestSourcesResponse,
)
from app.backend.services.pesticide_service import PesticideService, get_pesticide_service
from app.security.audit import audit
from app.security.auth import check_advisory_rate_limit, get_current_user

router = APIRouter(prefix="/pest-alerts", tags=["pest-alerts"])


def _client_ip(request: Request) -> Optional[str]:
    forwarded = request.headers.get("x-forwarded-for")
    if forwarded:
        return forwarded.split(",")[0].strip()
    if request.client:
        return request.client.host
    return None


@router.get("/recent", response_model=PestAlertsResponse)
async def recent_alerts(
    request: Request,
    district: Optional[str] = Query(None, min_length=1, max_length=100),
    crop: Optional[str] = Query(None, min_length=1, max_length=100),
    category: Optional[str] = Query(None, min_length=1, max_length=100),
    limit: int = Query(50, ge=1, le=100),
    svc: PesticideService = Depends(get_pesticide_service),
    current_user: dict = Depends(get_current_user),
):
    audit(
        event="pest_alerts.recent",
        actor_id=current_user.get("user_id"),
        ip=_client_ip(request),
        details={
            "district": district,
            "crop": crop,
            "category": category,
            "limit": limit,
            "source_status": svc.source_status,
        },
    )
    alerts = svc.recent_alerts(
        district=district,
        crop=crop,
        category=category,
        limit=limit,
    )
    return PestAlertsResponse(
        district=district,
        crop=crop,
        category=category,
        source_status=svc.source_status,
        alerts=alerts,
    )


@router.post("/advisory", response_model=AdvisoryResponse)
async def advisory(
    request: Request,
    payload: AdvisoryRequest,
    svc: PesticideService = Depends(get_pesticide_service),
    current_user: dict = Depends(get_current_user),
):
    user_id = current_user.get("user_id")
    check_advisory_rate_limit(request, user_id)

    result = svc.advisory(
        crop=payload.crop,
        pest=payload.pest,
        district=payload.district,
    )

    audit(
        event="pest_alerts.advisory",
        actor_id=user_id,
        ip=_client_ip(request),
        details={
            "crop": payload.crop,
            "pest": payload.pest,
            "district": payload.district,
            "source_status": result.get("source_status"),
            "matched": result.get("matched"),
            "num_citations": len(result.get("citations", [])),
        },
    )

    return AdvisoryResponse(**result)


@router.get("/sources", response_model=PestSourcesResponse)
async def sources(
    request: Request,
    svc: PesticideService = Depends(get_pesticide_service),
    current_user: dict = Depends(get_current_user),
):
    audit(
        event="pest_alerts.sources",
        actor_id=current_user.get("user_id"),
        ip=_client_ip(request),
        details={"source_status": svc.source_status},
    )
    return PestSourcesResponse(sources=svc.sources())
