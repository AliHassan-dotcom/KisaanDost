"""Admin-only endpoints for user management and audit review."""

from __future__ import annotations

import json
from datetime import datetime, timezone
from typing import Any, Dict, List

from fastapi import APIRouter, Depends

from app.backend.database import UserStore, get_user_store
from app.security.auth import Role, require_role

router = APIRouter(prefix="/admin", tags=["admin"])


@router.get("/users")
async def list_users(
    store: UserStore = Depends(get_user_store),
    admin: Dict[str, Any] = Depends(require_role(Role.ADMIN)),
):
    return {"success": True, "data": store.list_users()}


@router.get("/audit")
async def read_audit(
    admin: Dict[str, Any] = Depends(require_role(Role.ADMIN)),
    limit: int = 100,
):
    from app.config import settings

    log_path = settings.audit_log_path()
    entries: List[Dict[str, Any]] = []
    if log_path.exists():
        with open(log_path, "r", encoding="utf-8") as fh:
            for line in fh:
                line = line.strip()
                if not line:
                    continue
                try:
                    entries.append(json.loads(line))
                except json.JSONDecodeError:
                    continue
    return {"success": True, "data": entries[-limit:]}


@router.get("/stats")
async def stats(
    store: UserStore = Depends(get_user_store),
    admin: Dict[str, Any] = Depends(require_role(Role.ADMIN)),
):
    users = store.list_users()
    return {
        "success": True,
        "data": {
            "total_users": len(users),
            "roles": {
                role.value: sum(1 for u in users if u["role"] == role.value)
                for role in Role
            },
            "generated_at": datetime.now(timezone.utc).isoformat(),
        },
    }


@router.get("/migration-status")
async def migration_status(
    admin: Dict[str, Any] = Depends(require_role(Role.ADMIN)),
):
    """Admin-only check for database migration metadata and row counts."""
    from app.db.models import MigrationMetadata
    from app.db.session import SessionLocal, is_db_connected

    connected = is_db_connected()
    latest_meta = None

    if connected:
        db = SessionLocal()
        try:
            record = db.query(MigrationMetadata).order_by(MigrationMetadata.migrated_at.desc()).first()
            if record:
                latest_meta = {
                    "migration_name": record.migration_name,
                    "migrated_at": record.migrated_at.isoformat() if record.migrated_at else None,
                    "snapshot_hash": record.source_json_snapshot_hash,
                    "row_counts": record.row_counts,
                    "status": record.status,
                }
        finally:
            db.close()

    return {
        "success": True,
        "database_connected": connected,
        "migration_metadata": latest_meta or {
            "migration_name": "none",
            "status": "not_migrated" if not connected else "pending",
            "row_counts": {},
        },
    }

