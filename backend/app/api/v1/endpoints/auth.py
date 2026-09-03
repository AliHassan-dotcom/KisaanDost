"""Auth endpoints — phone OTP login → JWT (PRD.md F1). Implementation pending."""

from fastapi import APIRouter

router = APIRouter()


@router.post("/otp/request")
async def request_otp() -> dict:
    """Send OTP to phone. Rate limits: RULES.md §7.2."""
    raise NotImplementedError
