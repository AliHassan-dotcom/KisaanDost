"""Process district land utilization and crop acreage metrics from PBS 2024 Agricultural Census.

Input:
- Kisaan_Dost_Data/processed/pbs_farm_structure.csv
- Kisaan_Dost_Data/processed/pbs_crops.csv

Output:
- Kisaan_Dost_Data/processed/district_land_utilization_v1.csv
"""

from __future__ import annotations

import csv
from datetime import datetime, timezone
import logging
from pathlib import Path
from typing import Any, Dict, List, Optional

ROOT = Path(__file__).resolve().parent.parent
PROCESSED_DIR = ROOT / "processed"
FARM_STRUCTURE_CSV = PROCESSED_DIR / "pbs_farm_structure.csv"
CROPS_CSV = PROCESSED_DIR / "pbs_crops.csv"
OUTPUT_CSV = PROCESSED_DIR / "district_land_utilization_v1.csv"

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger(__name__)

FIELDNAMES = [
    "district",
    "total_farm_area_acres",
    "cultivated_area_acres",
    "uncultivated_area_acres",
    "total_cropped_area_acres",
    "cultivated_share_pct",
    "cropping_intensity_pct",
    "wheat_area_acres",
    "wheat_share_pct",
    "rice_area_acres",
    "rice_share_pct",
    "cotton_area_acres",
    "cotton_share_pct",
    "sugarcane_area_acres",
    "sugarcane_share_pct",
    "maize_area_acres",
    "maize_share_pct",
    "fodder_area_acres",
    "fodder_share_pct",
    "orchard_area_acres",
    "orchard_share_pct",
    "kharif_total_acres",
    "rabi_total_acres",
    "data_source",
    "source_year",
    "processed_at",
]


def _safe_float(val: Any) -> Optional[float]:
    if val is None:
        return None
    s = str(val).strip().replace(",", "")
    if not s or s in {"-", "N/A", "NA", "--"}:
        return None
    try:
        return float(s)
    except ValueError:
        return None


