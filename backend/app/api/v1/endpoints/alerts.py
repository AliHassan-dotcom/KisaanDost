"""Alert endpoints — in-app alert center (PRD.md F7)."""

from fastapi import APIRouter

router = APIRouter()


@router.get("")
async def list_alerts() -> dict:
    return {"success": True, "data": []}
