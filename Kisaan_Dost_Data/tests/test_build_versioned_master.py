"""Tests for build_versioned_master.py — Step 7 validation.

Covers:
- Master v2 row/column counts
- No duplicate composite keys
- Weather coverage (28 districts × 48 months = 1,344)
- Null weather for 6 uncovered districts (with no_coverage_flag=True)
- Null weather for 2026 months (weather only covers 2022-2025)
- Context file has exactly 3 extra units
- Context file has source_table column
- Original master columns preserved
"""

import csv
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
MASTER_V2_PATH = ROOT / "processed" / "kisaan_dost_master_v2.csv"
CONTEXT_PATH = ROOT / "processed" / "kisaan_dost_context_only.csv"
MASTER_ORIG_PATH = ROOT / "processed" / "district_master_clean.csv"
WEATHER_PATH = ROOT / "processed" / "district_monthly_weather.csv"

EXPECTED_UNCOVERED = {
    "Gujrat District",
    "Lodhran District",
    "Mianwali District",
    "Narowal District",
    "Pakpattan District",
    "Sheikhupura District",
}

EXPECTED_CONTEXT_UNITS = {
    "Chiniot District",
    "Nankana Sahib District",
    "Cholistan Area",
}


def load_csv(path: Path):
    with path.open("r", encoding="utf-8", newline="") as fh:
        return list(csv.DictReader(fh))


class TestMasterV2Shape(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.rows = load_csv(MASTER_V2_PATH)
        cls.orig_rows = load_csv(MASTER_ORIG_PATH)

    def test_row_count_matches_master(self):
        self.assertEqual(len(self.rows), 1904)
        self.assertEqual(len(self.rows), len(self.orig_rows))

    def test_column_count(self):
        self.assertEqual(len(self.rows[0]), 27)

    def test_original_columns_preserved(self):
        orig_cols = list(self.orig_rows[0].keys())
        v2_cols = list(self.rows[0].keys())
        for col in orig_cols:
            self.assertIn(col, v2_cols, f"missing original column: {col}")

    def test_weather_columns_appended(self):
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
        for col in weather_cols:
            self.assertIn(col, self.rows[0], f"missing weather column: {col}")

    def test_no_duplicate_keys(self):
        keys = set()
        for row in self.rows:
            key = (row["year"], row["month"], row["district"])
            self.assertNotIn(key, keys, f"duplicate key: {key}")
            keys.add(key)

    def test_district_count(self):
        districts = {row["district"] for row in self.rows}
        self.assertEqual(len(districts), 34)


class TestWeatherCoverage(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.rows = load_csv(MASTER_V2_PATH)

    def test_weather_present_count(self):
        present = sum(1 for r in self.rows if r.get("t2m_mean_c", "") != "")
        self.assertEqual(present, 1344)

    def test_weather_null_count(self):
        null = sum(1 for r in self.rows if r.get("t2m_mean_c", "") == "")
        self.assertEqual(null, 560)

    def test_uncovered_districts_flagged(self):
        flagged = {
            r["district"] for r in self.rows if r.get("no_coverage_flag") == "True"
        }
        self.assertEqual(flagged, EXPECTED_UNCOVERED)

    def test_uncovered_districts_always_null(self):
        for row in self.rows:
            if row["district"] in EXPECTED_UNCOVERED:
                self.assertEqual(
                    row.get("t2m_mean_c", ""),
                    "",
                    f"uncovered district {row['district']} has weather data",
                )

    def test_covered_districts_have_weather_2022_2025(self):
        covered = {
            r["district"]
            for r in self.rows
            if r["district"] not in EXPECTED_UNCOVERED
        }
        for row in self.rows:
            if row["district"] in covered:
                year = int(row["year"])
                if 2022 <= year <= 2025:
                    self.assertNotEqual(
                        row.get("t2m_mean_c", ""),
                        "",
                        f"covered district {row['district']} missing weather in {year}-{row['month']}",
                    )

    def test_2026_months_have_null_weather(self):
        for row in self.rows:
            if int(row["year"]) == 2026:
                self.assertEqual(
                    row.get("t2m_mean_c", ""),
                    "",
                    f"2026 row has weather: {row['district']} {row['month']}",
                )

    def test_source_provider_when_present(self):
        for row in self.rows:
            if row.get("t2m_mean_c", "") != "":
                self.assertEqual(row.get("source_provider"), "nasa_power_merra2")


class TestContextFile(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.rows = load_csv(CONTEXT_PATH)

    def test_row_count(self):
        self.assertEqual(len(self.rows), 99)

    def test_exactly_three_extra_units(self):
        districts = {row["district"] for row in self.rows}
        self.assertEqual(districts, EXPECTED_CONTEXT_UNITS)

    def test_no_master_districts_in_context(self):
        master_rows = load_csv(MASTER_ORIG_PATH)
        master_districts = {row["district"] for row in master_rows}
        for row in self.rows:
            self.assertNotIn(
                row["district"],
                master_districts,
                f"master district {row['district']} found in context file",
            )

    def test_source_table_column_present(self):
        for row in self.rows:
            self.assertIn("source_table", row)
            self.assertTrue(row["source_table"], "empty source_table")

    def test_context_has_multiple_source_tables(self):
        tables = {row["source_table"] for row in self.rows}
        self.assertGreater(len(tables), 1, "expected multiple PBS source tables")


class TestNoDataFabrication(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.rows = load_csv(MASTER_V2_PATH)

    def test_no_dummy_weather_values(self):
        measurement_cols = ["t2m_mean_c", "rh2m_mean_percent", "precip_total_mm"]
        for row in self.rows:
            if row.get("t2m_mean_c", "") == "":
                for col in measurement_cols:
                    self.assertEqual(
                        row.get(col, ""),
                        "",
                        f"dummy value in {col} for {row['district']} {row['year']}-{row['month']}",
                    )

    def test_original_data_not_modified(self):
        orig_rows = load_csv(MASTER_ORIG_PATH)
        orig_cols = list(orig_rows[0].keys())
        for v2_row, orig_row in zip(self.rows, orig_rows):
            for col in orig_cols:
                self.assertEqual(
                    v2_row[col],
                    orig_row[col],
                    f"original column {col} modified for {orig_row['district']} {orig_row['year']}-{orig_row['month']}",
                )


if __name__ == "__main__":
    unittest.main()
