#!/usr/bin/env python3
"""Create processed/district_master_clean.csv from district-level remote-sensing exports.

Reads the monthly CSV files in D:\\Kisaan_Dost_Data\\District data, standardizes
schema across 2022-2024 (detailed) and 2025-2026 (simplified) exports, and merges
all variables horizontally by (year, month, district) into a single long-format
analytical table. Province-level image/PDF context assets are documented in the
accompanying reports, not merged here.

Raw files are opened read-only and never modified.
"""

from __future__ import annotations

import csv
import sys
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
DISTRICT_DIR = BASE_DIR / "District data"
PROCESSED_DIR = BASE_DIR / "processed"
OUT_FILE = PROCESSED_DIR / "district_master_clean.csv"
DICT_FILE = PROCESSED_DIR / "district_master_data_dictionary.csv"

DROP_COLS = {"system:index", ".geo"}

OUTPUT_HEADER = [
    "date", "year", "month", "district",
    "NDVI_mean", "NDWI_mean",
    "rainfall_total_mm", "rainfall_mean_mm_per_day",
    "temp_max_c", "temp_mean_c", "temp_min_c",
    "soil_moisture_0_7cm", "soil_moisture_7_28cm",
    "landcover_crops_km2", "landcover_cropland_fraction",
    "data_source_schema", "data_quality_flag", "missing_columns_note"
]

SCHEMA_LEGACY = "legacy_detailed"
SCHEMA_MODERN = "modern_simplified"

MONSOON_MONTHS = {6, 7, 8, 9}

# Map (variable, source_column) -> output column for the legacy schema
LEGACY_COLUMN_MAP = {
    ("NDVI", "NDVI_mean"): "NDVI_mean",
    ("NDWI", "NDWI_mean"): "NDWI_mean",
    ("Rainfall", "rainfall_total_mm"): "rainfall_total_mm",
    ("Rainfall", "rainfall_mean_mm_per_day"): "rainfall_mean_mm_per_day",
    ("Temperature", "temp_max_c"): "temp_max_c",
    ("Temperature", "temp_mean_c"): "temp_mean_c",
    ("Temperature", "temp_min_c"): "temp_min_c",
    ("SoilMoisture", "soil_moisture_0_7cm"): "soil_moisture_0_7cm",
    ("SoilMoisture", "soil_moisture_7_28cm"): "soil_moisture_7_28cm",
    ("LandCover", "crops_km2"): "landcover_crops_km2",
}

# Map (variable, source_column) -> output column for the modern schema
MODERN_COLUMN_MAP = {
    ("NDVI", "NDVI_mean"): "NDVI_mean",
    ("NDWI", "NDWI_mean"): "NDWI_mean",
    ("Rainfall", "Rainfall_mm"): "rainfall_total_mm",
    ("Temperature", "Temperature_C"): "temp_mean_c",
    ("SoilMoisture", "SoilMoisture"): "soil_moisture_0_7cm",
}


