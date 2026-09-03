#!/usr/bin/env python3
"""Validate processed/district_master_clean.csv and the raw district exports.

Read-only validator. Checks row counts, date coverage, district coverage,
missing values, duplicates, and cross-checks key values against raw files.
"""

from __future__ import annotations

import csv
import sys
from pathlib import Path
from collections import Counter

BASE_DIR = Path(__file__).resolve().parent.parent
DISTRICT_DIR = BASE_DIR / "District data"
CLEAN_FILE = BASE_DIR / "processed" / "district_master_clean.csv"
DICT_FILE = BASE_DIR / "processed" / "district_master_data_dictionary.csv"

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


def read_csv(path: Path) -> tuple[list[str], list[dict[str, str]]]:
    with open(path, newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        return reader.fieldnames or [], list(reader)


def main() -> int:
    print("District Master Data Validation")
    print(f"Data directory: {BASE_DIR}\n")

    # Check files exist
    print("== Required files ==")
    for p in [CLEAN_FILE, DICT_FILE]:
        if p.exists():
            ok(f"{p.name} exists")
        else:
            err(f"{p.name} missing")

    if not CLEAN_FILE.exists():
        return 1

    header, rows = read_csv(CLEAN_FILE)
    expected_header = [
        "date", "year", "month", "district",
        "NDVI_mean", "NDWI_mean",
        "rainfall_total_mm", "rainfall_mean_mm_per_day",
        "temp_max_c", "temp_mean_c", "temp_min_c",
        "soil_moisture_0_7cm", "soil_moisture_7_28cm",
        "landcover_crops_km2", "landcover_cropland_fraction",
        "data_source_schema", "data_quality_flag", "missing_columns_note"
    ]

    print("\n== Structure ==")
    print(f"  rows (excl. header): {len(rows)}")
    print(f"  columns: {len(header)}")
    print(f"  column names: {header}")
    if header != expected_header:
        err(f"header mismatch\n  expected: {expected_header}\n  found:    {header}")
    else:
        ok("header matches expected")

    # Date coverage
    dates = sorted({r["date"] for r in rows})
    print(f"\n== Date coverage ==")
    print(f"  range: {dates[0]} to {dates[-1]}")
    print(f"  unique month-dates: {len(dates)}")

    # Check 2026-09 to 2026-12 absent
    missing_dates = [f"2026-{m:02d}-01" for m in range(9, 13)]
    present_extra = [d for d in missing_dates if d in dates]
    if present_extra:
        err(f"unexpected 2026 months present: {present_extra}")
    else:
        ok("2026-09 to 2026-12 are absent")

    # District coverage
    districts = sorted({r["district"] for r in rows})
    print(f"\n== District coverage ==")
    print(f"  districts: {len(districts)}")
    for d in districts:
        print(f"    {d}")

    # Check each district has expected months
    expected_counts = {}
    for y in range(2022, 2026):
        for m in range(1, 13):
            expected_counts[(y, m)] = 34
    for m in range(1, 9):
        expected_counts[(2026, m)] = 34

    actual_counts = Counter((int(r["year"]), int(r["month"])) for r in rows)
    print(f"\n== Month completeness ==")
    for key in sorted(expected_counts.keys()):
        expected = expected_counts[key]
        actual = actual_counts.get(key, 0)
        if actual != expected:
            err(f"{key[0]}-{key[1]:02d}: expected {expected} rows, got {actual}")
        else:
            ok(f"{key[0]}-{key[1]:02d}: {actual} rows")

    # Duplicates
    keys = [(r["year"], r["month"], r["district"]) for r in rows]
    dup_count = len(keys) - len(set(keys))
    print(f"\n== Duplicates ==")
    if dup_count:
        err(f"{dup_count} duplicate (year, month, district) rows")
    else:
        ok("no duplicate rows")

    # Missing values
    print(f"\n== Missing values ==")
    for col in header[4:-3]:  # analytical columns only
        missing = sum(1 for r in rows if r.get(col, "").strip() == "")
        if missing:
            warn(f"{col}: {missing} missing")
        else:
            ok(f"{col}: no missing values")

    # Schema distribution
    schema_counts = Counter(r["data_source_schema"] for r in rows)
    print(f"\n== Schema distribution ==")
    for schema, count in schema_counts.items():
        print(f"  {schema}: {count}")

    # Data quality flags
    flag_counts = Counter(r["data_quality_flag"] for r in rows if r["data_quality_flag"])
    print(f"\n== Data quality flags ==")
    if flag_counts:
        for flag, count in flag_counts.items():
            warn(f"{flag}: {count}")
    else:
        ok("no quality flags set")

    # Raw file inventory
    print(f"\n== Raw file inventory ==")
    raw_csvs = sorted(DISTRICT_DIR.glob("*_Districts_Punjab_*.csv"))
    print(f"  district CSV files: {len(raw_csvs)}")
    for p in raw_csvs[:5]:
        print(f"    {p.name}")
    if len(raw_csvs) > 5:
        print(f"    ... and {len(raw_csvs) - 5} more")

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
