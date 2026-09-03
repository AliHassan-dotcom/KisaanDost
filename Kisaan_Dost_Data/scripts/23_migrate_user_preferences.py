"""Migrate user notification preferences (user_preferences.json) to PostgreSQL/SQLite database."""

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
from app.db.models import User, UserPreference
from app.db.session import SessionLocal, init_db

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)


def migrate_user_preferences(db_session=None) -> int:
    init_db()
    db = db_session or SessionLocal()
    migrated_count = 0

    pref_file = settings.project_root / "data" / "processed" / "user_preferences.json"
    pref_data = {}

    if pref_file.exists():
        try:
            with open(pref_file, "r", encoding="utf-8") as fh:
                pref_data = json.load(fh)
        except Exception as e:
            logger.warning(f"Could not read user_preferences.json: {e}")

    # Ensure user exists for default
    if not pref_data:
        pref_data = {
            "default_farmer": {
                "user_id": "default_farmer",
                "selected_district": "Lahore District",
                "selected_market": "Lahore",
                "selected_crops": ["Wheat", "Rice Basmati Super (New)", "Cotton", "Potato Fresh"],
                "alert_types": ["weather", "market", "advisory"],
                "channels": ["in_app", "local"],
                "heatwave_temp_threshold": 40.0,
                "rainfall_threshold_mm": 25.0,
                "frost_temp_threshold": 3.0,
                "market_mover_threshold_pct": 10.0,
                "fcm_status": "not_configured",
            }
        }

    try:
        now = datetime.now(timezone.utc)
        for uid, p in pref_data.items():
            # Check or create user
            user = db.query(User).filter(User.id == uid).first()
            if not user:
                user = User(
                    id=uid,
                    email=f"{uid}@kisaandost.pk",
                    password_hash="pwd_hash",
                    full_name="Farmer User",
                    district=p.get("selected_district", "Lahore District"),
                )
                db.add(user)
                db.flush()

            existing = db.query(UserPreference).filter(UserPreference.user_id == uid).first()
            thresholds = {
                "heatwave_temp_threshold": p.get("heatwave_temp_threshold", 40.0),
                "rainfall_threshold_mm": p.get("rainfall_threshold_mm", 25.0),
                "frost_temp_threshold": p.get("frost_temp_threshold", 3.0),
                "market_mover_threshold_pct": p.get("market_mover_threshold_pct", 10.0),
            }

            if existing:
                existing.selected_crops = p.get("selected_crops", [])
                existing.primary_district = p.get("selected_district", "Lahore District")
                existing.primary_market = p.get("selected_market", "Lahore")
                existing.alert_types = p.get("alert_types", ["weather", "market", "advisory"])
                existing.notification_channels = p.get("channels", ["in_app", "local"])
                existing.threshold_settings = thresholds
                existing.fcm_config_status = p.get("fcm_status", "not_configured")
                existing.updated_at = now
            else:
                new_pref = UserPreference(
                    id=f"pref_{uid}",
                    user_id=uid,
                    selected_crops=p.get("selected_crops", []),
                    primary_district=p.get("selected_district", "Lahore District"),
                    primary_market=p.get("selected_market", "Lahore"),
                    alert_types=p.get("alert_types", ["weather", "market", "advisory"]),
                    notification_channels=p.get("channels", ["in_app", "local"]),
                    threshold_settings=thresholds,
                    fcm_config_status=p.get("fcm_status", "not_configured"),
                    updated_at=now,
                )
                db.add(new_pref)
            migrated_count += 1

        db.commit()
        logger.info(f"Successfully migrated {migrated_count} user preferences to database.")
    except Exception as e:
        db.rollback()
        logger.error(f"Error migrating user preferences: {e}")
        raise
    finally:
        if not db_session:
            db.close()

    return migrated_count


if __name__ == "__main__":
    migrate_user_preferences()
