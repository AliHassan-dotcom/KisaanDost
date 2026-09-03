"""Crop health scan endpoints."""

from __future__ import annotations

from pathlib import Path

from fastapi import APIRouter, Depends, File, HTTPException, Request, UploadFile, status

from app.backend.database import UserStore, get_user_store
from app.backend.services import disease_service
from app.security.audit import audit
from app.security.auth import get_current_user
from app.security.upload import save_upload

router = APIRouter(prefix="/crop-health", tags=["crop-health"])


@router.post("/scan")
async def scan(
    request: Request,
    image: UploadFile = File(...),
    current_user: dict = Depends(get_current_user),
    store: UserStore = Depends(get_user_store),
):
    try:
        saved_path, original_name = save_upload(image)
    except HTTPException:
        raise
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Could not process upload: {exc}",
        ) from exc

    try:
        prediction = disease_service.predict(Path(saved_path))
    except FileNotFoundError as exc:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Disease model is not available.",
        ) from exc
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"Inference failed: {exc}",
        ) from exc

    record = store.record_scan(current_user["user_id"], prediction, str(saved_path))
    audit(
        "crop_scan",
        actor_id=current_user["user_id"],
        ip=_client_ip(request),
        details={
            "predicted_class": prediction["predicted_class"],
            "confidence": prediction["confidence"],
            "uncertain": prediction["uncertain"],
        },
    )

    return {"success": True, "data": record}


@router.get("/history")
async def history(
    current_user: dict = Depends(get_current_user),
    store: UserStore = Depends(get_user_store),
):
    return {"success": True, "data": store.list_scans(current_user["user_id"])}


def _client_ip(request: Request) -> str:
    forwarded = request.headers.get("x-forwarded-for")
    if forwarded:
        return forwarded.split(",")[0].strip()
    return request.client.host if request.client else "unknown"
