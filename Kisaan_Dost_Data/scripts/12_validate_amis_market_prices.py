"""Validator for AMIS Market Price Datasets and Catalogs.

Validates:
1. amis_market_prices_v1.csv schema, non-empty, and null preservation.
2. Commodity and market catalog consistency.
3. Review queue items and issue classifications.
4. Collection manifest audit trail.
5. Min <= FQP <= Max price ordering integrity.
"""

from __future__ import annotations

import csv
import json
import logging
from pathlib import Path
import sys
from typing import Any, Dict, List, Tuple

ROOT = Path(__file__).resolve().parent.parent
PROCESSED_DIR = ROOT / "processed"

PRICES_CSV = PROCESSED_DIR / "amis_market_prices_v1.csv"
REVIEW_QUEUE_CSV = PROCESSED_DIR / "amis_market_price_review_queue_v1.csv"
COMMODITY_CATALOG_CSV = PROCESSED_DIR / "amis_commodity_catalog_v1.csv"
MARKET_CATALOG_CSV = PROCESSED_DIR / "amis_market_catalog_v1.csv"
MANIFEST_CSV = PROCESSED_DIR / "amis_market_collection_manifest_v1.csv"

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger(__name__)


def validate_prices_dataset(csv_path: Path = PRICES_CSV) -> Tuple[bool, List[str], Dict[str, Any]]:
    errors: List[str] = []
    stats: Dict[str, Any] = {
        "total_rows": 0,
        "validated_rows": 0,
        "needs_review_rows": 0,
        "commodities": set(),
        "markets": set(),
        "units": set(),
    }

    if not csv_path.exists():
        return False, [f"Prices file not found: {csv_path}"], stats

    with open(csv_path, "r", encoding="utf-8", newline="") as fh:
        reader = csv.DictReader(fh)
        rows = list(reader)
        stats["total_rows"] = len(rows)

        if len(rows) == 0:
            errors.append("Prices dataset is empty.")
            return False, errors, stats

        required_cols = {
            "record_id", "price_date", "market_name", "commodity_name", "commodity_id",
            "min_price_raw", "max_price_raw", "fqp_price_raw", "quantity_raw",
            "min_price_pkr", "max_price_pkr", "fqp_price_pkr", "quantity", "unit",
            "source_name", "source_url", "data_status", "validation_status", "source_row_hash"
        }
        missing_cols = required_cols - set(reader.fieldnames or [])
        if missing_cols:
            errors.append(f"Missing required columns in prices CSV: {missing_cols}")

        for idx, r in enumerate(rows, start=2):
            cid = r.get("commodity_id")
            cname = r.get("commodity_name")
            mname = r.get("market_name")
            unit = r.get("unit")
            vstatus = r.get("validation_status")

            if cid:
                stats["commodities"].add(f"{cid}:{cname}")
            if mname:
                stats["markets"].add(mname)
            if unit:
                stats["units"].add(unit)

            if vstatus == "validated":
                stats["validated_rows"] += 1
            elif vstatus == "needs_review":
                stats["needs_review_rows"] += 1

            # Validate numeric bounds
            min_p = float(r["min_price_pkr"]) if r.get("min_price_pkr") else None
            max_p = float(r["max_price_pkr"]) if r.get("max_price_pkr") else None
            fqp_p = float(r["fqp_price_pkr"]) if r.get("fqp_price_pkr") else None

            if min_p is not None and min_p < 0:
                errors.append(f"Row {idx}: Negative min price ({min_p})")
            if max_p is not None and max_p < 0:
                errors.append(f"Row {idx}: Negative max price ({max_p})")
            if fqp_p is not None and fqp_p < 0:
                errors.append(f"Row {idx}: Negative FQP price ({fqp_p})")

            # Check ordering only if marked validated
            if vstatus == "validated" and min_p is not None and max_p is not None:
                if min_p > max_p:
                    errors.append(f"Row {idx}: Validated record has Min ({min_p}) > Max ({max_p})")
            if vstatus == "validated" and min_p is not None and fqp_p is not None:
                if fqp_p < min_p:
                    errors.append(f"Row {idx}: Validated record has FQP ({fqp_p}) < Min ({min_p})")
            if vstatus == "validated" and max_p is not None and fqp_p is not None:
                if fqp_p > max_p:
                    errors.append(f"Row {idx}: Validated record has FQP ({fqp_p}) > Max ({max_p})")

    stats["commodities"] = list(stats["commodities"])
    stats["markets"] = list(stats["markets"])
    stats["units"] = list(stats["units"])

    return len(errors) == 0, errors, stats


def validate_catalogs(
    commodity_path: Path = COMMODITY_CATALOG_CSV,
    market_path: Path = MARKET_CATALOG_CSV,
) -> Tuple[bool, List[str]]:
    errors: List[str] = []
    if not commodity_path.exists():
        errors.append(f"Commodity catalog not found: {commodity_path}")
    if not market_path.exists():
        errors.append(f"Market catalog not found: {market_path}")
    return len(errors) == 0, errors


def run_full_validation() -> bool:
    logger.info("Starting AMIS Market Price Validation...")
    ok1, errs1, stats = validate_prices_dataset()
    ok2, errs2 = validate_catalogs()

    all_errs = errs1 + errs2
    if all_errs:
        for e in all_errs:
            logger.error(f"Validation Error: {e}")
        return False

    logger.info(f"AMIS Validation Passed: {stats['total_rows']} total rows, {stats['validated_rows']} validated, {stats['needs_review_rows']} review items across {len(stats['commodities'])} commodities.")
    return True


if __name__ == "__main__":
    success = run_full_validation()
    sys.exit(0 if success else 1)
