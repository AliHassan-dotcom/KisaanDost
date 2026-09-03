"""Append-only audit logging for security-relevant events.

Logs are written outside source-control paths and never include passwords.
"""

from __future__ import annotations

import json
import threading
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, Optional

from app.config import settings

_lock = threading.Lock()


def _ensure_log_file(path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)


def audit(
    event: str,
    actor_id: Optional[str] = None,
    details: Optional[Dict[str, Any]] = None,
    ip: Optional[str] = None,
) -> None:
    """Record a single audit event as a JSON line."""
    entry = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "event": event,
        "actor_id": actor_id,
        "ip": ip,
        "details": details or {},
    }
    log_path = settings.audit_log_path()
    _ensure_log_file(log_path)
    with _lock:
        with open(log_path, "a", encoding="utf-8") as fh:
            fh.write(json.dumps(entry, default=str, ensure_ascii=False) + "\n")
