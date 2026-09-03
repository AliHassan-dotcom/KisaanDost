"""AI Assistant router for real-time agricultural query answering."""

from __future__ import annotations

from typing import Optional
from fastapi import APIRouter, Depends
from pydantic import BaseModel

from app.backend.services.ai_agronomist_service import AIAgronomistService, get_ai_agronomist_service
from app.security.auth import get_current_user

router = APIRouter(prefix="/ai", tags=["ai-assistant"])


class AIAskRequest(BaseModel):
    query: str
    district: Optional[str] = "Lahore"
    crop: Optional[str] = "Wheat"
    language: Optional[str] = "ur"


class AIAskResponse(BaseModel):
    answer: str
    source: str
    confidence: float


@router.post("/ask", response_model=AIAskResponse)
async def ask_agronomist(
    payload: AIAskRequest,
    svc: AIAgronomistService = Depends(get_ai_agronomist_service),
    current_user: dict = Depends(get_current_user),
):
    result = await svc.answer_query(
        query=payload.query,
        district=payload.district or "Lahore",
        crop=payload.crop or "Wheat",
        language=payload.language or "ur",
    )
    return AIAskResponse(**result)
