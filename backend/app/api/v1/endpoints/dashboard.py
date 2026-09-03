"""Dashboard endpoints — the one-screen daily summary (PRD.md F5, the core endpoint).

Composes: risk score + crop health + weather + prices. Each module must degrade
independently (ERROR_HANDLING.md §1).
"""

from fastapi import APIRouter

router = APIRouter()


@router.get("")
async def daily_summary() -> dict:
    raise NotImplementedError
