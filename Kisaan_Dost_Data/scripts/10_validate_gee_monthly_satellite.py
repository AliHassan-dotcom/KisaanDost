#!/usr/bin/env python3
"""Validate GEE monthly district-level satellite baseline artifacts.

Can be run as a CLI or imported as a module. Validates:
1. Exact row count: 34 master districts × 48 months = 1,632 rows.
2. Uniqueness: No duplicate (year, month, normalized_district) tuples.
3. Completeness: All 34 master districts appear every month across 2022-2025.
4. Boundary Handling: 5 missing boundary districts have null metrics,
   data_status='boundary_unavailable', and no_coverage_flag=True.
5. Physical Plausibility: NDVI and NDWI metrics fall within [-1.0, 1.0].
6. Exclusion: Chiniot and Nankana Sahib are strictly excluded.
7. Metadata: Source product, spatial scale, date ranges, and timestamps present.
"""

from __future__ import annotations

import csv
import json
import sys
from pathlib import Path
from typing import Any, Dict, List, Set, Tuple

BASE_DIR = Path(__file__).resolve().parent.parent
PROCESSED_DIR = BASE_DIR / "processed"

SATELLITE_CSV = PROCESSED_DIR / "district_monthly_satellite_v1.csv"
COVERAGE_CSV = PROCESSED_DIR / "district_monthly_satellite_coverage_v1.csv"
JOIN_AUDIT_CSV = PROCESSED_DIR / "district_monthly_satellite_join_audit_v1.csv"

EXPECTED_YEARS = {2022, 2023, 2024, 2025}
EXPECTED_MONTHS = set(range(1, 13))
EXPECTED_MONTHS_COUNT = len(EXPECTED_YEARS) * len(EXPECTED_MONTHS)  # 48

MASTER_34_DISTRICTS = {
    "Attock District", "Bahawalnagar District", "Bahawalpur District", "Bhakkar District",
    "Chakwal District", "Dera Ghazi Khan District", "Faisalabad District", "Gujranwala District",
    "Gujrat District", "Hafizabad District", "Jhang District", "Jhelum District",
    "Kasur District", "Khanewal District", "Khushab District", "Lahore District",
    "Layyah District", "Lodhran District", "Mandi Bahauddin District", "Mianwali District",
    "Multan District", "Muzaffargarh District", "Narowal District", "Okara District",
    "Pakpattan District", "Rahim Yar Khan District", "Rajanpur District", "Rawalpindi District",
    "Sahiwal District", "Sargodha District", "Sheikhupura District", "Sialkot District",
    "Toba Tek Singh District", "Vehari District"
}

MISSING_BOUNDARY_DISTRICTS = {
    "Bhakkar District", "Jhang District", "Layyah District",
    "Muzaffargarh District", "Okara District"
}

EXCLUDED_DISTRICTS = {"Chiniot", "Chiniot District", "Nankana Sahib", "Nankana Sahib District"}

EXPECTED_HEADER = [
    "year",
    "month",
    "district",
    "normalized_district",
    "ndvi_mean",
    "ndvi_median",
    "ndwi_mean",
    "ndwi_median",
    "valid_pixel_count",
    "observation_count",
    "cloud_or_quality_fraction",
    "satellite_source",
    "product_id",
    "spatial_scale_m",
    "period_start",
    "period_end",
    "data_status",
    "no_coverage_flag",
    "quality_flag",
    "source_processing_timestamp",
]


