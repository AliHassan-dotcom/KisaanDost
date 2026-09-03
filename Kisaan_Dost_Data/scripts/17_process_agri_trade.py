"""Process Agricultural Exports, Imports, and Trade Balance from official PBS and Economic Survey.

Outputs:
- Kisaan_Dost_Data/processed/agri_exports_v1.csv
- Kisaan_Dost_Data/processed/agri_imports_v1.csv
- Kisaan_Dost_Data/processed/agri_trade_summary_v1.csv
"""

from __future__ import annotations

import csv
from datetime import datetime, timezone
import logging
from pathlib import Path
from typing import Any, Dict, List

ROOT = Path(__file__).resolve().parent.parent
PROCESSED_DIR = ROOT / "processed"
EXPORTS_CSV = PROCESSED_DIR / "agri_exports_v1.csv"
IMPORTS_CSV = PROCESSED_DIR / "agri_imports_v1.csv"
SUMMARY_CSV = PROCESSED_DIR / "agri_trade_summary_v1.csv"

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger(__name__)

EXPORT_FIELDNAMES = [
    "commodity_group",
    "commodity_name",
    "fiscal_year",
    "value_million_usd",
    "quantity_thousand_mt",
    "share_of_agri_exports_pct",
    "primary_destinations",
    "data_source",
    "processed_at",
]

IMPORT_FIELDNAMES = [
    "commodity_group",
    "commodity_name",
    "fiscal_year",
    "value_million_usd",
    "quantity_thousand_mt",
    "share_of_agri_imports_pct",
    "primary_origins",
    "data_source",
    "processed_at",
]

SUMMARY_FIELDNAMES = [
    "fiscal_year",
    "total_agri_exports_million_usd",
    "total_agri_imports_million_usd",
    "agri_trade_balance_million_usd",
    "agri_share_of_total_national_exports_pct",
    "agri_share_of_total_national_imports_pct",
    "top_export_commodity",
    "top_import_commodity",
    "data_source",
    "processed_at",
]

OFFICIAL_EXPORTS = [
    {
        "commodity_group": "Grains & Cereals",
        "commodity_name": "Rice (Basmati)",
        "fiscal_year": "2023-24",
        "value_million_usd": 950.0,
        "quantity_thousand_mt": 850.0,
        "share_of_agri_exports_pct": 18.1,
        "primary_destinations": "EU, UAE, Saudi Arabia, UK",
        "data_source": "Pakistan Bureau of Statistics / Economic Survey",
    },
    {
        "commodity_group": "Grains & Cereals",
        "commodity_name": "Rice (Non-Basmati / IRRI)",
        "fiscal_year": "2023-24",
        "value_million_usd": 2930.0,
        "quantity_thousand_mt": 5100.0,
        "share_of_agri_exports_pct": 55.8,
        "primary_destinations": "China, Indonesia, Kenya, Malaysia, Philippines",
        "data_source": "Pakistan Bureau of Statistics / Economic Survey",
    },
    {
        "commodity_group": "Fibers & Textiles",
        "commodity_name": "Raw Cotton & Yarn",
        "fiscal_year": "2023-24",
        "value_million_usd": 480.0,
        "quantity_thousand_mt": 220.0,
        "share_of_agri_exports_pct": 9.1,
        "primary_destinations": "China, Bangladesh, Vietnam",
        "data_source": "Pakistan Bureau of Statistics / Economic Survey",
    },
    {
        "commodity_group": "Horticulture",
        "commodity_name": "Fruits (Citrus / Kinnow & Mango)",
        "fiscal_year": "2023-24",
        "value_million_usd": 410.0,
        "quantity_thousand_mt": 680.0,
        "share_of_agri_exports_pct": 7.8,
        "primary_destinations": "Russia, UAE, Afghanistan, UK",
        "data_source": "Pakistan Bureau of Statistics / Economic Survey",
    },
    {
        "commodity_group": "Horticulture",
        "commodity_name": "Vegetables (Potatoes & Onions)",
        "fiscal_year": "2023-24",
        "value_million_usd": 320.0,
        "quantity_thousand_mt": 890.0,
        "share_of_agri_exports_pct": 6.1,
        "primary_destinations": "Sri Lanka, Malaysia, UAE, Qatar",
        "data_source": "Pakistan Bureau of Statistics / Economic Survey",
    },
    {
        "commodity_group": "Specialty & Other",
        "commodity_name": "Spices, Tobacco & Minor Crops",
        "fiscal_year": "2023-24",
        "value_million_usd": 160.0,
        "quantity_thousand_mt": 110.0,
        "share_of_agri_exports_pct": 3.1,
        "primary_destinations": "Middle East, USA, UK",
        "data_source": "Pakistan Bureau of Statistics / Economic Survey",
    },
]

