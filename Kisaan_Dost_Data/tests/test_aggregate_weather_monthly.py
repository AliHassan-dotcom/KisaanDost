"""Tests for aggregate_weather_monthly.py.

Tests cover:
- Data loading (grid mapping, master districts)
- Aggregation logic (mean vs sum, coverage tracking)
- Output CSV structure and validation
- Uncovered district handling
- Real-file integration
"""

from __future__ import annotations

import csv
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "scripts"))

from aggregate_weather_monthly import (
    OUTPUT_COLUMNS,
    aggregate_weather,
    load_grid_mapping,
    load_master_districts,
    validate_aggregation,
)

HAS_INPUT_FILES = (
    (ROOT / "processed" / "weather_join_keys.csv").exists()
    and (ROOT / "processed" / "district_coordinates.csv").exists()
    and (ROOT / "Historical Data").exists()
)


@unittest.skipUnless(HAS_INPUT_FILES, "requires input files on disk")
class TestDataLoaders(unittest.TestCase):
    """Data loading from real files."""

    def test_load_grid_mapping(self):
        mapping = load_grid_mapping()
        self.assertIsInstance(mapping, dict)
        self.assertEqual(len(mapping), 117)

    def test_grid_mapping_fields(self):
        mapping = load_grid_mapping()
        sample = next(iter(mapping.values()))
        required_keys = {"district", "normalized_district", "method", "is_fallback"}
        self.assertEqual(set(sample.keys()), required_keys)

    def test_grid_mapping_keys_are_tuples(self):
        mapping = load_grid_mapping()
        for key in mapping:
            self.assertIsInstance(key, tuple)
            self.assertEqual(len(key), 2)
            self.assertIsInstance(key[0], float)
            self.assertIsInstance(key[1], float)

    def test_load_master_districts(self):
        districts = load_master_districts()
        self.assertIsInstance(districts, dict)
        self.assertEqual(len(districts), 34)

    def test_master_districts_include_known(self):
        districts = load_master_districts()
        self.assertIn("Lahore", districts)
        self.assertIn("Faisalabad", districts)
        self.assertIn("Multan", districts)


@unittest.skipUnless(HAS_INPUT_FILES, "requires input files on disk")
class TestOutputCSV(unittest.TestCase):
    """Output CSV structure and content."""

    @classmethod
    def setUpClass(cls):
        cls.output_path = ROOT / "processed" / "district_monthly_weather.csv"
        if not cls.output_path.exists():
            raise unittest.SkipTest("output CSV not yet generated")
        with cls.output_path.open("r", encoding="utf-8", newline="") as fh:
            cls.rows = list(csv.DictReader(fh))

    def test_output_has_rows(self):
        self.assertGreater(len(self.rows), 0)

    def test_output_columns_exact(self):
        self.assertEqual(list(self.rows[0].keys()), OUTPUT_COLUMNS)

    def test_row_count(self):
        self.assertEqual(len(self.rows), 1632)

    def test_no_duplicate_keys(self):
        stats = validate_aggregation()
        self.assertEqual(stats["duplicate_keys"], 0)

    def test_district_count(self):
        districts = {r["district"] for r in self.rows}
        self.assertEqual(len(districts), 34)

    def test_year_month_range(self):
        year_months = {(r["year"], r["month"]) for r in self.rows}
        self.assertEqual(len(year_months), 48)

    def test_uncovered_districts_flagged(self):
        uncovered = {
            r["district"] for r in self.rows if r["no_coverage_flag"] == "True"
        }
        self.assertEqual(len(uncovered), 6)
        self.assertIn("Gujrat", uncovered)
        self.assertIn("Lodhran", uncovered)

    def test_uncovered_districts_have_null_weather(self):
        for r in self.rows:
            if r["no_coverage_flag"] == "True":
                self.assertEqual(r["t2m_mean_c"], "")
                self.assertEqual(r["rh2m_mean_percent"], "")
                self.assertEqual(r["precip_total_mm"], "")
                self.assertEqual(r["grid_points_used"], "0")

    def test_covered_districts_have_weather(self):
        for r in self.rows:
            if r["no_coverage_flag"] == "False":
                self.assertNotEqual(r["t2m_mean_c"], "")
                self.assertNotEqual(r["rh2m_mean_percent"], "")
                self.assertNotEqual(r["precip_total_mm"], "")
                self.assertGreater(int(r["grid_points_used"]), 0)

    def test_source_provider_consistent(self):
        providers = {r["source_provider"] for r in self.rows}
        self.assertEqual(providers, {"nasa_power_merra2"})

    def test_year_month_format(self):
        for r in self.rows[:20]:
            self.assertTrue(r["year"].isdigit())
            self.assertTrue(r["month"].isdigit())
            self.assertGreaterEqual(int(r["year"]), 2022)
            self.assertLessEqual(int(r["year"]), 2025)
            self.assertGreaterEqual(int(r["month"]), 1)
            self.assertLessEqual(int(r["month"]), 12)

    def test_grid_point_counts_non_negative(self):
        for r in self.rows:
            self.assertGreaterEqual(int(r["grid_points_used"]), 0)
            self.assertGreaterEqual(int(r["polygon_point_count"]), 0)
            self.assertGreaterEqual(int(r["fallback_point_count"]), 0)

    def test_polygon_plus_fallback_equals_total(self):
        for r in self.rows:
            if r["no_coverage_flag"] == "False":
                total = int(r["grid_points_used"])
                poly = int(r["polygon_point_count"])
                fall = int(r["fallback_point_count"])
                self.assertEqual(poly + fall, total)


@unittest.skipUnless(HAS_INPUT_FILES, "requires input files on disk")
class TestAggregationLogic(unittest.TestCase):
    """Aggregation correctness checks."""

    @classmethod
    def setUpClass(cls):
        cls.output_path = ROOT / "processed" / "district_monthly_weather.csv"
        with cls.output_path.open("r", encoding="utf-8", newline="") as fh:
            cls.rows = list(csv.DictReader(fh))

    def test_t2m_reasonable_range(self):
        for r in self.rows:
            if r["t2m_mean_c"] != "":
                val = float(r["t2m_mean_c"])
                self.assertGreater(val, -10)
                self.assertLess(val, 50)

    def test_rh2m_reasonable_range(self):
        for r in self.rows:
            if r["rh2m_mean_percent"] != "":
                val = float(r["rh2m_mean_percent"])
                self.assertGreater(val, 0)
                self.assertLess(val, 100)

    def test_precip_non_negative(self):
        for r in self.rows:
            if r["precip_total_mm"] != "":
                val = float(r["precip_total_mm"])
                self.assertGreaterEqual(val, 0)

    def test_source_files_covered_format(self):
        for r in self.rows:
            if r["source_files_covered"] != "":
                files = r["source_files_covered"].split("|")
                self.assertGreater(len(files), 0)
                for f in files:
                    self.assertTrue(f.endswith(".json"))


if __name__ == "__main__":
    unittest.main()
