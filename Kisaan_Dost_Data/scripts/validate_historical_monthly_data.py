#!/usr/bin/env python3
"""Validate the combined 2022-2026 historical clean dataset (stdlib only).

Checks processed/Punjab_Monthly_Clean_2022_2026.csv against the raw monthly
exports and reports structural and quality metrics.

Usage: python scripts/validate_historical_monthly_data.py
"""

from __future__ import annotations

import calendar
import csv
import sys
from pathlib import Path

DATA_DIR = Path(__file__).resolve().parent.parent
CLEAN_FILE = DATA_DIR / "processed" / "Punjab_Monthly_Clean_2022_2026.csv"

YEARS = (2022, 2023, 2024, 2025, 2026)
FULL_GRID = [(y, m) for y in YEARS for m in range(1, 13)]

PUNJAB_AREA_KM2 = 205_344.0
AREA_TOLERANCE = 0.02
MONSOON_MONTHS = {6, 7, 8, 9}

SEASONS = {
    "Winter": {12, 1, 2},
    "Spring": {3, 4, 5},
    "Summer": {6, 7, 8, 9},
    "Autumn": {10, 11},
}

SPECS = {
    "NDVI": ("NDVI_Punjab_{year}_Monthly.csv",
             ["NDVI_mean", "month", "year"]),
    "NDWI": ("NDWI_Punjab_{year}_Monthly.csv",
             ["NDWI_mean", "month", "year"]),
    "Rainfall": ("Rainfall_Punjab_{year}_Monthly.csv",
                 ["month", "rainfall_mean_mm_per_day", "rainfall_total_mm", "year"]),
    "Temperature": ("Temperature_Punjab_{year}_Monthly.csv",
                    ["month", "temp_max_c", "temp_mean_c", "temp_min_c", "year"]),
    "SoilMoisture": ("SoilMoisture_Punjab_{year}_Monthly.csv",
                     ["month", "soil_moisture_0_7cm", "soil_moisture_7_28cm", "year"]),
    "LandCover": ("LandCover_Punjab_{year}_Monthly.csv",
                  ["bare_km2", "built_km2", "crops_km2", "flooded_vegetation_km2",
                   "grass_km2", "month", "shrub_and_scrub_km2", "snow_and_ice_km2",
                   "trees_km2", "water_km2", "year"]),
}

LANDCOVER_COLS = ["bare_km2", "built_km2", "crops_km2", "flooded_vegetation_km2",
                  "grass_km2", "shrub_and_scrub_km2", "snow_and_ice_km2",
                  "trees_km2", "water_km2"]

CLEAN_HEADER = [
    "date", "year", "month", "season",
    "NDVI_mean", "NDWI_mean",
    "rainfall_mean_mm_per_day", "rainfall_total_mm",
    "temp_max_c", "temp_mean_c", "temp_min_c",
    "soil_moisture_0_7cm", "soil_moisture_7_28cm",
] + LANDCOVER_COLS + [
    "landcover_total_km2", "coverage_quality", "data_quality_flag", "year_to_date"
]

error_count = 0
warning_count = 0


def err(msg: str) -> None:
    global error_count
    error_count += 1
    print(f"  [ERROR] {msg}")


def warn(msg: str) -> None:
    global warning_count
    warning_count += 1
    print(f"  [WARN]  {msg}")


def ok(msg: str) -> None:
    print(f"  [OK]    {msg}")


def season_for(month: int) -> str:
    for name, months in SEASONS.items():
        if month in months:
            return name
    return ""


