"""Weather endpoints — current + 48h forecast per farm (PRD.md F3)."""

from fastapi import APIRouter

router = APIRouter()


@router.get("/farms/{farm_id}")
async def farm_weather(farm_id: int) -> dict:
    raise NotImplementedError
