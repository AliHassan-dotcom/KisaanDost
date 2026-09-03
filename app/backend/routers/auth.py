"""Authentication endpoints."""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Request, status

from app.backend.database import UserStore, get_user_store
from app.backend.schemas import LoginRequest, RegisterRequest, TokenResponse
from app.security import create_access_token, verify_password
from app.security.audit import audit
from app.security.auth import Role, check_login_rate_limit, check_rate_limit, get_current_user

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/register", response_model=TokenResponse)
async def register(
    request: Request,
    payload: RegisterRequest,
    store: UserStore = Depends(get_user_store),
):
    check_rate_limit(request)
    try:
        user = store.create_user(
            phone=payload.phone,
            password=payload.password,
            role=payload.role.value,
            name=payload.name,
        )
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=str(exc),
        ) from exc

    audit("register", actor_id=user["id"], ip=_client_ip(request), details={"role": user["role"]})
    token = create_access_token(user["id"], Role(user["role"]), user["phone"])
    return TokenResponse(access_token=token, user_id=user["id"], role=Role(user["role"]))


@router.post("/login", response_model=TokenResponse)
async def login(
    request: Request,
    payload: LoginRequest,
    store: UserStore = Depends(get_user_store),
):
    check_login_rate_limit(request, payload.phone)
    user = store.get_user(payload.phone)
    if user is None or not verify_password(payload.password, user["password_hash"]):
        audit("login_failed", ip=_client_ip(request), details={"phone": payload.phone})
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid phone or password.",
        )

    audit("login_success", actor_id=user["id"], ip=_client_ip(request))
    token = create_access_token(user["id"], Role(user["role"]), user["phone"])
    return TokenResponse(
        access_token=token,
        user_id=user["id"],
        role=Role(user["role"]),
    )


@router.get("/me")
async def me(current_user: dict = Depends(get_current_user)):
    return {"success": True, "data": current_user}


def _client_ip(request: Request) -> str:
    forwarded = request.headers.get("x-forwarded-for")
    if forwarded:
        return forwarded.split(",")[0].strip()
    return request.client.host if request.client else "unknown"
