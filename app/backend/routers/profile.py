"""Farmer profile endpoints."""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, status

from app.backend.database import UserStore, get_user_store
from app.backend.schemas import FarmerProfile, ProfileUpdateRequest
from app.security.auth import get_current_user

router = APIRouter(prefix="/profile", tags=["profile"])


@router.get("", response_model=FarmerProfile)
async def get_profile(
    current_user: dict = Depends(get_current_user),
    store: UserStore = Depends(get_user_store),
):
    profile = store.get_profile(current_user["user_id"])
    if profile is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Profile not found.",
        )
    return FarmerProfile(**profile)


@router.patch("", response_model=FarmerProfile)
async def update_profile(
    payload: ProfileUpdateRequest,
    current_user: dict = Depends(get_current_user),
    store: UserStore = Depends(get_user_store),
):
    updates = payload.model_dump(exclude_unset=True)
    if not updates:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No fields provided for update.",
        )
    try:
        profile = store.update_profile(current_user["user_id"], updates)
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(exc),
        ) from exc
    return FarmerProfile(**profile)
