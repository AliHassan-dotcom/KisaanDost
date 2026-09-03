"""Migrate users from JSON store (data/store/users.json) to PostgreSQL/SQLite database."""

from __future__ import annotations

from datetime import datetime, timezone
import json
import logging
from pathlib import Path
import sys

# Ensure repo root in sys.path
repo_root = Path(__file__).resolve().parent.parent.parent
if str(repo_root) not in sys.path:
    sys.path.insert(0, str(repo_root))

from app.config.settings import settings
from app.db.models import User
from app.db.session import SessionLocal, init_db

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)


def migrate_users(db_session=None) -> int:
    init_db()
    db = db_session or SessionLocal()
    migrated_count = 0

    user_store = settings.user_store_path()
    users_data = []

    if user_store.exists():
        try:
            with open(user_store, "r", encoding="utf-8") as fh:
                raw = json.load(fh)
                if isinstance(raw, list):
                    users_data = raw
                elif isinstance(raw, dict):
                    users_data = list(raw.values())
        except Exception as e:
            logger.warning(f"Could not read user store: {e}")

    # If user store empty, seed default test users
    if not users_data:
        users_data = [
            {
                "id": "user_farmer_001",
                "email": "farmer@kisaandost.pk",
                "password_hash": "$2b$12$e8Y5tGq6R2bL8uT1XJ6Oeu7mJ5pX8k7V4F2q9.W8r2c3s4d5e6f7g",
                "full_name": "Muhammad Ali Farmer",
                "phone_number": "+923001234567",
                "district": "Lahore District",
            },
            {
                "id": "user_admin_001",
                "email": "admin@kisaandost.pk",
                "password_hash": "$2b$12$e8Y5tGq6R2bL8uT1XJ6Oeu7mJ5pX8k7V4F2q9.W8r2c3s4d5e6f7g",
                "full_name": "Kisaan Dost Admin",
                "phone_number": "+923007654321",
                "district": "Lahore District",
            },
        ]

    try:
        for u in users_data:
            uid = u.get("id") or str(u.get("user_id"))
            email = u.get("email")
            if not email:
                continue

            existing = db.query(User).filter((User.id == uid) | (User.email == email)).first()
            if existing:
                existing.full_name = u.get("full_name") or existing.full_name
                existing.phone_number = u.get("phone_number") or existing.phone_number
                existing.district = u.get("district") or existing.district
            else:
                new_user = User(
                    id=uid,
                    email=email,
                    password_hash=u.get("password_hash") or "hashed_pwd",
                    full_name=u.get("full_name") or "Farmer User",
                    phone_number=u.get("phone_number"),
                    district=u.get("district") or "Lahore District",
                    created_at=datetime.now(timezone.utc),
                    updated_at=datetime.now(timezone.utc),
                )
                db.add(new_user)
            migrated_count += 1

        db.commit()
        logger.info(f"Successfully migrated {migrated_count} users to database.")
    except Exception as e:
        db.rollback()
        logger.error(f"Error migrating users: {e}")
        raise
    finally:
        if not db_session:
            db.close()

    return migrated_count


if __name__ == "__main__":
    migrate_users()
