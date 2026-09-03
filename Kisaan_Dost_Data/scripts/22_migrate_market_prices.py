"""Migrate AMIS Punjab market prices CSV records to PostgreSQL/SQLite database."""

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
from app.db.models import MarketPrice
from app.db.session import SessionLocal, init_db

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)


def migrate_market_prices(db_session=None) -> int:
    init_db()
    db = db_session or SessionLocal()
    migrated_count = 0

    csv_path = settings.amis_prices_csv_full_path()
    if not csv_path.exists():
        logger.warning(f"Market prices CSV not found at {csv_path}")
        return 0

    try:
        now = datetime.now(timezone.utc)
        with open(csv_path, "r", encoding="utf-8") as fh:
            reader = csv.DictReader(fh)
            for r in reader:
                market = r.get("market_name", "").strip()
                commodity = r.get("commodity_name", "").strip()
                p_date = r.get("price_date", "").strip()
                if not market or not commodity:
                    continue

                min_p = float(r["min_price_pkr"]) if r.get("min_price_pkr") and r["min_price_pkr"] != "" else None
                max_p = float(r["max_price_pkr"]) if r.get("max_price_pkr") and r["max_price_pkr"] != "" else None
                fqp_p = float(r["fqp_price_pkr"]) if r.get("fqp_price_pkr") and r["fqp_price_pkr"] != "" else None
                qty = float(r["quantity"]) if r.get("quantity") and r["quantity"] != "" else None
                cid = int(r["commodity_id"]) if r.get("commodity_id") and r["commodity_id"].isdigit() else None

                pid = f"mp_{commodity.lower()}_{market.lower()}_{p_date}".replace(" ", "_")
                existing = db.query(MarketPrice).filter(MarketPrice.id == pid).first()

                if existing:
                    existing.min_price_pkr = min_p
                    existing.max_price_pkr = max_p
                    existing.fqp_price_pkr = fqp_p
                else:
                    item = MarketPrice(
                        id=pid,
                        price_date=p_date,
                        province=r.get("province", "Punjab"),
                        district=r.get("district"),
                        market_name=market,
                        market_id_or_source_label=r.get("market_id_or_source_label"),
                        commodity_name=commodity,
                        commodity_id=cid,
                        variety=r.get("variety"),
                        min_price_pkr=min_p,
                        max_price_pkr=max_p,
                        fqp_price_pkr=fqp_p,
                        quantity=qty,
                        unit=r.get("unit", "100 Kg"),
                        source_name=r.get("source_name", "AMIS Punjab"),
                        source_url=r.get("source_url"),
                        source_displayed_date=r.get("source_displayed_date"),
                        retrieved_at=now,
                        data_status=r.get("data_status", "live"),
                        validation_status=r.get("validation_status", "pass"),
                    )
                    db.add(item)
                migrated_count += 1

        db.commit()
        logger.info(f"Successfully migrated {migrated_count} market price records to database.")
    except Exception as e:
        db.rollback()
        logger.error(f"Error migrating market prices: {e}")
        raise
    finally:
        if not db_session:
            db.close()

    return migrated_count


if __name__ == "__main__":
    migrate_market_prices()
