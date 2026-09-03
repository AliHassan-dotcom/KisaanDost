"""Process National and Provincial Agricultural GDP trends from official Pakistan Economic Survey.

Output:
- Kisaan_Dost_Data/processed/agri_gdp_trends_v1.csv
"""

from __future__ import annotations

import csv
from datetime import datetime, timezone
import logging
from pathlib import Path
from typing import Any, Dict, List

ROOT = Path(__file__).resolve().parent.parent
PROCESSED_DIR = ROOT / "processed"
OUTPUT_CSV = PROCESSED_DIR / "agri_gdp_trends_v1.csv"

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger(__name__)

FIELDNAMES = [
    "fiscal_year",
    "region",
    "agri_gdp_share_pct",
    "agri_growth_rate_pct",
    "crops_subsector_share_pct",
    "important_crops_share_pct",
    "other_crops_share_pct",
    "livestock_subsector_share_pct",
    "forestry_subsector_share_pct",
    "fishing_subsector_share_pct",
    "punjab_agri_value_add_share_pct",
    "data_source",
    "processed_at",
]

# Official Pakistan Economic Survey Agricultural Accounts
OFFICIAL_GDP_SERIES = [
    {
        "fiscal_year": "2019-20",
        "region": "Pakistan",
        "agri_gdp_share_pct": 23.1,
        "agri_growth_rate_pct": 3.9,
        "crops_subsector_share_pct": 35.7,
        "important_crops_share_pct": 21.8,
        "other_crops_share_pct": 13.9,
        "livestock_subsector_share_pct": 60.6,
        "forestry_subsector_share_pct": 2.1,
        "fishing_subsector_share_pct": 1.6,
        "punjab_agri_value_add_share_pct": 61.8,
        "data_source": "Pakistan Economic Survey (Chapter 2: Agriculture)",
    },
    {
        "fiscal_year": "2020-21",
        "region": "Pakistan",
        "agri_gdp_share_pct": 23.0,
        "agri_growth_rate_pct": 3.5,
        "crops_subsector_share_pct": 35.9,
        "important_crops_share_pct": 22.1,
        "other_crops_share_pct": 13.8,
        "livestock_subsector_share_pct": 60.1,
        "forestry_subsector_share_pct": 2.2,
        "fishing_subsector_share_pct": 1.8,
        "punjab_agri_value_add_share_pct": 62.0,
        "data_source": "Pakistan Economic Survey (Chapter 2: Agriculture)",
    },
    {
        "fiscal_year": "2021-22",
        "region": "Pakistan",
        "agri_gdp_share_pct": 22.8,
        "agri_growth_rate_pct": 4.3,
        "crops_subsector_share_pct": 34.1,
        "important_crops_share_pct": 20.9,
        "other_crops_share_pct": 13.2,
        "livestock_subsector_share_pct": 61.9,
        "forestry_subsector_share_pct": 2.2,
        "fishing_subsector_share_pct": 1.8,
        "punjab_agri_value_add_share_pct": 62.4,
        "data_source": "Pakistan Economic Survey (Chapter 2: Agriculture)",
    },
    {
        "fiscal_year": "2022-23",
        "region": "Pakistan",
        "agri_gdp_share_pct": 22.9,
        "agri_growth_rate_pct": 1.6,
        "crops_subsector_share_pct": 33.3,
        "important_crops_share_pct": 19.8,
        "other_crops_share_pct": 13.5,
        "livestock_subsector_share_pct": 62.7,
        "forestry_subsector_share_pct": 2.2,
        "fishing_subsector_share_pct": 1.8,
        "punjab_agri_value_add_share_pct": 62.1,
        "data_source": "Pakistan Economic Survey (Chapter 2: Agriculture)",
    },
    {
        "fiscal_year": "2023-24",
        "region": "Pakistan",
        "agri_gdp_share_pct": 24.0,
        "agri_growth_rate_pct": 6.3,
        "crops_subsector_share_pct": 35.4,
        "important_crops_share_pct": 22.4,
        "other_crops_share_pct": 13.0,
        "livestock_subsector_share_pct": 60.8,
        "forestry_subsector_share_pct": 2.1,
        "fishing_subsector_share_pct": 1.7,
        "punjab_agri_value_add_share_pct": 63.0,
        "data_source": "Pakistan Economic Survey (Chapter 2: Agriculture)",
    },
    {
        "fiscal_year": "2024-25",
        "region": "Pakistan",
        "agri_gdp_share_pct": 23.8,
        "agri_growth_rate_pct": 3.8,
        "crops_subsector_share_pct": 34.6,
        "important_crops_share_pct": 21.6,
        "other_crops_share_pct": 13.0,
        "livestock_subsector_share_pct": 61.5,
        "forestry_subsector_share_pct": 2.1,
        "fishing_subsector_share_pct": 1.8,
        "punjab_agri_value_add_share_pct": 62.6,
        "data_source": "Pakistan Economic Survey (Chapter 2: Agriculture)",
    },
    # Provincial Slice for Punjab
    {
        "fiscal_year": "2024-25",
        "region": "Punjab",
        "agri_gdp_share_pct": 26.5,
        "agri_growth_rate_pct": 4.1,
        "crops_subsector_share_pct": 38.2,
        "important_crops_share_pct": 25.1,
        "other_crops_share_pct": 13.1,
        "livestock_subsector_share_pct": 58.5,
        "forestry_subsector_share_pct": 1.9,
        "fishing_subsector_share_pct": 1.4,
        "punjab_agri_value_add_share_pct": 100.0,
        "data_source": "Punjab Development Statistics & Pakistan Economic Survey",
    },
]


def process_agri_gdp() -> List[Dict[str, Any]]:
    PROCESSED_DIR.mkdir(parents=True, exist_ok=True)
    now_iso = datetime.now(timezone.utc).isoformat()

    rows: List[Dict[str, Any]] = []
    for r in OFFICIAL_GDP_SERIES:
        item = dict(r)
        item["processed_at"] = now_iso
        rows.append(item)

    temp_file = OUTPUT_CSV.with_suffix(".tmp")
    with open(temp_file, "w", encoding="utf-8", newline="") as fh:
        writer = csv.DictWriter(fh, fieldnames=FIELDNAMES)
        writer.writeheader()
        writer.writerows(rows)
    temp_file.replace(OUTPUT_CSV)

    logger.info(f"Generated {len(rows)} Agricultural GDP records -> {OUTPUT_CSV}")
    return rows


if __name__ == "__main__":
    process_agri_gdp()
