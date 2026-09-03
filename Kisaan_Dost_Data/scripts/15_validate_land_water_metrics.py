"""Validator for district land utilization and water availability datasets (Phase 8)."""

from __future__ import annotations

import csv
import logging
from pathlib import Path
import sys
from typing import Dict, List

ROOT = Path(__file__).resolve().parent.parent
PROCESSED_DIR = ROOT / "processed"
LAND_CSV = PROCESSED_DIR / "district_land_utilization_v1.csv"
WATER_CSV = PROCESSED_DIR / "district_water_availability_v1.csv"

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger(__name__)


def validate_land_utilization() -> bool:
    if not LAND_CSV.exists():
        logger.error(f"Land utilization CSV not found at {LAND_CSV}")
        return False

    with open(LAND_CSV, "r", encoding="utf-8", newline="") as fh:
        rows = list(csv.DictReader(fh))

    if len(rows) < 30:
        logger.error(f"Land utilization row count ({len(rows)}) below minimum 30 districts.")
        return False

    for r in rows:
        dist = r["district"]
        tot_farm = float(r["total_farm_area_acres"])
        cult = float(r["cultivated_area_acres"])
        uncult = float(r["uncultivated_area_acres"])
        cropped = float(r["total_cropped_area_acres"])
        cult_pct = float(r["cultivated_share_pct"])

        if tot_farm <= 0:
            logger.error(f"[{dist}] Invalid total farm area: {tot_farm}")
            return False

        if cult < 0 or uncult < 0 or cropped < 0:
            logger.error(f"[{dist}] Negative acreage values found.")
            return False

        if not (0.0 <= cult_pct <= 100.0):
            logger.error(f"[{dist}] Cultivated share percentage out of bounds: {cult_pct}")
            return False

    logger.info(f"Land utilization validation passed: {len(rows)} districts validated.")
    return True


def validate_water_availability() -> bool:
    if not WATER_CSV.exists():
        logger.error(f"Water availability CSV not found at {WATER_CSV}")
        return False

    with open(WATER_CSV, "r", encoding="utf-8", newline="") as fh:
        rows = list(csv.DictReader(fh))

    if len(rows) < 30:
        logger.error(f"Water availability row count ({len(rows)}) below minimum 30 districts.")
        return False

    for r in rows:
        dist = r["district"]
        cult = float(r["total_cultivated_area_acres"])
        irrig = float(r["irrigated_area_acres"])
        cov_pct = float(r["irrigation_coverage_pct"])
        barani_pct = float(r["barani_share_pct"])

        if cult <= 0:
            logger.error(f"[{dist}] Invalid cultivated area: {cult}")
            return False

        if irrig < 0 or cov_pct < 0 or barani_pct < 0:
            logger.error(f"[{dist}] Negative values in water availability.")
            return False

        if not (0.0 <= cov_pct <= 100.0):
            logger.error(f"[{dist}] Irrigation coverage percentage out of bounds: {cov_pct}")
            return False

    logger.info(f"Water availability validation passed: {len(rows)} districts validated.")
    return True


def run_full_validation() -> bool:
    v1 = validate_land_utilization()
    v2 = validate_water_availability()
    return v1 and v2


if __name__ == "__main__":
    success = run_full_validation()
    sys.exit(0 if success else 1)
