"""Build versioned master by merging weather features into district master.

Input:
- `processed/district_master_clean.csv` (1,904 rows, 34 districts × 56 months)
- `processed/district_monthly_weather.csv` (1,632 rows, 34 districts × 48 months)
- PBS census files (8 tables, 37 districts including 3 non-master units)

Output:
- `processed/kisaan_dost_master_v2.csv` — merged master with weather
- `processed/kisaan_dost_context_only.csv` — PBS context for non-master units

Merge strategy:
- Left join from master on (year, month, normalized_district)
- Preserve null weather for 6 uncovered districts
- Preserve null weather for 2026-01 to 2026-08 (no weather data)
- Keep PBS extra units (Chiniot, Nankana Sahib, Cholistan) in context file

Stdlib only.
"""

from __future__ import annotations

import csv
import sys
from pathlib import Path
from typing import Any, Dict, List, Set

ROOT = Path(__file__).resolve().parent.parent

MASTER_PATH = ROOT / "processed" / "district_master_clean.csv"
WEATHER_PATH = ROOT / "processed" / "district_monthly_weather.csv"
OUTPUT_MASTER_PATH = ROOT / "processed" / "kisaan_dost_master_v2.csv"
OUTPUT_CONTEXT_PATH = ROOT / "processed" / "kisaan_dost_context_only.csv"

PBS_FILES = [
    "pbs_farm_structure.csv",
    "pbs_land_tenure.csv",
    "pbs_irrigation.csv",
    "pbs_crops.csv",
    "pbs_machinery.csv",
    "pbs_livestock.csv",
    "pbs_modern_farming.csv",
    "pbs_credit.csv",
]

# 34 master districts (from district_master_clean.csv)
# 3 extra units in PBS: Chiniot District, Nankana Sahib District, Cholistan Area
EXTRA_UNITS = {"Chiniot District", "Nankana Sahib District", "Cholistan Area"}


def load_master(path: Path = MASTER_PATH) -> List[Dict[str, str]]:
    """Load the authoritative district master."""
    with path.open("r", encoding="utf-8", newline="") as fh:
        reader = csv.DictReader(fh)
        return list(reader)


def load_weather(path: Path = WEATHER_PATH) -> Dict[tuple, Dict[str, str]]:
    """Load weather data indexed by (year, month, normalized_district)."""
    index: Dict[tuple, Dict[str, str]] = {}
    with path.open("r", encoding="utf-8", newline="") as fh:
        reader = csv.DictReader(fh)
        for row in reader:
            key = (row["year"], row["month"], row["normalized_district"])
            index[key] = row
    return index


