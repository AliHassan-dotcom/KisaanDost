"""Authentication, password hashing, JWT handling, and role-based access.

All password material is hashed; no plaintext is stored or returned.
Tokens carry role claims only — never passwords.
"""

from __future__ import annotations

import time
from datetime import datetime, timedelta, timezone
from enum import Enum
from typing import Any, Callable, Dict, Optional

from fastapi import Depends, HTTPException, Request, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from jose import JWTError, jwt
from passlib.context import CryptContext

from app.config import settings

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
bearer_scheme = HTTPBearer(auto_error=False)


class Role(str, Enum):
    FARMER = "farmer"
    EXTENSION_WORKER = "extension_worker"
    ADMIN = "admin"


def hash_password(password: str) -> str:
    return pwd_context.hash(password)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(plain_password, hashed_password)


def create_access_token(
    user_id: str,
    role: Role,
    phone: str,
    expires_delta: Optional[timedelta] = None,
) -> str:
    if expires_delta is None:
        expires_delta = timedelta(minutes=settings.jwt_access_token_minutes)
    now = datetime.now(timezone.utc)
    payload = {
        "sub": user_id,
        "role": role.value,
        "phone": phone,
        "iat": now,
        "exp": now + expires_delta,
        "type": "access",
    }
    return jwt.encode(payload, settings.jwt_secret_key, algorithm=settings.jwt_algorithm)


def decode_token(token: str) -> Optional[Dict[str, Any]]:
    try:
        return jwt.decode(
            token, settings.jwt_secret_key, algorithms=[settings.jwt_algorithm]
        )
    except JWTError:
        return None


def _extract_token_from_request(
    credentials: Optional[HTTPAuthorizationCredentials],
) -> Optional[str]:
    if credentials is None:
        return None
    scheme, _, param = credentials.scheme.strip(), "", credentials.credentials
    # Accept "Bearer <token>" or raw token
    if scheme.lower() == "bearer":
        return param
    return credentials.credentials


async def get_current_user(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(bearer_scheme),
) -> Dict[str, Any]:
    token = _extract_token_from_request(credentials)
    if token is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication required.",
            headers={"WWW-Authenticate": "Bearer"},
        )
    payload = decode_token(token)
    if payload is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token.",
        )
    if payload.get("type") != "access":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token type.",
        )
    return {
        "user_id": payload["sub"],
        "role": Role(payload["role"]),
        "phone": payload["phone"],
    }


async def get_current_user_optional(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(bearer_scheme),
) -> Optional[Dict[str, Any]]:
    token = _extract_token_from_request(credentials)
    if token is None:
        return None
    payload = decode_token(token)
    if payload is None or payload.get("type") != "access":
        return None
    try:
        return {
            "user_id": payload["sub"],
            "role": Role(payload["role"]),
            "phone": payload["phone"],
        }
    except Exception:
        return None



def require_role(*allowed: Role) -> Callable:
    def checker(user: Dict[str, Any] = Depends(get_current_user)) -> Dict[str, Any]:
        if user["role"] not in allowed:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You do not have permission to access this resource.",
            )
        return user

    return checker


# ---- In-memory rate limiting ----
# Production should use Redis; this satisfies the MVP requirement without extra infra.
_rate_buckets: Dict[str, list[float]] = {}
_login_buckets: Dict[str, list[float]] = {}


def _is_allowed(buckets: Dict[str, list[float]], key: str, limit: int, window: int) -> bool:
    now = time.time()
    timestamps = buckets.get(key, [])
    timestamps = [t for t in timestamps if now - t < window]
    buckets[key] = timestamps
    if len(timestamps) >= limit:
        return False
    timestamps.append(now)
    return True


def rate_limit_key(request: Request) -> str:
    forwarded = request.headers.get("x-forwarded-for")
    client = forwarded.split(",")[0].strip() if forwarded else request.client.host if request.client else "unknown"
    return f"{client}:{request.url.path}"


def check_rate_limit(request: Request) -> None:
    key = rate_limit_key(request)
    if not _is_allowed(
        _rate_buckets,
        key,
        settings.rate_limit_requests,
        settings.rate_limit_window_seconds,
    ):
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail="Too many requests. Please slow down.",
        )


def check_login_rate_limit(request: Request, phone: str) -> None:
    key = f"{rate_limit_key(request)}:{phone}"
    if not _is_allowed(
        _login_buckets,
        key,
        settings.login_rate_limit_requests,
        settings.login_rate_limit_window_seconds,
    ):
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail="Too many login attempts. Please try again later.",
        )


# ---- Advisory rate limiting ----
_advisory_buckets: Dict[str, list[float]] = {}


def check_advisory_rate_limit(request: Request, user_id: str) -> None:
    key = f"advisory:{user_id}"
    if not _is_allowed(
        _advisory_buckets,
        key,
        settings.pesticide_advisory_rate_limit_requests,
        settings.pesticide_advisory_rate_limit_window_seconds,
    ):
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail="Too many advisory requests. Please slow down.",
        )