def read_csv(path: Path) -> tuple[list[str], list[dict[str, str]]]:
    with open(path, newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        return reader.fieldnames or [], list(reader)


def load_raw_map() -> dict[tuple[int, int], dict[str, str]]:
    raw: dict[tuple[int, int], dict[str, str]] = {}
    for pattern, keep in SPECS.values():
        for year in YEARS:
            path = DATA_DIR / pattern.format(year=year)
            if not path.exists():
                continue
            _, rows = read_csv(path)
            for rec in rows:
                key = (int(rec["year"]), int(rec["month"]))
                raw.setdefault(key, {}).update({col: rec[col] for col in keep if col not in ("year", "month")})
    return raw


def main() -> int:
    print("Kisaan Dost historical (2022-2026) monthly data validation")
    print(f"Data directory: {DATA_DIR}\n")

    if not CLEAN_FILE.exists():
        print(f"  [ERROR] {CLEAN_FILE.name} not found")
        return 1

    header, rows = read_csv(CLEAN_FILE)

    print("== Dataset structure ==")
    print(f"  file: {CLEAN_FILE}")
    print(f"  row count (excl. header): {len(rows)}")
    print(f"  column count: {len(header)}")
    print(f"  columns: {header}")

    if header != CLEAN_HEADER:
        err(f"header mismatch\n  expected: {CLEAN_HEADER}\n  found:    {header}")

    raw = load_raw_map()
    covered: set[tuple[int, int]] = set()
    prev_date = ""
    suspicious_rows: list[str] = []
    coverage_warnings: list[str] = []
    duplicates: set[tuple[int, int]] = set()

    for i, rec in enumerate(rows, start=2):
        where = f"{CLEAN_FILE.name} row {i}"
        date = rec.get("date", "")
        try:
            y, m = int(date[:4]), int(date[5:7])
        except (TypeError, ValueError):
            err(f"{where}: unparseable date {date!r}")
            continue

        key = (y, m)
        if key in covered:
            duplicates.add(key)
        covered.add(key)

        if date != f"{y}-{m:02d}-01":
            err(f"{where}: date {date!r} is not first-of-month ISO format")
        if prev_date and date < prev_date:
            err(f"{where}: rows not sorted chronologically")
        prev_date = date

        if int(rec.get("year", -1)) != y or int(rec.get("month", -1)) != m:
            err(f"{where}: year/month columns disagree with date")
        if rec.get("season") != season_for(m):
            err(f"{where}: season {rec.get('season')!r} != expected {season_for(m)!r}")

        # Validate values against raw
        for col in CLEAN_HEADER[4:-4]:
            v = rec.get(col)
            if v is None or str(v).strip() == "":
                err(f"{where}: empty value in {col!r}")
                continue
            raw_val = raw.get(key, {}).get(col)
            if raw_val is None:
                err(f"{where}: no raw counterpart for {col!r}")
            elif float(v) != float(raw_val):
                err(f"{where}: {col} {v} differs from raw {raw_val}")

        # Land cover total
        try:
            total = sum(float(rec[col]) for col in LANDCOVER_COLS)
        except (TypeError, ValueError):
            total = None
        if total is not None:
            expected_total = float(rec.get("landcover_total_km2", "nan"))
            if abs(total - expected_total) > 0.001:
                err(f"{where}: landcover_total_km2 {expected_total} != sum {total}")
            lower = PUNJAB_AREA_KM2 * (1 - AREA_TOLERANCE)
            upper = PUNJAB_AREA_KM2 * (1 + AREA_TOLERANCE)
            if total < lower:
                coverage_warnings.append(f"{y}-{m:02d}: {total:,.0f} km2 ({(PUNJAB_AREA_KM2 - total) / PUNJAB_AREA_KM2 * 100:.1f}% short)")
            elif total > upper:
                coverage_warnings.append(f"{y}-{m:02d}: {total:,.0f} km2 (above +2%)")

        # Quality flags
        quality = rec.get("coverage_quality", "")
        if key in ((2022, 7), (2022, 8), (2023, 7)):
            if quality != "poor":
                err(f"{where}: expected coverage_quality='poor' for {y}-{m:02d}, got {quality!r}")
        if key == (2026, 8):
            if rec.get("data_quality_flag") != "suspicious_rainfall":
                err(f"{where}: expected data_quality_flag='suspicious_rainfall' for 2026-08")
            suspicious_rows.append("2026-08: suspicious_rainfall")
        if y == 2026 and rec.get("year_to_date") != "True":
            err(f"{where}: expected year_to_date=True for 2026")
        if y != 2026 and rec.get("year_to_date") != "False":
            err(f"{where}: expected year_to_date=False for {y}")

    print("\n== Date coverage ==")
    if covered:
        first = min(covered)
        last = max(covered)
        print(f"  range: {first[0]}-{first[1]:02d} to {last[0]}-{last[1]:02d}")
    missing = sorted(set(FULL_GRID) - covered)
    print(f"  months present: {len(covered)}")
    print(f"  months missing: {len(missing)}")
    if missing:
        print(f"  missing list: {', '.join(f'{y}-{m:02d}' for y, m in missing)}")

    print("\n== Duplicates ==")
    if duplicates:
        for key in sorted(duplicates):
            err(f"duplicate month: {key[0]}-{key[1]:02d}")
    else:
        ok("no duplicate months")

    print("\n== Coverage warnings ==")
    if coverage_warnings:
        for item in coverage_warnings:
            warn(item)
    else:
        ok("no coverage warnings")

    print("\n== Suspicious rows ==")
    if suspicious_rows:
        for item in suspicious_rows:
            warn(item)
    else:
        ok("no suspicious rows flagged")

    print("\n== First five rows ==")
    for rec in rows[:5]:
        print(f"  {rec}")

    print("\n== Summary ==")
    print(f"  errors:   {error_count}")
    print(f"  warnings: {warning_count}")
    if error_count:
        print("  RESULT: FAILED")
        return 1
    print("  RESULT: PASSED" + (" (with warnings)" if warning_count else ""))
    return 0


if __name__ == "__main__":
    sys.exit(main())