def read_csv(path: Path) -> tuple[list[str], list[dict[str, str]]]:
    with open(path, newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        return reader.fieldnames or [], list(reader)


def standardize_district(name: str) -> str:
    return " ".join(name.strip().title().split())


def variable_from_filename(path: Path) -> str:
    return path.name.split("_")[0]


def process_monthly_files() -> tuple[list[dict[str, str]], dict]:
    """Read all monthly CSVs, merge by (year, month, district), return rows + stats."""
    monthly_files = sorted(DISTRICT_DIR.glob("*_Districts_Punjab_*_Monthly.csv"))

    # First pass: aggregate all values by (year, month, district)
    merged: dict[tuple[int, int, str], dict[str, str]] = {}
    stats = {
        "files_read": 0,
        "raw_rows": 0,
        "output_rows": 0,
        "missing_values": 0,
        "suspicious_zero_rainfall": 0,
        "schema_legacy_rows": 0,
        "schema_modern_rows": 0,
    }

    for path in monthly_files:
        variable = variable_from_filename(path)
        year = int(path.name.split("_")[3])
        header, file_rows = read_csv(path)
        stats["files_read"] += 1
        stats["raw_rows"] += len(file_rows)

        # Detect schema by checking header contents
        is_modern = any(h in header for h in ["Rainfall_mm", "Temperature_C", "SoilMoisture"])
        active_map = MODERN_COLUMN_MAP if is_modern else LEGACY_COLUMN_MAP

        for r in file_rows:
            district = standardize_district(r["district"])
            month = int(r["month"])
            key = (year, month, district)
            if key not in merged:
                merged[key] = {
                    "date": f"{year}-{month:02d}-01",
                    "year": str(year),
                    "month": str(month),
                    "district": district,
                }
            for src_col in header:
                if src_col in DROP_COLS or src_col in ("district", "month", "year"):
                    continue
                out_col = active_map.get((variable, src_col))
                if out_col:
                    merged[key][out_col] = r[src_col]

    # Second pass: attach annual cropland fraction where available
    annual_lc = {}
    for path in sorted(DISTRICT_DIR.glob("LandCover_Districts_Punjab_*.csv")):
        if "Monthly" in path.name:
            continue
        year = int(path.name.split("_")[3].split(".")[0])
        _, file_rows = read_csv(path)
        for r in file_rows:
            district = standardize_district(r["district"])
            annual_lc[(year, district)] = r["Cropland_Fraction"]

    rows: list[dict[str, str]] = []
    for key in sorted(merged.keys()):
        data = merged[key]
        year, month, district = key

        # Attach annual cropland fraction if available for this year/district
        cf_key = (year, district)
        if cf_key in annual_lc:
            data["landcover_cropland_fraction"] = annual_lc[cf_key]

        # Determine schema based on which rainfall column source was used
        has_legacy = "rainfall_mean_mm_per_day" in data

        out: dict[str, str] = {col: data.get(col, "") for col in OUTPUT_HEADER}
        out["date"] = data["date"]
        out["year"] = data["year"]
        out["month"] = data["month"]
        out["district"] = data["district"]

        if has_legacy:
            out["data_source_schema"] = SCHEMA_LEGACY
            out["missing_columns_note"] = ""
            stats["schema_legacy_rows"] += 1
        else:
            out["data_source_schema"] = SCHEMA_MODERN
            note = "simplified_2025_2026_schema: no mean/min/max/total breakdowns"
            if cf_key in annual_lc:
                note += "; annual_cropland_fraction_applied_to_all_months"
            out["missing_columns_note"] = note
            stats["schema_modern_rows"] += 1

        # Flag suspicious zero rainfall in monsoon months
        rain_val = out.get("rainfall_total_mm", "")
        if rain_val in ("0", "0.0") and month in MONSOON_MONTHS:
            out["data_quality_flag"] = "suspicious_zero_monsoon_rainfall"
            stats["suspicious_zero_rainfall"] += 1
        else:
            out["data_quality_flag"] = ""

        for col in OUTPUT_HEADER[4:-3]:
            if out.get(col, "") == "":
                stats["missing_values"] += 1

        rows.append(out)
        stats["output_rows"] += 1

    return rows, stats


def write_data_dictionary() -> None:
    definitions = [
        ("date", "YYYY-MM-01 first-of-month ISO date derived from year and month", "date"),
        ("year", "Calendar year of observation", "integer"),
        ("month", "Month of year (1-12)", "integer"),
        ("district", "Standardized Punjab district name", "text"),
        ("NDVI_mean", "Mean Normalized Difference Vegetation Index for the district-month", "unitless (-1 to 1)"),
        ("NDWI_mean", "Mean Normalized Difference Water Index for the district-month", "unitless (-1 to 1)"),
        ("rainfall_total_mm", "Monthly total rainfall; 2025-2026 maps from single Rainfall_mm column", "mm"),
        ("rainfall_mean_mm_per_day", "Daily mean rainfall (only available for 2022-2024)", "mm/day"),
        ("temp_max_c", "Monthly maximum temperature (only available for 2022-2024)", "degrees Celsius"),
        ("temp_mean_c", "Monthly mean temperature; 2025-2026 maps from single Temperature_C column", "degrees Celsius"),
        ("temp_min_c", "Monthly minimum temperature (only available for 2022-2024)", "degrees Celsius"),
        ("soil_moisture_0_7cm", "Volumetric soil moisture 0-7 cm layer; 2025-2026 maps from single SoilMoisture column", "m3/m3"),
        ("soil_moisture_7_28cm", "Volumetric soil moisture 7-28 cm layer (only available for 2022-2024)", "m3/m3"),
        ("landcover_crops_km2", "Area classified as crops from monthly land-cover data (2022-2024 only)", "km2"),
        ("landcover_cropland_fraction", "Annual cropland fraction from 2025-2026 simplified land-cover exports", "fraction"),
        ("data_source_schema", "Either legacy_detailed (2022-2024) or modern_simplified (2025-2026)", "text"),
        ("data_quality_flag", "Quality flag e.g. suspicious_zero_monsoon_rainfall", "text"),
        ("missing_columns_note", "Explanation when 2025-2026 simplified schema cannot provide legacy columns", "text"),
    ]
    with open(DICT_FILE, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=["column", "description", "unit"])
        writer.writeheader()
        for col, desc, unit in definitions:
            writer.writerow({"column": col, "description": desc, "unit": unit})


def main() -> int:
    PROCESSED_DIR.mkdir(parents=True, exist_ok=True)

    rows, stats = process_monthly_files()

    with open(OUT_FILE, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=OUTPUT_HEADER)
        writer.writeheader()
        writer.writerows(rows)

    write_data_dictionary()

    print("=== district_master_clean.csv created ===")
    print(f"Output rows: {stats['output_rows']}")
    print(f"Raw files read: {stats['files_read']}")
    print(f"Raw rows ingested: {stats['raw_rows']}")
    print(f"Legacy detailed rows: {stats['schema_legacy_rows']}")
    print(f"Modern simplified rows: {stats['schema_modern_rows']}")
    print(f"Missing analytical values: {stats['missing_values']}")
    print(f"Suspicious zero monsoon rainfall flags: {stats['suspicious_zero_rainfall']}")
    print(f"Districts: {len(set(r['district'] for r in rows))}")
    print(f"Date range: {min(r['date'] for r in rows)} to {max(r['date'] for r in rows)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
