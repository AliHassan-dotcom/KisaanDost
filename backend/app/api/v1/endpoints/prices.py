"""Mandi price endpoints — crop × district with as-of timestamps (PRD.md F6)."""

from fastapi import APIRouter

router = APIRouter()


@router.get("")
async def list_prices() -> dict:
    raise NotImplementedError