def validate_satellite_artifacts() -> Dict[str, Any]:
    errors: List[str] = []
    warnings: List[str] = []

    # 1. Verify existence of all three artifacts
    for name, path in [
        ("satellite_csv", SATELLITE_CSV),
        ("coverage_csv", COVERAGE_CSV),
        ("join_audit_csv", JOIN_AUDIT_CSV),
    ]:
        if not path.exists():
            errors.append(f"Missing required artifact: {name} at {path}")

    if errors:
        return {
            "success": False,
            "errors": errors,
            "warnings": warnings,
            "total_rows": 0,
            "valid_rows": 0,
            "boundary_unavailable_rows": 0,
        }

    # 2. Validate district_monthly_satellite_v1.csv
    with SATELLITE_CSV.open("r", encoding="utf-8", newline="") as fh:
        reader = csv.DictReader(fh)
        header = reader.fieldnames or []
        rows = list(reader)

    if header != EXPECTED_HEADER:
        errors.append(f"Header mismatch: expected {EXPECTED_HEADER}, got {header}")

    expected_total_rows = len(MASTER_34_DISTRICTS) * EXPECTED_MONTHS_COUNT  # 1632
    if len(rows) != expected_total_rows:
        errors.append(f"Row count mismatch: expected {expected_total_rows}, got {len(rows)}")

    seen_keys: Set[Tuple[int, int, str]] = set()
    district_month_counts: Dict[str, int] = {d: 0 for d in MASTER_34_DISTRICTS}
    valid_data_rows = 0
    boundary_unavailable_rows = 0

    for idx, row in enumerate(rows, start=2):
        try:
            year = int(row["year"])
            month = int(row["month"])
        except ValueError:
            errors.append(f"Row {idx}: Invalid year/month format ({row.get('year')}, {row.get('month')})")
            continue

        if year not in EXPECTED_YEARS:
            errors.append(f"Row {idx}: Unexpected year {year}")
        if month not in EXPECTED_MONTHS:
            errors.append(f"Row {idx}: Unexpected month {month}")

        norm_district = row.get("normalized_district", "").strip()
        if not norm_district:
            errors.append(f"Row {idx}: Missing normalized_district")
            continue

        if norm_district in EXCLUDED_DISTRICTS:
            errors.append(f"Row {idx}: Excluded district present: {norm_district}")

        if norm_district not in MASTER_34_DISTRICTS:
            errors.append(f"Row {idx}: Non-master district found: {norm_district}")
            continue

        key = (year, month, norm_district)
        if key in seen_keys:
            errors.append(f"Row {idx}: Duplicate composite key {key}")
        seen_keys.add(key)
        district_month_counts[norm_district] += 1

        # Check metadata fields presence
        for meta_field in [
            "satellite_source", "product_id", "spatial_scale_m",
            "period_start", "period_end", "data_status",
            "no_coverage_flag", "quality_flag", "source_processing_timestamp"
        ]:
            if not row.get(meta_field, "").strip():
                errors.append(f"Row {idx} ({norm_district}): Missing required metadata field '{meta_field}'")

        # Invariant checks for missing vs matched boundary districts
        if norm_district in MISSING_BOUNDARY_DISTRICTS:
            boundary_unavailable_rows += 1
            if row.get("data_status") != "boundary_unavailable":
                errors.append(f"Row {idx} ({norm_district}): Expected data_status='boundary_unavailable', got '{row.get('data_status')}'")
            if row.get("no_coverage_flag") != "True":
                errors.append(f"Row {idx} ({norm_district}): Expected no_coverage_flag='True', got '{row.get('no_coverage_flag')}'")
            if row.get("quality_flag") != "missing_authoritative_arcgis_polygon":
                errors.append(f"Row {idx} ({norm_district}): Expected quality_flag='missing_authoritative_arcgis_polygon', got '{row.get('quality_flag')}'")

            for metric in ["ndvi_mean", "ndvi_median", "ndwi_mean", "ndwi_median", "valid_pixel_count", "observation_count"]:
                if row.get(metric, "").strip() != "":
                    errors.append(f"Row {idx} ({norm_district}): Metric '{metric}' must be null for missing boundary, got '{row.get(metric)}'")
        else:
            status = row.get("data_status")
            if status == "historical_satellite_baseline":
                valid_data_rows += 1
                if row.get("no_coverage_flag") != "False":
                    errors.append(f"Row {idx} ({norm_district}): Expected no_coverage_flag='False', got '{row.get('no_coverage_flag')}'")

                # Validate physical range of NDVI / NDWI
                for idx_name in ["ndvi_mean", "ndvi_median", "ndwi_mean", "ndwi_median"]:
                    val_str = row.get(idx_name, "").strip()
                    if not val_str:
                        errors.append(f"Row {idx} ({norm_district}): Missing value for '{idx_name}'")
                        continue
                    try:
                        val = float(val_str)
                        if not (-1.0 <= val <= 1.0):
                            errors.append(f"Row {idx} ({norm_district}): '{idx_name}' value {val} out of physical bounds [-1, 1]")
                    except ValueError:
                        errors.append(f"Row {idx} ({norm_district}): '{idx_name}' is not a valid float: '{val_str}'")
            elif status == "satellite_source_unavailable":
                if row.get("no_coverage_flag") != "True":
                    errors.append(f"Row {idx} ({norm_district}): Expected no_coverage_flag='True' for cloud-masked month, got '{row.get('no_coverage_flag')}'")
                if row.get("quality_flag") != "cloud_masked_no_valid_pixels":
                    errors.append(f"Row {idx} ({norm_district}): Expected quality_flag='cloud_masked_no_valid_pixels', got '{row.get('quality_flag')}'")
                for metric in ["ndvi_mean", "ndvi_median", "ndwi_mean", "ndwi_median"]:
                    if row.get(metric, "").strip() != "":
                        errors.append(f"Row {idx} ({norm_district}): Expected null metric '{metric}', got '{row.get(metric)}'")
            else:
                errors.append(f"Row {idx} ({norm_district}): Unexpected data_status='{status}'")

    # Verify every master district has exactly 48 months
    for dist, count in district_month_counts.items():
        if count != EXPECTED_MONTHS_COUNT:
            errors.append(f"District {dist} has {count} months (expected {EXPECTED_MONTHS_COUNT})")

    # 3. Validate coverage table
    with COVERAGE_CSV.open("r", encoding="utf-8", newline="") as fh:
        coverage_rows = list(csv.DictReader(fh))
    if len(coverage_rows) != len(MASTER_34_DISTRICTS):
        errors.append(f"Coverage table has {len(coverage_rows)} rows (expected {len(MASTER_34_DISTRICTS)})")

    # 4. Validate join audit table
    with JOIN_AUDIT_CSV.open("r", encoding="utf-8", newline="") as fh:
        audit_rows = list(csv.DictReader(fh))
    if len(audit_rows) != len(MASTER_34_DISTRICTS):
        errors.append(f"Join audit table has {len(audit_rows)} rows (expected {len(MASTER_34_DISTRICTS)})")

    summary = {
        "success": len(errors) == 0,
        "errors": errors,
        "warnings": warnings,
        "total_rows": len(rows),
        "valid_rows": valid_data_rows,
        "boundary_unavailable_rows": boundary_unavailable_rows,
        "expected_rows": expected_total_rows,
        "matched_districts": len(MASTER_34_DISTRICTS) - len(MISSING_BOUNDARY_DISTRICTS),
        "missing_boundary_districts": len(MISSING_BOUNDARY_DISTRICTS),
    }
    return summary


def main() -> int:
    result = validate_satellite_artifacts()
    print(json.dumps(result, indent=2))
    return 0 if result["success"] else 1


if __name__ == "__main__":
    sys.exit(main())