def process_land_utilization() -> List[Dict[str, Any]]:
    if not FARM_STRUCTURE_CSV.exists() or not CROPS_CSV.exists():
        raise FileNotFoundError("Required PBS input CSV files not found.")

    # 1. Load Farm Structure
    farm_data: Dict[str, Dict[str, float]] = {}
    with open(FARM_STRUCTURE_CSV, "r", encoding="utf-8", newline="") as fh:
        reader = csv.DictReader(fh)
        for r in reader:
            dist = r["district"].strip()
            total_farm = _safe_float(r.get("total_farm_area")) or 0.0
            cultivated = _safe_float(r.get("cultivated_area")) or 0.0
            uncultivated = _safe_float(r.get("uncultivated_area")) or 0.0
            farm_data[dist] = {
                "total_farm_area": total_farm,
                "cultivated_area": cultivated,
                "uncultivated_area": uncultivated,
            }

    # 2. Load Crops Acreage
    crop_data: Dict[str, Dict[str, Any]] = {}
    with open(CROPS_CSV, "r", encoding="utf-8", newline="") as fh:
        reader = csv.DictReader(fh)
        for r in reader:
            dist = r["district"].strip()
            crop_name = r.get("crop_name", "").strip()
            c_area = _safe_float(r.get("crop_area"))
            c_share = _safe_float(r.get("crop_share"))
            tot_crop = _safe_float(r.get("total_cropped_area")) or 0.0

            if dist not in crop_data:
                crop_data[dist] = {
                    "total_cropped_area": tot_crop,
                    "wheat_area": 0.0,
                    "wheat_share": 0.0,
                    "rice_area": 0.0,
                    "rice_share": 0.0,
                    "cotton_area": 0.0,
                    "cotton_share": 0.0,
                    "sugarcane_area": 0.0,
                    "sugarcane_share": 0.0,
                    "maize_area": 0.0,
                    "maize_share": 0.0,
                    "fodder_area": 0.0,
                    "fodder_share": 0.0,
                    "orchard_area": 0.0,
                    "orchard_share": 0.0,
                    "kharif_total": 0.0,
                    "rabi_total": 0.0,
                }

            if tot_crop > crop_data[dist]["total_cropped_area"]:
                crop_data[dist]["total_cropped_area"] = tot_crop

            c_lower = crop_name.lower()
            if "wheat" in c_lower and "straw" not in c_lower:
                if c_area is not None:
                    crop_data[dist]["wheat_area"] = c_area
                if c_share is not None:
                    crop_data[dist]["wheat_share"] = c_share
            elif "rice" in c_lower or "paddy" in c_lower:
                if c_area is not None:
                    crop_data[dist]["rice_area"] = c_area
                if c_share is not None:
                    crop_data[dist]["rice_share"] = c_share
            elif "cotton" in c_lower:
                if c_area is not None:
                    crop_data[dist]["cotton_area"] = c_area
                if c_share is not None:
                    crop_data[dist]["cotton_share"] = c_share
            elif "sugarcane" in c_lower:
                if c_area is not None:
                    crop_data[dist]["sugarcane_area"] = c_area
                if c_share is not None:
                    crop_data[dist]["sugarcane_share"] = c_share
            elif "maize (total)" in c_lower or c_lower == "maize":
                if c_area is not None:
                    crop_data[dist]["maize_area"] = c_area
                if c_share is not None:
                    crop_data[dist]["maize_share"] = c_share
            elif "fodders" in c_lower or "fodder" in c_lower:
                if c_area is not None:
                    crop_data[dist]["fodder_area"] = c_area
                if c_share is not None:
                    crop_data[dist]["fodder_share"] = c_share
            elif "orchards" in c_lower:
                if c_area is not None:
                    crop_data[dist]["orchard_area"] = c_area
                if c_share is not None:
                    crop_data[dist]["orchard_share"] = c_share
            elif "kharif crops (total)" in c_lower:
                if c_area is not None:
                    crop_data[dist]["kharif_total"] = c_area
            elif "rabi crops (total)" in c_lower:
                if c_area is not None:
                    crop_data[dist]["rabi_total"] = c_area

    # 3. Combine & Compute Ratios
    now_iso = datetime.now(timezone.utc).isoformat()
    rows: List[Dict[str, Any]] = []

    for dist, f_info in farm_data.items():
        c_info = crop_data.get(dist, {})
        tot_farm = f_info["total_farm_area"]
        cult = f_info["cultivated_area"]
        uncult = f_info["uncultivated_area"]
        cropped = c_info.get("total_cropped_area", 0.0)

        cult_share_pct = round((cult / tot_farm * 100.0), 2) if tot_farm > 0 else 0.0
        crop_intensity_pct = round((cropped / cult * 100.0), 2) if cult > 0 else 0.0

        w_area = c_info.get("wheat_area", 0.0)
        w_share = c_info.get("wheat_share", 0.0)
        r_area = c_info.get("rice_area", 0.0)
        r_share = c_info.get("rice_share", 0.0)
        c_area = c_info.get("cotton_area", 0.0)
        c_share = c_info.get("cotton_share", 0.0)
        s_area = c_info.get("sugarcane_area", 0.0)
        s_share = c_info.get("sugarcane_share", 0.0)
        m_area = c_info.get("maize_area", 0.0)
        m_share = c_info.get("maize_share", 0.0)
        fod_area = c_info.get("fodder_area", 0.0)
        fod_share = c_info.get("fodder_share", 0.0)
        orch_area = c_info.get("orchard_area", 0.0)
        orch_share = c_info.get("orchard_share", 0.0)

        rows.append({
            "district": dist,
            "total_farm_area_acres": tot_farm,
            "cultivated_area_acres": cult,
            "uncultivated_area_acres": uncult,
            "total_cropped_area_acres": cropped,
            "cultivated_share_pct": cult_share_pct,
            "cropping_intensity_pct": crop_intensity_pct,
            "wheat_area_acres": w_area,
            "wheat_share_pct": w_share,
            "rice_area_acres": r_area,
            "rice_share_pct": r_share,
            "cotton_area_acres": c_area,
            "cotton_share_pct": c_share,
            "sugarcane_area_acres": s_area,
            "sugarcane_share_pct": s_share,
            "maize_area_acres": m_area,
            "maize_share_pct": m_share,
            "fodder_area_acres": fod_area,
            "fodder_share_pct": fod_share,
            "orchard_area_acres": orch_area,
            "orchard_share_pct": orch_share,
            "kharif_total_acres": c_info.get("kharif_total", 0.0),
            "rabi_total_acres": c_info.get("rabi_total", 0.0),
            "data_source": "PBS 2024 Agricultural Census (Tables 1.0, 1.1, 6.5)",
            "source_year": 2024,
            "processed_at": now_iso,
        })

    # Sort by district name
    rows.sort(key=lambda x: x["district"])

    # Atomic write to CSV
    temp_file = OUTPUT_CSV.with_suffix(".tmp")
    with open(temp_file, "w", encoding="utf-8", newline="") as fh:
        writer = csv.DictWriter(fh, fieldnames=FIELDNAMES)
        writer.writeheader()
        writer.writerows(rows)
    temp_file.replace(OUTPUT_CSV)
    logger.info(f"Generated {len(rows)} land utilization records -> {OUTPUT_CSV}")
    return rows


if __name__ == "__main__":
    process_land_utilization()