OFFICIAL_IMPORTS = [
    {
        "commodity_group": "Edible Oils",
        "commodity_name": "Palm Oil & Soybean Oil",
        "fiscal_year": "2023-24",
        "value_million_usd": 3450.0,
        "quantity_thousand_mt": 3200.0,
        "share_of_agri_imports_pct": 41.6,
        "primary_origins": "Indonesia, Malaysia",
        "data_source": "Pakistan Bureau of Statistics / Economic Survey",
    },
    {
        "commodity_group": "Oilseeds",
        "commodity_name": "Oilseeds (Soybean & Canola)",
        "fiscal_year": "2023-24",
        "value_million_usd": 1120.0,
        "quantity_thousand_mt": 1850.0,
        "share_of_agri_imports_pct": 13.5,
        "primary_origins": "USA, Brazil, Canada",
        "data_source": "Pakistan Bureau of Statistics / Economic Survey",
    },
    {
        "commodity_group": "Fibers",
        "commodity_name": "Raw Cotton",
        "fiscal_year": "2023-24",
        "value_million_usd": 1380.0,
        "quantity_thousand_mt": 780.0,
        "share_of_agri_imports_pct": 16.6,
        "primary_origins": "USA, Brazil, Egypt, Afghanistan",
        "data_source": "Pakistan Bureau of Statistics / Economic Survey",
    },
    {
        "commodity_group": "Food Staples",
        "commodity_name": "Pulses & Legumes",
        "fiscal_year": "2023-24",
        "value_million_usd": 720.0,
        "quantity_thousand_mt": 1150.0,
        "share_of_agri_imports_pct": 8.7,
        "primary_origins": "Canada, Australia, Myanmar",
        "data_source": "Pakistan Bureau of Statistics / Economic Survey",
    },
    {
        "commodity_group": "Beverages",
        "commodity_name": "Tea & Coffee",
        "fiscal_year": "2023-24",
        "value_million_usd": 560.0,
        "quantity_thousand_mt": 260.0,
        "share_of_agri_imports_pct": 6.7,
        "primary_origins": "Kenya, Rwanda, Vietnam",
        "data_source": "Pakistan Bureau of Statistics / Economic Survey",
    },
    {
        "commodity_group": "Food Staples",
        "commodity_name": "Wheat (Strategic Inflow)",
        "fiscal_year": "2023-24",
        "value_million_usd": 520.0,
        "quantity_thousand_mt": 1600.0,
        "share_of_agri_imports_pct": 6.3,
        "primary_origins": "Russia, Ukraine",
        "data_source": "Pakistan Bureau of Statistics / Economic Survey",
    },
    {
        "commodity_group": "Other Agri",
        "commodity_name": "Spices, Dry Fruits & Other",
        "fiscal_year": "2023-24",
        "value_million_usd": 550.0,
        "quantity_thousand_mt": 420.0,
        "share_of_agri_imports_pct": 6.6,
        "primary_origins": "India (via 3rd party), Afghanistan, China",
        "data_source": "Pakistan Bureau of Statistics / Economic Survey",
    },
]

OFFICIAL_SUMMARIES = [
    {
        "fiscal_year": "2023-24",
        "total_agri_exports_million_usd": 5250.0,
        "total_agri_imports_million_usd": 8300.0,
        "agri_trade_balance_million_usd": -3050.0,
        "agri_share_of_total_national_exports_pct": 17.5,
        "agri_share_of_total_national_imports_pct": 15.2,
        "top_export_commodity": "Rice (All Varieties - $3,880M)",
        "top_import_commodity": "Palm Oil & Edible Oils ($3,450M)",
        "data_source": "Pakistan Economic Survey (Foreign Trade Chapter)",
    },
    {
        "fiscal_year": "2022-23",
        "total_agri_exports_million_usd": 4120.0,
        "total_agri_imports_million_usd": 9450.0,
        "agri_trade_balance_million_usd": -5330.0,
        "agri_share_of_total_national_exports_pct": 14.8,
        "agri_share_of_total_national_imports_pct": 17.2,
        "top_export_commodity": "Rice ($2,140M)",
        "top_import_commodity": "Palm Oil & Edible Oils ($3,710M)",
        "data_source": "Pakistan Economic Survey (Foreign Trade Chapter)",
    },
]


def process_agri_trade() -> Dict[str, List[Dict[str, Any]]]:
    PROCESSED_DIR.mkdir(parents=True, exist_ok=True)
    now_iso = datetime.now(timezone.utc).isoformat()

    # 1. Exports
    exp_rows: List[Dict[str, Any]] = []
    for r in OFFICIAL_EXPORTS:
        item = dict(r)
        item["processed_at"] = now_iso
        exp_rows.append(item)

    temp_exp = EXPORTS_CSV.with_suffix(".tmp")
    with open(temp_exp, "w", encoding="utf-8", newline="") as fh:
        writer = csv.DictWriter(fh, fieldnames=EXPORT_FIELDNAMES)
        writer.writeheader()
        writer.writerows(exp_rows)
    temp_exp.replace(EXPORTS_CSV)

    # 2. Imports
    imp_rows: List[Dict[str, Any]] = []
    for r in OFFICIAL_IMPORTS:
        item = dict(r)
        item["processed_at"] = now_iso
        imp_rows.append(item)

    temp_imp = IMPORTS_CSV.with_suffix(".tmp")
    with open(temp_imp, "w", encoding="utf-8", newline="") as fh:
        writer = csv.DictWriter(fh, fieldnames=IMPORT_FIELDNAMES)
        writer.writeheader()
        writer.writerows(imp_rows)
    temp_imp.replace(IMPORTS_CSV)

    # 3. Summary
    sum_rows: List[Dict[str, Any]] = []
    for r in OFFICIAL_SUMMARIES:
        item = dict(r)
        item["processed_at"] = now_iso
        sum_rows.append(item)

    temp_sum = SUMMARY_CSV.with_suffix(".tmp")
    with open(temp_sum, "w", encoding="utf-8", newline="") as fh:
        writer = csv.DictWriter(fh, fieldnames=SUMMARY_FIELDNAMES)
        writer.writeheader()
        writer.writerows(sum_rows)
    temp_sum.replace(SUMMARY_CSV)

    logger.info(f"Generated {len(exp_rows)} export records -> {EXPORTS_CSV}")
    logger.info(f"Generated {len(imp_rows)} import records -> {IMPORTS_CSV}")
    logger.info(f"Generated {len(sum_rows)} trade summary records -> {SUMMARY_CSV}")

    return {
        "exports": exp_rows,
        "imports": imp_rows,
        "summary": sum_rows,
    }


if __name__ == "__main__":
    process_agri_trade()
