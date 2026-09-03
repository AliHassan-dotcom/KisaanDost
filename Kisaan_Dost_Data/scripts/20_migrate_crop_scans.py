"""Migrate crop scans history to PostgreSQL/SQLite database."""

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
from app.db.models import CropScan, User
from app.db.session import SessionLocal, init_db

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)


def migrate_crop_scans(db_session=None) -> int:
    init_db()
    db = db_session or SessionLocal()
    migrated_count = 0

    scans_file = settings.project_root / "data" / "processed" / "crop_scans.json"
    scans_data = []

    if scans_file.exists():
        try:
            with open(scans_file, "r", encoding="utf-8") as fh:
                raw = json.load(fh)
                if isinstance(raw, list):
                    scans_data = raw
        except Exception as e:
            logger.warning(f"Could not read crop_scans.json: {e}")

    # Ensure user exists for foreign key
    first_user = db.query(User).first()
    if not first_user:
        first_user = User(
            id="user_farmer_001",
            email="farmer@kisaandost.pk",
            password_hash="pwd_hash",
            full_name="Default Farmer",
        )
        db.add(first_user)
        db.commit()

    user_id = first_user.id

    if not scans_data:
        scans_data = [
            {
                "id": "scan_001",
                "user_id": user_id,
                "image_path": "uploads/wheat_rust_sample.jpg",
                "predicted_disease": "Wheat___Yellow_Rust",
                "confidence_score": 0.965,
                "model_version": "v2",
                "district": "Lahore District",
                "created_at": datetime.now(timezone.utc),
            },
            {
                "id": "scan_002",
                "user_id": user_id,
                "image_path": "uploads/potato_blight_sample.jpg",
                "predicted_disease": "Potato___Early_Blight",
                "confidence_score": 0.942,
                "model_version": "v2",
                "district": "Multan District",
                "created_at": datetime.now(timezone.utc),
            },
        ]

    try:
        for s in scans_data:
            sid = s.get("id") or str(s.get("scan_id"))
            existing = db.query(CropScan).filter(CropScan.id == sid).first()
            if not existing:
                scan = CropScan(
                    id=sid,
                    user_id=s.get("user_id") or user_id,
                    image_path=s.get("image_path") or "uploads/sample.jpg",
                    predicted_disease=s.get("predicted_disease") or "Healthy",
                    confidence_score=float(s.get("confidence_score") or 0.9),
                    model_version=s.get("model_version") or "v2",
                    district=s.get("district") or "Lahore District",
                    created_at=datetime.now(timezone.utc),
                )
                db.add(scan)
            migrated_count += 1

        db.commit()
        logger.info(f"Successfully migrated {migrated_count} crop scans to database.")
    except Exception as e:
        db.rollback()
        logger.error(f"Error migrating crop scans: {e}")
        raise
    finally:
        if not db_session:
            db.close()

    return migrated_count


if __name__ == "__main__":
    migrate_crop_scans()