def merge_master(
    master_path: Path = MASTER_PATH,
    weather_path: Path = WEATHER_PATH,
    output_path: Path = OUTPUT_MASTER_PATH,
) -> Dict[str, Any]:
    """Merge weather into master and write output CSV.

    Returns summary statistics.
    """
    master_rows = load_master(master_path)
    weather_index = load_weather(weather_path)

    # Weather columns to add (excluding year, month, district, normalized_district)
    weather_cols = [
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

    output_rows: List[Dict[str, str]] = []
    weather_matches = 0
    weather_nulls = 0
    uncovered_districts: Set[str] = set()

    for row in master_rows:
        year = row["year"]
        month = row["month"]
        district_normalized = row["district"]

        key = (year, month, district_normalized)
        weather = weather_index.get(key)

        out_row = dict(row)

        if weather:
            for col in weather_cols:
                out_row[col] = weather.get(col, "")
            weather_matches += 1
            if weather.get("no_coverage_flag") == "True":
                uncovered_districts.add(district_normalized)
                weather_nulls += 1
        else:
            for col in weather_cols:
                out_row[col] = ""
            weather_nulls += 1

        output_rows.append(out_row)

    # Write output
    output_cols = list(master_rows[0].keys()) + weather_cols
    with output_path.open("w", encoding="utf-8", newline="") as fh:
        writer = csv.DictWriter(fh, fieldnames=output_cols, lineterminator="\n")
        writer.writeheader()
        writer.writerows(output_rows)

    return {
        "master_rows_input": len(master_rows),
        "output_rows": len(output_rows),
        "weather_matches": weather_matches,
        "weather_nulls": weather_nulls,
        "uncovered_districts": sorted(uncovered_districts),
        "output_path": str(output_path),
    }


def build_context_file(
    output_path: Path = OUTPUT_CONTEXT_PATH,
) -> Dict[str, Any]:
    """Build context file with PBS data for non-master units.

    Concatenates all PBS tables for the 3 extra units, with a source_table column.
    """
    context_rows: List[Dict[str, str]] = []
    all_columns: Set[str] = {"source_table", "district"}
    table_counts: Dict[str, int] = {}

    for pbs_name in PBS_FILES:
        pbs_path = ROOT / "processed" / pbs_name
        if not pbs_path.exists():
            continue

        with pbs_path.open("r", encoding="utf-8", newline="") as fh:
            reader = csv.DictReader(fh)
            cols = reader.fieldnames or []
            all_columns.update(cols)

            count = 0
            for row in reader:
                district = row.get("district", "")
                if district in EXTRA_UNITS:
                    out_row = {"source_table": pbs_name.replace(".csv", "")}
                    out_row.update(row)
                    context_rows.append(out_row)
                    count += 1

            table_counts[pbs_name] = count

    # Sort columns for consistent output
    sorted_cols = sorted(all_columns)

    with output_path.open("w", encoding="utf-8", newline="") as fh:
        writer = csv.DictWriter(
            fh, fieldnames=sorted_cols, lineterminator="\n", extrasaction="ignore"
        )
        writer.writeheader()
        for row in context_rows:
            writer.writerow(row)

    return {
        "context_rows": len(context_rows),
        "extra_units": sorted(EXTRA_UNITS),
        "table_counts": table_counts,
        "output_path": str(output_path),
    }


def validate_merge(
    master_path: Path = OUTPUT_MASTER_PATH,
    context_path: Path = OUTPUT_CONTEXT_PATH,
) -> Dict[str, Any]:
    """Validate the merged master and context files."""
    # Master validation
    with master_path.open("r", encoding="utf-8", newline="") as fh:
        master_rows = list(csv.DictReader(fh))

    master_keys = set()
    duplicate_keys = 0
    districts = set()
    weather_present = 0
    weather_null = 0
    uncovered = set()

    for row in master_rows:
        key = (row["year"], row["month"], row["district"])
        if key in master_keys:
            duplicate_keys += 1
        master_keys.add(key)

        districts.add(row["district"])

        if row.get("t2m_mean_c", "") != "":
            weather_present += 1
        else:
            weather_null += 1

        if row.get("no_coverage_flag") == "True":
            uncovered.add(row["district"])

    # Context validation
    with context_path.open("r", encoding="utf-8", newline="") as fh:
        context_rows = list(csv.DictReader(fh))

    context_districts = {row.get("district", "") for row in context_rows}

    return {
        "master_rows": len(master_rows),
        "master_districts": len(districts),
        "duplicate_keys": duplicate_keys,
        "weather_present_rows": weather_present,
        "weather_null_rows": weather_null,
        "uncovered_districts": sorted(uncovered),
        "context_rows": len(context_rows),
        "context_districts": sorted(context_districts),
        "master_columns": list(master_rows[0].keys()) if master_rows else [],
    }


if __name__ == "__main__":
    print("Building versioned master...")
    master_stats = merge_master()
    print(f"  Master rows: {master_stats['master_rows_input']} -> {master_stats['output_rows']}")
    print(f"  Weather matches: {master_stats['weather_matches']}")
    print(f"  Weather nulls: {master_stats['weather_nulls']}")
    print(f"  Uncovered: {len(master_stats['uncovered_districts'])} districts")

    print("\nBuilding context file...")
    context_stats = build_context_file()
    print(f"  Context rows: {context_stats['context_rows']}")
    print(f"  Extra units: {context_stats['extra_units']}")

    print("\nValidation...")
    stats = validate_merge()
    print(f"  Duplicate keys: {stats['duplicate_keys']}")
    print(f"  Weather present: {stats['weather_present_rows']}")
    print(f"  Weather null: {stats['weather_null_rows']}")
    print(f"  Uncovered: {stats['uncovered_districts']}")
    print(f"  Context districts: {stats['context_districts']}")
