"""Farm & AOI endpoints (PRD.md F2). Polygon validation via shapely before any GEE enqueue."""

from fastapi import APIRouter

router = APIRouter()


@router.get("")
async def list_farms() -> dict:
    return {"success": True, "data": []}
