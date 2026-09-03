#!/usr/bin/env python3
"""Validate the Kisaan Dost monthly Punjab CSV exports (read-only).

Checks the raw monthly files in the parent directory and, when present,
cross-checks processed/Punjab_Monthly_Clean.csv against them.

Usage: python scripts/validate_monthly_data.py
Exit code 0 = no errors (warnings allowed); 1 = at least one error.
"""

from __future__ import annotations

import calendar
import csv
import sys
from pathlib import Path

DATA_DIR = Path(__file__).resolve().parent.parent
PROCESSED_FILE = DATA_DIR / "processed" / "Punjab_Monthly_Clean.csv"

YEARS = (2024, 2025, 2026)
FULL_GRID = [(y, m) for y in YEARS for m in range(1, 13)]

PUNJAB_AREA_KM2 = 205_344.0  # administrative area of Punjab, Pakistan
AREA_TOLERANCE = 0.02        # +/- 2% band for land-cover class totals
MONSOON_MONTHS = {6, 7, 8, 9}

SEASONS = {
    "Winter": {12, 1, 2},
    "Spring": {3, 4, 5},
    "Summer": {6, 7, 8, 9},   # monsoon
    "Autumn": {10, 11},
}

SPECS = {
    "NDVI": ("NDVI_Punjab_{year}_Monthly.csv",
             ["system:index", "NDVI_mean", "month", "year", ".geo"]),
    "NDWI": ("NDWI_Punjab_{year}_Monthly.csv",
             ["system:index", "NDWI_mean", "month", "year", ".geo"]),
    "Rainfall": ("Rainfall_Punjab_{year}_Monthly.csv",
                 ["system:index", "month", "rainfall_mean_mm_per_day",
                  "rainfall_total_mm", "year", ".geo"]),
    "Temperature": ("Temperature_Punjab_{year}_Monthly.csv",
                    ["system:index", "month", "temp_max_c", "temp_mean_c",
                     "temp_min_c", "year", ".geo"]),
    "SoilMoisture": ("SoilMoisture_Punjab_{year}_Monthly.csv",
                     ["system:index", "month", "soil_moisture_0_7cm",
                      "soil_moisture_7_28cm", "year", ".geo"]),
    "LandCover": ("LandCover_Punjab_{year}_Monthly.csv",
                  ["system:index", "bare_km2", "built_km2", "crops_km2",
                   "flooded_vegetation_km2", "grass_km2", "month",
                   "shrub_and_scrub_km2", "snow_and_ice_km2", "trees_km2",
                   "water_km2", "year", ".geo"]),
}

LANDCOVER_COLS = ["bare_km2", "built_km2", "crops_km2", "flooded_vegetation_km2",
                  "grass_km2", "shrub_and_scrub_km2", "snow_and_ice_km2",
                  "trees_km2", "water_km2"]

CLEAN_HEADER = ["date", "year", "month", "season", "NDVI_mean", "NDWI_mean",
                "rainfall_mean_mm_per_day", "rainfall_total_mm", "temp_max_c",
                "temp_mean_c", "temp_min_c", "soil_moisture_0_7cm",
                "soil_moisture_7_28cm"] + LANDCOVER_COLS

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


