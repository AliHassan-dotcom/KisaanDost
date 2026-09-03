"""Validator for Agricultural GDP and Trade Datasets (Phase 9)."""

from __future__ import annotations

import csv
import logging
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parent.parent
PROCESSED_DIR = ROOT / "processed"
GDP_CSV = PROCESSED_DIR / "agri_gdp_trends_v1.csv"
EXPORTS_CSV = PROCESSED_DIR / "agri_exports_v1.csv"
IMPORTS_CSV = PROCESSED_DIR / "agri_imports_v1.csv"
SUMMARY_CSV = PROCESSED_DIR / "agri_trade_summary_v1.csv"

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger(__name__)


def validate_gdp() -> bool:
    if not GDP_CSV.exists():
        logger.error(f"GDP CSV not found: {GDP_CSV}")
        return False
    with open(GDP_CSV, "r", encoding="utf-8", newline="") as fh:
        rows = list(csv.DictReader(fh))
    if len(rows) < 5:
        logger.error(f"Too few GDP rows ({len(rows)})")
        return False
    for r in rows:
        share = float(r["agri_gdp_share_pct"])
        if not (15.0 <= share <= 40.0):
            logger.error(f"Invalid agri GDP share: {share}")
            return False
    logger.info(f"GDP validation passed: {len(rows)} records.")
    return True


def validate_trade() -> bool:
    if not EXPORTS_CSV.exists() or not IMPORTS_CSV.exists() or not SUMMARY_CSV.exists():
        logger.error("Missing trade CSV files.")
        return False

    with open(EXPORTS_CSV, "r", encoding="utf-8", newline="") as fh:
        exp_rows = list(csv.DictReader(fh))
    with open(IMPORTS_CSV, "r", encoding="utf-8", newline="") as fh:
        imp_rows = list(csv.DictReader(fh))
    with open(SUMMARY_CSV, "r", encoding="utf-8", newline="") as fh:
        sum_rows = list(csv.DictReader(fh))

    if len(exp_rows) < 4 or len(imp_rows) < 4 or len(sum_rows) < 1:
        logger.error("Too few trade rows.")
        return False

    for r in exp_rows:
        val = float(r["value_million_usd"])
        share = float(r["share_of_agri_exports_pct"])
        if val <= 0 or share <= 0:
            logger.error(f"Invalid export row: {r}")
            return False

    for r in imp_rows:
        val = float(r["value_million_usd"])
        share = float(r["share_of_agri_imports_pct"])
        if val <= 0 or share <= 0:
            logger.error(f"Invalid import row: {r}")
            return False

    for r in sum_rows:
        exp = float(r["total_agri_exports_million_usd"])
        imp = float(r["total_agri_imports_million_usd"])
        bal = float(r["agri_trade_balance_million_usd"])
        if exp <= 0 or imp <= 0:
            logger.error(f"Invalid summary row: {r}")
            return False
        if round(exp - imp, 1) != round(bal, 1):
            logger.error(f"Trade balance mismatch in summary: {exp} - {imp} != {bal}")
            return False

    logger.info(f"Trade validation passed: {len(exp_rows)} exports, {len(imp_rows)} imports, {len(sum_rows)} summaries.")
    return True


def run_full_validation() -> bool:
    return validate_gdp() and validate_trade()


if __name__ == "__main__":
    success = run_full_validation()
    sys.exit(0 if success else 1)
