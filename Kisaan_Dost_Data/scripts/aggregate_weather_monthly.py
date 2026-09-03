"""Aggregate daily NASA POWER weather records to district-month level.

Input:
- `processed/weather_join_keys.csv` (grid-point → district mapping)
- NASA POWER JSON files from `Historical Data/` (via parse_nasa_power_json)
- `processed/district_coordinates.csv` (34 master districts)

Aggregation rules:
- T2M → monthly mean (°C)
- RH2M → monthly mean (%)
- PRECTOTCORR → monthly sum (mm)

Output: `processed/district_monthly_weather.csv` — one row per
(district, year, month) with 13 columns.

Stdlib only.
"""

from __future__ import annotations

import csv
import sys
from collections import defaultdict
from pathlib import Path
from typing import Any, Dict, List, Set, Tuple

# Ensure scripts/ is importable
sys.path.insert(0, str(Path(__file__).resolve().parent))
from parse_nasa_power_json import iter_records  # noqa: E402

ROOT = Path(__file__).resolve().parent.parent
JOIN_KEYS_PATH = ROOT / "processed" / "weather_join_keys.csv"
COORDS_PATH = ROOT / "processed" / "district_coordinates.csv"
WEATHER_DIR = ROOT / "Historical Data"
OUTPUT_PATH = ROOT / "processed" / "district_monthly_weather.csv"

OUTPUT_COLUMNS = [
    "year",
    "month",
    "district",
    "normalized_district",
    "t2m_mean_c",
    "rh2m_mean_percent",
    "precip_total_mm",
    "grid_points_used",
    "polygon_point_count",
    "fallback_point_count",
    "no_coverage_flag",
    "source_provider",
    "source_files_covered",
]


# ---------------------------------------------------------------------------
# Data loaders
# ---------------------------------------------------------------------------

def load_grid_mapping(
    join_keys_path: Path = JOIN_KEYS_PATH,
) -> Dict[Tuple[float, float], Dict[str, Any]]:
    """Extract unique grid-point → district mapping from join_keys CSV.

    Returns {(lon, lat): {district, normalized_district, method, is_fallback}}.
    """
    mapping: Dict[Tuple[float, float], Dict[str, Any]] = {}
    with join_keys_path.open("r", encoding="utf-8", newline="") as fh:
        reader = csv.DictReader(fh)
        for row in reader:
            key = (float(row["grid_lon"]), float(row["grid_lat"]))
            if key not in mapping:
                mapping[key] = {
                    "district": row["district"],
                    "normalized_district": row["normalized_district"],
                    "method": row["method"],
                    "is_fallback": row["is_fallback"],
                }
    return mapping


def load_master_districts(
    coords_path: Path = COORDS_PATH,
) -> Dict[str, str]:
    """Load 34 master districts from district_coordinates.csv.

    Returns {district: normalized_district}.
    """
    districts = {}
    with coords_path.open("r", encoding="utf-8", newline="") as fh:
        reader = csv.DictReader(fh)
        for row in reader:
            if row["is_master_district"] == "True":
                districts[row["district"]] = row["normalized_district"]
    return districts


# ---------------------------------------------------------------------------
# Aggregation
# ---------------------------------------------------------------------------