def read_csv(path: Path):
    with open(path, newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        return reader.fieldnames or [], list(reader)


def num(rec: dict, col: str, where: str):
    val = rec.get(col)
    if val is None or str(val).strip() == "":
        err(f"{where}: empty value in column {col!r}")
        return None
    try:
        return float(val)
    except ValueError:
        err(f"{where}: non-numeric value {val!r} in column {col!r}")
        return None


def check_ranges(variable: str, rec: dict, year: int, month: int, where: str) -> None:
    if variable in ("NDVI", "NDWI"):
        v = num(rec, f"{variable}_mean", where)
        if v is not None and not -1.0 <= v <= 1.0:
            err(f"{where}: {variable}_mean {v} outside [-1, 1]")

    elif variable == "Rainfall":
        mean = num(rec, "rainfall_mean_mm_per_day", where)
        total = num(rec, "rainfall_total_mm", where)
        if mean is not None and mean < 0:
            err(f"{where}: negative rainfall_mean_mm_per_day {mean}")
        if total is not None and total < 0:
            err(f"{where}: negative rainfall_total_mm {total}")
        if mean is not None and total is not None:
            days = calendar.monthrange(year, month)[1]
            expected = mean * days
            if abs(expected - total) > max(0.05 * total, 0.01):
                err(f"{where}: rainfall_total_mm {total} inconsistent with "
                    f"mean {mean} x {days} days = {expected:.2f}")
        if total == 0.0 and month in MONSOON_MONTHS:
            warn(f"{where}: suspicious zero rainfall_total_mm in monsoon "
                 f"month {year}-{month:02d}")

    elif variable == "Temperature":
        vals = {c: num(rec, c, where) for c in ("temp_max_c", "temp_mean_c", "temp_min_c")}
        for c, v in vals.items():
            if v is not None and not -60.0 <= v <= 60.0:
                err(f"{where}: {c} {v} outside plausible Celsius range (-60, 60)")
                if v > 100.0:
                    err(f"{where}: {c} {v} looks Kelvin-scaled despite _c suffix")
        if all(v is not None for v in vals.values()):
            if not vals["temp_min_c"] <= vals["temp_mean_c"] <= vals["temp_max_c"]:
                err(f"{where}: temperature min/mean/max not ordered")

    elif variable == "SoilMoisture":
        for c in ("soil_moisture_0_7cm", "soil_moisture_7_28cm"):
            v = num(rec, c, where)
            if v is not None and not 0.0 <= v <= 1.0:
                err(f"{where}: {c} {v} outside [0, 1] m3/m3")

    elif variable == "LandCover":
        total = 0.0
        for c in LANDCOVER_COLS:
            v = num(rec, c, where)
            if v is None:
                continue
            if v < 0:
                err(f"{where}: negative {c} {v}")
            total += v
        lower = PUNJAB_AREA_KM2 * (1 - AREA_TOLERANCE)
        upper = PUNJAB_AREA_KM2 * (1 + AREA_TOLERANCE)
        if total < lower:
            warn(f"{where}: land-cover classes sum to {total:,.0f} km2 "
                 f"({PUNJAB_AREA_KM2 - total:,.0f} km2 short of Punjab area "
                 f"{PUNJAB_AREA_KM2:,.0f} km2) - partial mosaic coverage suspected")
        elif total > upper:
            warn(f"{where}: land-cover classes sum to {total:,.0f} km2, "
                 f"above Punjab area + 2%")


def validate_raw() -> set:
    print("== Raw monthly files ==")
    expected_files = {p.format(year=y) for p, _ in SPECS.values() for y in YEARS}
    found_files = {p.name for p in DATA_DIR.glob("*_Monthly.csv")}
    for extra in sorted(found_files - expected_files):
        warn(f"unexpected monthly file in data folder: {extra}")
    for missing in sorted(expected_files - found_files):
        err(f"missing expected file: {missing}")

    month_sets = {}
    for variable, (pattern, columns) in SPECS.items():
        print(f"-- {variable}")
        seen = set()
        for year in YEARS:
            path = DATA_DIR / pattern.format(year=year)
            if not path.exists():
                continue
            header, rows = read_csv(path)
            if header != columns:
                err(f"{path.name}: header mismatch\n"
                    f"           expected: {columns}\n"
                    f"           found:    {header}")
            for i, rec in enumerate(rows, start=2):
                where = f"{path.name} row {i}"
                if None in rec:
                    err(f"{where}: more fields than header columns")
                    continue
                try:
                    y, m = int(rec["year"]), int(rec["month"])
                except (TypeError, ValueError):
                    err(f"{where}: unparseable year/month "
                        f"({rec.get('year')!r}/{rec.get('month')!r})")
                    continue
                if y != year:
                    err(f"{where}: year column {y} does not match filename year {year}")
                if not 1 <= m <= 12:
                    err(f"{where}: month {m} out of range 1-12")
                    continue
                key = (y, m)
                if key in seen:
                    err(f"{where}: duplicate month {y}-{m:02d}")
                seen.add(key)
                check_ranges(variable, rec, y, m, where)

        for year in YEARS:
            got = sorted(m for (y, m) in seen if y == year)
            if year < 2026:
                missing = [m for m in range(1, 13) if m not in got]
                if missing:
                    err(f"{variable} {year}: months {missing} missing (expected all 12)")
                else:
                    ok(f"{year}: all 12 months present")
            else:
                if not got:
                    err(f"{variable} 2026: no months present")
                elif got != list(range(1, len(got) + 1)):
                    gaps = [m for m in range(1, max(got) + 1) if m not in got]
                    err(f"{variable} 2026: non-contiguous months, gaps at {gaps}")
                else:
                    ok(f"2026: months 1-{max(got)} present (partial year)")
        month_sets[variable] = seen

    reference = None
    for variable, seen in month_sets.items():
        if reference is None:
            reference = (variable, seen)
        elif seen != reference[1]:
            err(f"month coverage differs between {reference[0]} and {variable}")

    if reference is not None:
        covered = sorted(reference[1])
        missing = sorted(set(FULL_GRID) - reference[1])
        print(f"  coverage: {len(covered)} months, "
              f"{covered[0][0]}-{covered[0][1]:02d} to {covered[-1][0]}-{covered[-1][1]:02d}")
        if missing:
            label = ", ".join(f"{y}-{m:02d}" for y, m in missing)
            print(f"  [INFO]  months absent from export (not invented): {label}")
    return set(reference[1]) if reference else set()


def load_raw_map() -> dict:
    raw = {}
    for pattern, _ in SPECS.values():
        for year in YEARS:
            path = DATA_DIR / pattern.format(year=year)
            if not path.exists():
                continue
            _, rows = read_csv(path)
            for rec in rows:
                try:
                    key = (int(rec["year"]), int(rec["month"]))
                except (TypeError, ValueError):
                    continue
                raw.setdefault(key, {}).update(rec)
    return raw


def validate_processed(union_months: set) -> None:
    print("\n== processed/Punjab_Monthly_Clean.csv ==")
    if not PROCESSED_FILE.exists():
        print("  [INFO]  not present yet (run this script after cleaning)")
        return
    header, rows = read_csv(PROCESSED_FILE)
    if header != CLEAN_HEADER:
        err(f"unexpected header: {header}")
    if len(rows) != len(union_months):
        err(f"row count {len(rows)} does not match raw month count {len(union_months)}")
    else:
        ok(f"row count {len(rows)} matches raw month count")

    raw = load_raw_map()
    prev_date = None
    for i, rec in enumerate(rows, start=2):
        where = f"{PROCESSED_FILE.name} row {i}"
        if None in rec:
            err(f"{where}: more fields than header columns")
            continue
        date = str(rec.get("date", ""))
        try:
            y, m = int(date[:4]), int(date[5:7])
        except ValueError:
            err(f"{where}: unparseable date {date!r}")
            continue
        if date != f"{y}-{m:02d}-01":
            err(f"{where}: date {date!r} is not first-of-month ISO format")
        if prev_date is not None and date < prev_date:
            err(f"{where}: rows not sorted chronologically")
        prev_date = date
        if (y, m) not in union_months:
            err(f"{where}: month {y}-{m:02d} not present in raw data")
        if str(rec.get("year")) != str(y) or str(rec.get("month")) != str(m):
            err(f"{where}: year/month columns disagree with date")
        if rec.get("season") != season_for(m):
            err(f"{where}: season {rec.get('season')!r} != expected {season_for(m)!r}")
        for col in CLEAN_HEADER[4:]:
            v = rec.get(col)
            if v is None or str(v).strip() == "":
                err(f"{where}: empty value in column {col!r}")
                continue
            raw_val = raw.get((y, m), {}).get(col)
            if raw_val is None:
                err(f"{where}: column {col!r} has no raw counterpart")
            elif float(v) != float(raw_val):
                err(f"{where}: {col} value {v} differs from raw {raw_val}")
    if error_count == 0:
        ok("all values match raw exports; dates sorted; seasons consistent")


def main() -> int:
    print("Kisaan Dost monthly data validation")
    print(f"Data directory: {DATA_DIR}\n")
    union_months = validate_raw()
    validate_processed(union_months)
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
