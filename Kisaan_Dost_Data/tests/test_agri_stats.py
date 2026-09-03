"""Unit tests for Phase 8 Land Utilization and Water Availability pipeline."""

from __future__ import annotations

import csv
import importlib.util
from pathlib import Path
import pytest

ROOT = Path(__file__).resolve().parent.parent
PROCESSED_DIR = ROOT / "processed"

# Import processors
p13_path = ROOT / "scripts" / "13_process_land_utilization.py"
p13_spec = importlib.util.spec_from_file_location("p13", p13_path)
p13 = importlib.util.module_from_spec(p13_spec)
p13_spec.loader.exec_module(p13)

p14_path = ROOT / "scripts" / "14_process_water_availability.py"
p14_spec = importlib.util.spec_from_file_location("p14", p14_path)
p14 = importlib.util.module_from_spec(p14_spec)
p14_spec.loader.exec_module(p14)

p15_path = ROOT / "scripts" / "15_validate_land_water_metrics.py"
p15_spec = importlib.util.spec_from_file_location("p15", p15_path)
p15 = importlib.util.module_from_spec(p15_spec)
p15_spec.loader.exec_module(p15)


def test_land_utilization_processing():
    rows = p13.process_land_utilization()
    assert len(rows) >= 35
    districts = {r["district"] for r in rows}
    assert "Lahore District" in districts
    assert "Faisalabad District" in districts
    assert "Multan District" in districts

    lahore = next(r for r in rows if r["district"] == "Lahore District")
    assert lahore["total_farm_area_acres"] > 0
    assert lahore["cultivated_area_acres"] > 0
    assert lahore["wheat_area_acres"] > 0
    assert lahore["cultivated_share_pct"] > 0
    assert lahore["source_year"] == 2024


def test_water_availability_processing():
    rows = p14.process_water_availability()
    assert len(rows) >= 35
    districts = {r["district"] for r in rows}
    assert "Lahore District" in districts
    assert "Rawalpindi District" in districts

    # Lahore is tubewell/canal conjunctive
    lahore = next(r for r in rows if r["district"] == "Lahore District")
    assert lahore["irrigation_coverage_pct"] >= 80.0
    assert lahore["provincial_annual_canal_withdrawals_maf"] == 53.5

    # Rawalpindi is rainfed / Barani dominant
    rawalpindi = next(r for r in rows if r["district"] == "Rawalpindi District")
    assert rawalpindi["barani_share_pct"] > 50.0
    assert "Barani" in rawalpindi["primary_irrigation_mode"]


def test_land_water_validation():
    assert p15.run_full_validation() is True
