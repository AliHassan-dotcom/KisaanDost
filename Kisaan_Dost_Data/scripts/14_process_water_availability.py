"""Process district water availability, irrigation source reliance, and water stress metrics.

Input:
- Kisaan_Dost_Data/processed/pbs_irrigation.csv

Output:
- Kisaan_Dost_Data/processed/district_water_availability_v1.csv
"""

from __future__ import annotations

import csv
from datetime import datetime, timezone
import logging
from pathlib import Path
from typing import Any, Dict, List, Optional

ROOT = Path(__file__).resolve().parent.parent
PROCESSED_DIR = ROOT / "processed"
IRRIGATION_CSV = PROCESSED_DIR / "pbs_irrigation.csv"
OUTPUT_CSV = PROCESSED_DIR / "district_water_availability_v1.csv"

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger(__name__)

FIELDNAMES = [
    "district",
    "total_cultivated_area_acres",
    "irrigated_area_acres",
    "unirrigated_area_acres",
    "irrigation_coverage_pct",
    "canal_only_acres",
    "canal_only_pct",
    "canal_and_tubewell_acres",
    "canal_and_tubewell_pct",
    "tubewell_only_acres",
    "tubewell_only_pct",
    "barani_rainfed_acres",
    "barani_share_pct",
    "sailaba_flood_acres",
    "other_sources_acres",
    "groundwater_reliance_pct",
    "canal_surface_reliance_pct",
    "primary_irrigation_mode",
    "water_source_classification",
    "provincial_annual_canal_withdrawals_maf",
    "provincial_per_capita_water_m3_year",
    "falkenmark_stress_category",
    "data_source",
    "source_year",
    "processed_at",
]


def _safe_float(val: Any) -> float:
    if val is None:
        return 0.0
    s = str(val).strip().replace(",", "")
    if not s or s in {"-", "N/A", "NA", "--"}:
        return 0.0
    try:
        return float(s)
    except ValueError:
        return 0.0


def process_water_availability() -> List[Dict[str, Any]]:
    if not IRRIGATION_CSV.exists():
        raise FileNotFoundError(f"PBS irrigation input CSV not found at {IRRIGATION_CSV}")

    now_iso = datetime.now(timezone.utc).isoformat()
    rows: List[Dict[str, Any]] = []

    with open(IRRIGATION_CSV, "r", encoding="utf-8", newline="") as fh:
        reader = csv.DictReader(fh)
        for r in reader:
            dist = r["district"].strip()
            total_cult = _safe_float(r.get("total_cultivated_area"))
            irrigated = _safe_float(r.get("irrigated_area"))
            unirrigated = _safe_float(r.get("unirrigated_area"))
            canal = _safe_float(r.get("canal_area"))
            canal_tw = _safe_float(r.get("canal_and_tubewell_area"))
            tw = _safe_float(r.get("tubewell_area"))
            barani = _safe_float(r.get("barani_area"))
            sailaba = _safe_float(r.get("sailaba_area"))
            other = _safe_float(r.get("other_irrigation_area"))

            cov_pct = round((irrigated / total_cult * 100.0), 2) if total_cult > 0 else 0.0
            canal_pct = round((canal / irrigated * 100.0), 2) if irrigated > 0 else 0.0
            canal_tw_pct = round((canal_tw / irrigated * 100.0), 2) if irrigated > 0 else 0.0
            tw_pct = round((tw / irrigated * 100.0), 2) if irrigated > 0 else 0.0
            barani_pct = round((barani / total_cult * 100.0), 2) if total_cult > 0 else 0.0

            # Combined Surface vs Groundwater reliance across irrigated area
            gw_reliance = round(((tw + 0.5 * canal_tw) / irrigated * 100.0), 2) if irrigated > 0 else 0.0
            surface_reliance = round(((canal + 0.5 * canal_tw) / irrigated * 100.0), 2) if irrigated > 0 else 0.0

            # Determine dominant mode
            if barani_pct >= 50.0:
                primary_mode = "Rainfed (Barani)"
                classification = "Rainfed (Barani Dominant)"
            elif canal_tw >= canal and canal_tw >= tw:
                primary_mode = "Canal & Tubewell (Conjunctive)"
                classification = "Conjunctive Irrigation System"
            elif tw >= canal and tw >= canal_tw:
                primary_mode = "Tubewell (Groundwater)"
                classification = "Groundwater Dominant"
            elif canal >= tw and canal >= canal_tw:
                primary_mode = "Canal (Surface Water)"
                classification = "Surface Canal Dominant"
            else:
                primary_mode = "Mixed Sources"
                classification = "Mixed Irrigation System"

            rows.append({
                "district": dist,
                "total_cultivated_area_acres": total_cult,
                "irrigated_area_acres": irrigated,
                "unirrigated_area_acres": unirrigated,
                "irrigation_coverage_pct": cov_pct,
                "canal_only_acres": canal,
                "canal_only_pct": canal_pct,
                "canal_and_tubewell_acres": canal_tw,
                "canal_and_tubewell_pct": canal_tw_pct,
                "tubewell_only_acres": tw,
                "tubewell_only_pct": tw_pct,
                "barani_rainfed_acres": barani,
                "barani_share_pct": barani_pct,
                "sailaba_flood_acres": sailaba,
                "other_sources_acres": other,
                "groundwater_reliance_pct": gw_reliance,
                "canal_surface_reliance_pct": surface_reliance,
                "primary_irrigation_mode": primary_mode,
                "water_source_classification": classification,
                "provincial_annual_canal_withdrawals_maf": 53.5,
                "provincial_per_capita_water_m3_year": 860.0,
                "falkenmark_stress_category": "Water-Stressed (<1,000 m3/capita)",
                "data_source": "PBS 2024 Agricultural Census (Table 4.2) / Pakistan Economic Survey & IRSA",
                "source_year": 2024,
                "processed_at": now_iso,
            })

    rows.sort(key=lambda x: x["district"])

    temp_file = OUTPUT_CSV.with_suffix(".tmp")
    with open(temp_file, "w", encoding="utf-8", newline="") as fh:
        writer = csv.DictWriter(fh, fieldnames=FIELDNAMES)
        writer.writeheader()
        writer.writerows(rows)
    temp_file.replace(OUTPUT_CSV)
    logger.info(f"Generated {len(rows)} water availability records -> {OUTPUT_CSV}")
    return rows


if __name__ == "__main__":
    process_water_availability()
