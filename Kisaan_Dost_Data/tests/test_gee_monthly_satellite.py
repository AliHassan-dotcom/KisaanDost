"""Unit and integration tests for GEE monthly district satellite baseline artifacts."""

from __future__ import annotations

import csv
import importlib.util
import sys
from pathlib import Path

import pytest

BASE_DIR = Path(__file__).resolve().parent.parent
SCRIPTS_DIR = BASE_DIR / "scripts"
PROCESSED_DIR = BASE_DIR / "processed"
SATELLITE_CSV = PROCESSED_DIR / "district_monthly_satellite_v1.csv"
COVERAGE_CSV = PROCESSED_DIR / "district_monthly_satellite_coverage_v1.csv"
JOIN_AUDIT_CSV = PROCESSED_DIR / "district_monthly_satellite_join_audit_v1.csv"

# Load validator module dynamically to support numbered script prefix
validator_path = SCRIPTS_DIR / "10_validate_gee_monthly_satellite.py"
spec = importlib.util.spec_from_file_location("validate_gee_satellite", validator_path)
validator_mod = importlib.util.module_from_spec(spec)
spec.loader.exec_module(validator_mod)

EXPECTED_HEADER = validator_mod.EXPECTED_HEADER
MASTER_34_DISTRICTS = validator_mod.MASTER_34_DISTRICTS
MISSING_BOUNDARY_DISTRICTS = validator_mod.MISSING_BOUNDARY_DISTRICTS
validate_satellite_artifacts = validator_mod.validate_satellite_artifacts


def test_satellite_csv_exists_and_row_count():
    """Verify that district_monthly_satellite_v1.csv exists and contains 1,632 rows."""
    assert SATELLITE_CSV.exists(), f"Missing file: {SATELLITE_CSV}"
    with SATELLITE_CSV.open("r", encoding="utf-8", newline="") as fh:
        reader = csv.DictReader(fh)
        rows = list(reader)
    assert len(rows) == 1632, f"Expected 1,632 rows, got {len(rows)}"


def test_schema_columns_and_headers():
    """Verify that the CSV header matches the 20-field specification."""
    with SATELLITE_CSV.open("r", encoding="utf-8", newline="") as fh:
        reader = csv.DictReader(fh)
        header = reader.fieldnames or []
    assert header == EXPECTED_HEADER


def test_temporal_coverage_2022_to_2025():
    """Verify all 34 master districts appear in all 48 months."""
    with SATELLITE_CSV.open("r", encoding="utf-8", newline="") as fh:
        rows = list(csv.DictReader(fh))

    counts: dict[str, int] = {d: 0 for d in MASTER_34_DISTRICTS}
    years_seen = set()
    months_seen = set()

    for r in rows:
        norm_d = r["normalized_district"]
        assert norm_d in MASTER_34_DISTRICTS, f"Unknown district {norm_d}"
        counts[norm_d] += 1
        years_seen.add(int(r["year"]))
        months_seen.add(int(r["month"]))

    assert years_seen == {2022, 2023, 2024, 2025}
    assert months_seen == set(range(1, 13))
    for dist, cnt in counts.items():
        assert cnt == 48, f"District {dist} has {cnt} rows, expected 48"


def test_missing_boundary_districts_have_null_metrics_and_flags():
    """Verify the 5 missing boundary districts have null metrics and explicit boundary flags."""
    with SATELLITE_CSV.open("r", encoding="utf-8", newline="") as fh:
        rows = list(csv.DictReader(fh))

    for r in rows:
        norm_d = r["normalized_district"]
        if norm_d in MISSING_BOUNDARY_DISTRICTS:
            assert r["data_status"] == "boundary_unavailable"
            assert r["no_coverage_flag"] == "True"
            assert r["quality_flag"] == "missing_authoritative_arcgis_polygon"
            assert r["ndvi_mean"] == ""
            assert r["ndvi_median"] == ""
            assert r["ndwi_mean"] == ""
            assert r["ndwi_median"] == ""
            assert r["valid_pixel_count"] == ""
            assert r["observation_count"] == ""


def test_physical_range_of_ndvi_and_ndwi():
    """Verify that all non-null NDVI and NDWI metrics fall within [-1.0, 1.0]."""
    with SATELLITE_CSV.open("r", encoding="utf-8", newline="") as fh:
        rows = list(csv.DictReader(fh))

    for r in rows:
        if r["ndvi_mean"]:
            val = float(r["ndvi_mean"])
            assert -1.0 <= val <= 1.0, f"NDVI out of bounds: {val}"
        if r["ndwi_mean"]:
            val = float(r["ndwi_mean"])
            assert -1.0 <= val <= 1.0, f"NDWI out of bounds: {val}"


def test_exclusion_of_non_master_districts():
    """Verify that Chiniot and Nankana Sahib are strictly excluded."""
    with SATELLITE_CSV.open("r", encoding="utf-8", newline="") as fh:
        rows = list(csv.DictReader(fh))

    districts = {r["normalized_district"] for r in rows}
    assert "Chiniot District" not in districts
    assert "Nankana Sahib District" not in districts


def test_coverage_and_join_audit_tables():
    """Verify coverage and join audit tables exist and have 34 rows."""
    assert COVERAGE_CSV.exists()
    assert JOIN_AUDIT_CSV.exists()

    with COVERAGE_CSV.open("r", encoding="utf-8", newline="") as fh:
        cov_rows = list(csv.DictReader(fh))
    assert len(cov_rows) == 34

    with JOIN_AUDIT_CSV.open("r", encoding="utf-8", newline="") as fh:
        audit_rows = list(csv.DictReader(fh))
    assert len(audit_rows) == 34


def test_validator_module_passes():
    """Verify that validate_satellite_artifacts() passes with 0 errors."""
    result = validate_satellite_artifacts()
    assert result["success"] is True
    assert len(result["errors"]) == 0
    assert result["total_rows"] == 1632
    assert result["matched_districts"] == 29
    assert result["missing_boundary_districts"] == 5
