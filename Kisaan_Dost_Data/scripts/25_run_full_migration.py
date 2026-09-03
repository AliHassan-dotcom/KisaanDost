"""Master migration orchestrator: executes all data migrations and logs migration_metadata."""

from __future__ import annotations

from datetime import datetime, timezone
import hashlib
import importlib
import json
import logging
from pathlib import Path
import sys

repo_root = Path(__file__).resolve().parent.parent.parent
if str(repo_root) not in sys.path:
    sys.path.insert(0, str(repo_root))

from app.config.settings import settings
from app.db.models import (
    CropScan,
    MarketPrice,
    MigrationMetadata,
    Notification,
    User,
    UserPreference,
    WeatherCache,
)
from app.db.session import SessionLocal, init_db

# Dynamically import numeric-prefixed migration modules
m_users = importlib.import_module("Kisaan_Dost_Data.scripts.19_migrate_users")
m_scans = importlib.import_module("Kisaan_Dost_Data.scripts.20_migrate_crop_scans")
m_weather = importlib.import_module("Kisaan_Dost_Data.scripts.21_migrate_weather_cache")
m_market = importlib.import_module("Kisaan_Dost_Data.scripts.22_migrate_market_prices")
m_prefs = importlib.import_module("Kisaan_Dost_Data.scripts.23_migrate_user_preferences")
m_notifs = importlib.import_module("Kisaan_Dost_Data.scripts.24_migrate_notifications")

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)


def compute_files_hash(paths: list[Path]) -> str:
    hasher = hashlib.sha256()
    for p in paths:
        if p.exists():
            with open(p, "rb") as fh:
                while chunk := fh.read(8192):
                    hasher.update(chunk)
    return hasher.hexdigest()


def run_full_migration() -> dict:
    init_db()
    db = SessionLocal()

    source_files = [
        settings.user_store_path(),
        settings.project_root / "data" / "processed" / "crop_scans.json",
        settings.coordinates_csv_full_path(),
        settings.amis_prices_csv_full_path(),
        settings.project_root / "data" / "processed" / "user_preferences.json",
        settings.project_root / "data" / "processed" / "notifications.json",
    ]

    snapshot_hash = compute_files_hash(source_files)
    now = datetime.now(timezone.utc)

    logger.info("Starting Full Database Migration (JSON/CSV -> DB)...")
    logger.info(f"Source snapshot SHA256: {snapshot_hash}")

    row_counts = {}
    try:
        row_counts["users"] = m_users.migrate_users(db_session=db)
        row_counts["crop_scans"] = m_scans.migrate_crop_scans(db_session=db)
        row_counts["weather_cache"] = m_weather.migrate_weather_cache(db_session=db)
        row_counts["market_prices"] = m_market.migrate_market_prices(db_session=db)
        row_counts["user_preferences"] = m_prefs.migrate_user_preferences(db_session=db)
        row_counts["notifications"] = m_notifs.migrate_notifications(db_session=db)

        # Record migration metadata
        meta = MigrationMetadata(
            migration_name="001_initial_json_to_db_migration",
            migrated_at=now,
            source_json_snapshot_hash=snapshot_hash,
            row_counts=row_counts,
            status="success",
        )
        db.add(meta)
        db.commit()

        logger.info(f"Full migration completed successfully! Row counts: {row_counts}")

        return {
            "status": "success",
            "migrated_at": now.isoformat(),
            "snapshot_hash": snapshot_hash,
            "row_counts": row_counts,
        }
    except Exception as e:
        db.rollback()
        logger.error(f"Migration failed: {e}")
        meta = MigrationMetadata(
            migration_name="001_initial_json_to_db_migration",
            migrated_at=now,
            source_json_snapshot_hash=snapshot_hash,
            row_counts=row_counts,
            status="failed",
        )
        db.add(meta)
        db.commit()
        return {
            "status": "failed",
            "error": str(e),
            "migrated_at": now.isoformat(),
            "snapshot_hash": snapshot_hash,
            "row_counts": row_counts,
        }
    finally:
        db.close()


if __name__ == "__main__":
    run_full_migration()
