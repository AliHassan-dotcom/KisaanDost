"""Minimal JSON-backed user store for the MVP.

Production should replace this with PostgreSQL/SQLAlchemy. The store is used
only for auth credentials and farmer profiles; no sensitive plaintext is kept.
"""

from __future__ import annotations

import json
import threading
from pathlib import Path
from typing import Any, Dict, List, Optional

from app.config import settings
from app.security import hash_password

_lock = threading.Lock()


def _load_store(path: Path) -> Dict[str, Any]:
    if not path.exists():
        data = {"users": {}, "profiles": {}}
    else:
        try:
            with open(path, "r", encoding="utf-8") as fh:
                data = json.load(fh)
        except Exception:
            data = {"users": {}, "profiles": {}}

    # Auto-seed default demonstration accounts if not present
    if "03001234567" not in data.get("users", {}):
        data.setdefault("users", {})["03001234567"] = {
            "id": "user_000001",
            "phone": "03001234567",
            "role": "farmer",
            "password_hash": hash_password("password123"),
            "created_at": _now_iso(),
        }
        data.setdefault("profiles", {})["user_000001"] = {
            "user_id": "user_000001",
            "name": "Farm Hero",
            "district": "Multan",
            "crop": "wheat",
            "language": "en",
        }
    if "03009999999" not in data.get("users", {}):
        data.setdefault("users", {})["03009999999"] = {
            "id": "user_000002",
            "phone": "03009999999",
            "role": "admin",
            "password_hash": hash_password("admin123"),
            "created_at": _now_iso(),
        }
        data.setdefault("profiles", {})["user_000002"] = {
            "user_id": "user_000002",
            "name": "Agri Admin",
            "district": "Lahore",
            "crop": "wheat",
            "language": "en",
        }
    return data


def _save_store(path: Path, data: Dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", encoding="utf-8") as fh:
        json.dump(data, fh, indent=2, ensure_ascii=False)


class UserStore:
    def __init__(self, path: Optional[Path] = None):
        self.path = path or settings.user_store_path()

    def _read(self) -> Dict[str, Any]:
        return _load_store(self.path)

    def _write(self, data: Dict[str, Any]) -> None:
        _save_store(self.path, data)

    def get_user(self, phone: str) -> Optional[Dict[str, Any]]:
        phone = phone.strip()
        data = self._read()
        return data["users"].get(phone)

    def create_user(
        self,
        phone: str,
        password: str,
        role: str,
        name: str,
    ) -> Dict[str, Any]:
        phone = phone.strip()
        with _lock:
            data = self._read()
            if phone in data["users"]:
                raise ValueError("Phone number already registered.")
            user_id = f"user_{len(data['users']) + 1:06d}"
            data["users"][phone] = {
                "id": user_id,
                "phone": phone,
                "role": role,
                "password_hash": hash_password(password),
                "created_at": _now_iso(),
            }
            data["profiles"][user_id] = {
                "user_id": user_id,
                "name": name,
                "phone": phone,
                "district": None,
                "crop": None,
                "farm_size_acres": None,
                "irrigation_type": None,
                "language": "en",
            }
            self._write(data)
            return data["users"][phone]

    def get_profile(self, user_id: str) -> Optional[Dict[str, Any]]:
        data = self._read()
        return data["profiles"].get(user_id)

    def update_profile(self, user_id: str, updates: Dict[str, Any]) -> Dict[str, Any]:
        allowed = {
            "name",
            "email",
            "district",
            "crop",
            "farm_size_acres",
            "irrigation_type",
            "language",
        }
        with _lock:
            data = self._read()
            profile = data["profiles"].get(user_id)
            if profile is None:
                raise ValueError("Profile not found.")
            for key, value in updates.items():
                if key in allowed:
                    profile[key] = value
            profile["updated_at"] = _now_iso()
            self._write(data)
            return profile

    def record_scan(self, user_id: str, prediction: Dict[str, Any], image_path: str) -> Dict[str, Any]:
        """Append a crop-health scan record for a user."""
        with _lock:
            data = self._read()
            scans = data.setdefault("scans", {})
            user_scans = scans.setdefault(user_id, [])
            record = {
                "scan_id": f"scan_{len(user_scans) + 1:06d}",
                "user_id": user_id,
                "image_path": image_path,
                "predicted_class": prediction.get("predicted_class"),
                "confidence": prediction.get("confidence"),
                "model_version": prediction.get("model_version"),
                "uncertain": prediction.get("uncertain"),
                "scanned_at": _now_iso(),
            }
            user_scans.insert(0, record)
            scans[user_id] = user_scans[:100]  # keep last 100 scans
            self._write(data)
            return record

    def list_scans(self, user_id: str) -> List[Dict[str, Any]]:
        data = self._read()
        return list(data.get("scans", {}).get(user_id, []))

    def list_users(self) -> List[Dict[str, Any]]:
        data = self._read()
        return [
            {"id": u["id"], "phone": u["phone"], "role": u["role"]}
            for u in data["users"].values()
        ]


def _now_iso() -> str:
    from datetime import datetime, timezone

    return datetime.now(timezone.utc).isoformat()


def get_user_store() -> UserStore:
    return UserStore()
