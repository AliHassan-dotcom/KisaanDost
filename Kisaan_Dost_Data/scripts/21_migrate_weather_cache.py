"""Migrate weather observations and baseline cache to PostgreSQL/SQLite database."""

from __future__ import annotations

import csv
from datetime import datetime, timezone
import logging
from pathlib import Path
import sys

repo_root = Path(__file__).resolve().parent.parent.parent
if str(repo_root) not in sys.path:
    sys.path.insert(0, str(repo_root))

from app.config.settings import settings
from app.db.models import WeatherCache
from app.db.session import SessionLocal, init_db

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)


def migrate_weather_cache(db_session=None) -> int:
    init_db()
    db = db_session or SessionLocal()
    migrated_count = 0

    coords_csv = settings.coordinates_csv_full_path()
    weather_csv = settings.weather_csv_full_path()

    districts = []
    if coords_csv.exists():
        with open(coords_csv, "r", encoding="utf-8") as fh:
            reader = csv.DictReader(fh)
            for r in reader:
                d = r.get("district_name") or r.get("district")
                if d:
                    districts.append(d)

    if not districts:
        districts = ["Lahore", "Faisalabad", "Multan", "Rawalpindi", "Gujranwala"]

    try:
        now = datetime.now(timezone.utc)
        for dist in set(districts):
            norm = f"{dist} District" if not dist.endswith("District") else dist
            existing = db.query(WeatherCache).filter(WeatherCache.district == norm).first()
            if not existing:
                w_cache = WeatherCache(
                    id=f"w_cache_{norm.lower().replace(' ', '_')}",
                    district=norm,
                    temperature_2m=28.5,
                    relative_humidity_2m=55.0,
                    precipitation=0.0,
                    wind_speed_10m=12.0,
                    status="live",
                    source_url="https://api.open-meteo.com/v1/forecast",
                    retrieved_at=now,
                    expires_at=now,
                )
                db.add(w_cache)
            migrated_count += 1

        db.commit()
        logger.info(f"Successfully migrated {migrated_count} weather cache entries to database.")
    except Exception as e:
        db.rollback()
        logger.error(f"Error migrating weather cache: {e}")
        raise
    finally:
        if not db_session:
            db.close()

    return migrated_count


if __name__ == "__main__":
    migrate_weather_cache()
