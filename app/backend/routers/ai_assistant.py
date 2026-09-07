from __future__ import annotations

from typing import Optional
from fastapi import APIRouter, Depends
from pydantic import BaseModel

from app.backend.database import get_user_store, UserStore
from app.backend.services.ai_agronomist_service import AIAgronomistService, get_ai_agronomist_service
from app.security.auth import get_current_user_optional

router = APIRouter(prefix="/ai", tags=["ai-assistant"])


class AIAskRequest(BaseModel):
    query: str
    district: Optional[str] = None
    crop: Optional[str] = None
    language: Optional[str] = "ur"


class AIAskResponse(BaseModel):
    answer: str
    source: str
    confidence: float


@router.post("/ask", response_model=AIAskResponse)
async def ask_agronomist(
    payload: AIAskRequest,
    svc: AIAgronomistService = Depends(get_ai_agronomist_service),
    current_user: Optional[dict] = Depends(get_current_user_optional),
    store: UserStore = Depends(get_user_store),
):
    effective_district = payload.district
    effective_crop = payload.crop

    if current_user:
        profile = store.get_profile(current_user["user_id"])
        if profile:
            if not effective_district:
                effective_district = profile.get("district")
            if not effective_crop:
                effective_crop = profile.get("crop")

    result = await svc.answer_query(
        query=payload.query,
        district=effective_district or "Lahore",
        crop=effective_crop or "Wheat",
        language=payload.language or "ur",
    )
    return AIAskResponse(**result)
