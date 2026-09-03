"""Migrate notifications history (notifications.json) to PostgreSQL/SQLite database."""

from __future__ import annotations

from datetime import datetime, timezone
import json
import logging
from pathlib import Path
import sys

repo_root = Path(__file__).resolve().parent.parent.parent
if str(repo_root) not in sys.path:
    sys.path.insert(0, str(repo_root))

from app.config.settings import settings
from app.db.models import Notification, User
from app.db.session import SessionLocal, init_db

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)


def migrate_notifications(db_session=None) -> int:
    init_db()
    db = db_session or SessionLocal()
    migrated_count = 0

    notif_file = settings.project_root / "data" / "processed" / "notifications.json"
    notif_data = []

    if notif_file.exists():
        try:
            with open(notif_file, "r", encoding="utf-8") as fh:
                notif_data = json.load(fh)
        except Exception as e:
            logger.warning(f"Could not read notifications.json: {e}")

    try:
        now = datetime.now(timezone.utc)
        for n in notif_data:
            nid = n.get("id") or str(n.get("notification_id"))
            uid = n.get("user_id") or "default_farmer"

            # Check or create user
            user = db.query(User).filter(User.id == uid).first()
            if not user:
                user = User(
                    id=uid,
                    email=f"{uid}@kisaandost.pk",
                    password_hash="pwd_hash",
                    full_name="Farmer User",
                )
                db.add(user)
                db.flush()

            existing = db.query(Notification).filter(Notification.id == nid).first()
            if not existing:
                notif = Notification(
                    id=nid,
                    user_id=uid,
                    type=n.get("type", "advisory_reminder"),
                    title=n.get("title", ""),
                    body=n.get("body") or n.get("message", ""),
                    body_urdu=n.get("body_urdu") or n.get("message_ur", ""),
                    severity=n.get("severity", "info"),
                    metadata_json=n.get("metadata", {}),
                    created_at=now,
                    read_at=now if n.get("is_read") else None,
                    source_attribution=n.get("source_attribution", "Official Source"),
                )
                db.add(notif)
            migrated_count += 1

        db.commit()
        logger.info(f"Successfully migrated {migrated_count} notifications to database.")
    except Exception as e:
        db.rollback()
        logger.error(f"Error migrating notifications: {e}")
        raise
    finally:
        if not db_session:
            db.close()

    return migrated_count


if __name__ == "__main__":
    migrate_notifications()