def aggregate_weather(
    weather_dir: Path = WEATHER_DIR,
    join_keys_path: Path = JOIN_KEYS_PATH,
    coords_path: Path = COORDS_PATH,
    output_path: Path = OUTPUT_PATH,
) -> Dict[str, Any]:
    """Run the full aggregation and write the output CSV.

    Returns a summary dict with counts for the report.
    """
    grid_mapping = load_grid_mapping(join_keys_path)
    master_districts = load_master_districts(coords_path)

    # Accumulators: {(district, year, month): {param: {"sum": x, "count": n}}}
    accum: Dict[Tuple[str, int, int], Dict[str, Dict[str, float]]] = defaultdict(
        lambda: {
            "T2M": {"sum": 0.0, "count": 0},
            "RH2M": {"sum": 0.0, "count": 0},
            "PRECTOTCORR": {"sum": 0.0, "count": 0},
        }
    )

    # Tracking: {(district, year, month): {grid_points, polygon_points, fallback_points, source_files}}
    tracking: Dict[Tuple[str, int, int], Dict[str, Any]] = defaultdict(
        lambda: {
            "grid_points": set(),
            "polygon_points": set(),
            "fallback_points": set(),
            "source_files": set(),
        }
    )

    json_files = sorted(weather_dir.glob("*.json"))
    total_records = 0
    unmatched = 0

    for jf in json_files:
        source_file = jf.name
        for rec in iter_records(jf):
            key = (rec["lon"], rec["lat"])
            mapping = grid_mapping.get(key)
            if mapping is None:
                unmatched += 1
                continue

            district = mapping["district"]
            year = rec["year"]
            month = rec["month"]
            param = rec["parameter"]
            value = rec["value"]

            agg_key = (district, year, month)
            accum[agg_key][param]["sum"] += value
            accum[agg_key][param]["count"] += 1

            track = tracking[agg_key]
            track["grid_points"].add(key)
            if mapping["method"] == "polygon":
                track["polygon_points"].add(key)
            elif mapping["method"] == "nearest_centroid":
                track["fallback_points"].add(key)
            track["source_files"].add(source_file)

            total_records += 1

    # Build output rows
    rows: List[Dict[str, Any]] = []

    # 1. Districts with coverage
    for agg_key, params in accum.items():
        district, year, month = agg_key
        track = tracking[agg_key]

        t2m = params["T2M"]
        rh2m = params["RH2M"]
        precip = params["PRECTOTCORR"]

        t2m_mean = t2m["sum"] / t2m["count"] if t2m["count"] > 0 else None
        rh2m_mean = rh2m["sum"] / rh2m["count"] if rh2m["count"] > 0 else None
        precip_total = precip["sum"] if precip["count"] > 0 else None

        rows.append({
            "year": year,
            "month": month,
            "district": district,
            "normalized_district": master_districts.get(district, f"{district} District"),
            "t2m_mean_c": f"{t2m_mean:.4f}" if t2m_mean is not None else "",
            "rh2m_mean_percent": f"{rh2m_mean:.4f}" if rh2m_mean is not None else "",
            "precip_total_mm": f"{precip_total:.4f}" if precip_total is not None else "",
            "grid_points_used": len(track["grid_points"]),
            "polygon_point_count": len(track["polygon_points"]),
            "fallback_point_count": len(track["fallback_points"]),
            "no_coverage_flag": "False",
            "source_provider": "nasa_power_merra2",
            "source_files_covered": "|".join(sorted(track["source_files"])),
        })

    # 2. Districts with no coverage (all year-months)
    covered_districts = {k[0] for k in accum.keys()}
    uncovered = sorted(set(master_districts.keys()) - covered_districts)
    year_months = {(y, m) for (_, y, m) in accum.keys()}

    for district in uncovered:
        for year, month in sorted(year_months):
            rows.append({
                "year": year,
                "month": month,
                "district": district,
                "normalized_district": master_districts[district],
                "t2m_mean_c": "",
                "rh2m_mean_percent": "",
                "precip_total_mm": "",
                "grid_points_used": 0,
                "polygon_point_count": 0,
                "fallback_point_count": 0,
                "no_coverage_flag": "True",
                "source_provider": "nasa_power_merra2",
                "source_files_covered": "",
            })

    # Sort by year, month, district
    rows.sort(key=lambda r: (r["year"], r["month"], r["district"]))

    # Write output
    with output_path.open("w", encoding="utf-8", newline="") as fh:
        writer = csv.DictWriter(fh, fieldnames=OUTPUT_COLUMNS, lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)

    return {
        "total_records_processed": total_records,
        "unmatched_records": unmatched,
        "total_rows": len(rows),
        "covered_districts": len(covered_districts),
        "uncovered_districts": uncovered,
        "year_months": len(year_months),
        "json_files_processed": len(json_files),
        "output_path": str(output_path),
    }


# ---------------------------------------------------------------------------
# Validation
# ---------------------------------------------------------------------------

def validate_aggregation(csv_path: Path = OUTPUT_PATH) -> Dict[str, Any]:
    """Read the output CSV and return validation statistics."""
    rows: List[Dict[str, str]] = []
    with csv_path.open("r", encoding="utf-8", newline="") as fh:
        reader = csv.DictReader(fh)
        rows = list(reader)

    total = len(rows)
    districts = set()
    uncovered = set()
    duplicate_keys = 0
    seen_keys = set()
    null_weather = 0
    valid_weather = 0

    for r in rows:
        key = (r["year"], r["month"], r["district"])
        if key in seen_keys:
            duplicate_keys += 1
        seen_keys.add(key)

        districts.add(r["district"])
        if r["no_coverage_flag"] == "True":
            uncovered.add(r["district"])
            null_weather += 1
        else:
            valid_weather += 1

    # Check aggregation methods (sample)
    sample_checks = []
    for r in rows[:10]:
        if r["no_coverage_flag"] == "False":
            has_t2m = r["t2m_mean_c"] != ""
            has_rh2m = r["rh2m_mean_percent"] != ""
            has_precip = r["precip_total_mm"] != ""
            sample_checks.append({
                "district": r["district"],
                "year": r["year"],
                "month": r["month"],
                "has_t2m": has_t2m,
                "has_rh2m": has_rh2m,
                "has_precip": has_precip,
            })

    return {
        "total_rows": total,
        "unique_districts": len(districts),
        "districts": sorted(districts),
        "uncovered_districts": sorted(uncovered),
        "uncovered_count": len(uncovered),
        "duplicate_keys": duplicate_keys,
        "null_weather_rows": null_weather,
        "valid_weather_rows": valid_weather,
        "sample_checks": sample_checks,
        "columns": list(rows[0].keys()) if rows else [],
    }


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    summary = aggregate_weather()
    print(f"Total records processed: {summary['total_records_processed']}")
    print(f"Unmatched records: {summary['unmatched_records']}")
    print(f"Total output rows: {summary['total_rows']}")
    print(f"Covered districts: {summary['covered_districts']}")
    print(f"Uncovered districts: {len(summary['uncovered_districts'])}")
    print(f"Year-months: {summary['year_months']}")
    print(f"Output: {summary['output_path']}")

    stats = validate_aggregation()
    print(f"\nValidation:")
    print(f"  Duplicate keys: {stats['duplicate_keys']}")
    print(f"  Null weather rows: {stats['null_weather_rows']}")
    print(f"  Valid weather rows: {stats['valid_weather_rows']}")
