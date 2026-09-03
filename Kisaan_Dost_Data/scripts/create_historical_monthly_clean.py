#!/usr/bin/env python3
"""Create the combined 2022-2026 historical clean dataset.

Reads the 30 raw monthly CSV exports in the parent directory, merges them
horizontally on (year, month), adds quality flags, and writes:
    processed/Punjab_Monthly_Clean_2022_2026.csv

No raw files are modified.
"""

from __future__ import annotations

import csv
import sys
from pathlib import Path

DATA_DIR = Path(__file__).resolve().parent.parent
PROCESSED_DIR = DATA_DIR / "processed"
OUTPUT_FILE = PROCESSED_DIR / "Punjab_Monthly_Clean_2022_2026.csv"

YEARS = (2022, 2023, 2024, 2025, 2026)

PUNJAB_AREA_KM2 = 205_344.0

SEASONS = {
    "Winter": {12, 1, 2},
    "Spring": {3, 4, 5},
    "Summer": {6, 7, 8, 9},
    "Autumn": {10, 11},
}

# Variable name -> filename pattern -> list of columns to retain (year/month handled separately)
SPECS = {
    "NDVI": ("NDVI_Punjab_{year}_Monthly.csv", ["NDVI_mean"]),
    "NDWI": ("NDWI_Punjab_{year}_Monthly.csv", ["NDWI_mean"]),
    "Rainfall": ("Rainfall_Punjab_{year}_Monthly.csv", ["rainfall_mean_mm_per_day", "rainfall_total_mm"]),
    "Temperature": ("Temperature_Punjab_{year}_Monthly.csv", ["temp_max_c", "temp_mean_c", "temp_min_c"]),
    "SoilMoisture": ("SoilMoisture_Punjab_{year}_Monthly.csv", ["soil_moisture_0_7cm", "soil_moisture_7_28cm"]),
    "LandCover": ("LandCover_Punjab_{year}_Monthly.csv", [
        "bare_km2", "built_km2", "crops_km2", "flooded_vegetation_km2",
        "grass_km2", "shrub_and_scrub_km2", "snow_and_ice_km2",
        "trees_km2", "water_km2"
    ]),
}

LANDCOVER_COLS = SPECS["LandCover"][1]

OUTPUT_HEADER = [
    "date", "year", "month", "season",
    "NDVI_mean", "NDWI_mean",
    "rainfall_mean_mm_per_day", "rainfall_total_mm",
    "temp_max_c", "temp_mean_c", "temp_min_c",
    "soil_moisture_0_7cm", "soil_moisture_7_28cm",
] + LANDCOVER_COLS + [
    "landcover_total_km2", "coverage_quality", "data_quality_flag", "year_to_date"
]

COVERAGE_WARNINGS = {
    (2022, 7): "poor",
    (2022, 8): "poor",
    (2023, 7): "poor",
}

SUSPICIOUS_RAINFALL = {(2026, 8)}


def season_for(month: int) -> str:
    for name, months in SEASONS.items():
        if month in months:
            return name
    raise ValueError(f"month {month} out of range")


def read_csv(path: Path) -> tuple[list[str], list[dict[str, str]]]:
    with open(path, newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        return reader.fieldnames or [], list(reader)


def load_variable(pattern: str, keep_cols: list[str]) -> dict[tuple[int, int], dict[str, str]]:
    result: dict[tuple[int, int], dict[str, str]] = {}
    for year in YEARS:
        path = DATA_DIR / pattern.format(year=year)
        if not path.exists():
            raise FileNotFoundError(path)
        header, rows = read_csv(path)
        for col in keep_cols:
            if col not in header:
                raise ValueError(f"{path.name}: missing expected column {col!r}")
        for rec in rows:
            key = (int(rec["year"]), int(rec["month"]))
            if key in result:
                raise ValueError(f"{path.name}: duplicate month {key}")
            result[key] = {col: rec[col] for col in keep_cols}
    return result


def coverage_quality(total: float, key: tuple[int, int]) -> str:
    if key in COVERAGE_WARNINGS:
        return COVERAGE_WARNINGS[key]
    ratio = total / PUNJAB_AREA_KM2
    if ratio >= 0.98:
        return "good"
    if ratio >= 0.90:
        return "moderate"
    return "poor"


def main() -> int:
    PROCESSED_DIR.mkdir(exist_ok=True)

    merged: dict[tuple[int, int], dict[str, str]] = {}
    for variable, (pattern, keep_cols) in SPECS.items():
        data = load_variable(pattern, keep_cols)
        for key, vals in data.items():
            merged.setdefault(key, {}).update(vals)

    # Build rows in chronological order
    rows: list[dict[str, str]] = []
    for year in YEARS:
        for month in range(1, 13):
            key = (year, month)
            if key not in merged:
                continue
            rec = merged[key]
            landcover_total = sum(float(rec[col]) for col in LANDCOVER_COLS)
            quality = coverage_quality(landcover_total, key)
            flag = "suspicious_rainfall" if key in SUSPICIOUS_RAINFALL else ""
            ytd = "True" if year == 2026 else "False"
            row = {
                "date": f"{year}-{month:02d}-01",
                "year": str(year),
                "month": str(month),
                "season": season_for(month),
                "landcover_total_km2": f"{landcover_total:.6f}",
                "coverage_quality": quality,
                "data_quality_flag": flag,
                "year_to_date": ytd,
            }
            row.update({col: rec[col] for col in OUTPUT_HEADER[4:-4]})
            rows.append(row)

    with open(OUTPUT_FILE, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=OUTPUT_HEADER)
        writer.writeheader()
        writer.writerows(rows)

    print(f"Wrote {len(rows)} rows to {OUTPUT_FILE}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
