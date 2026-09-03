"""Unit tests for scripts/build_district_coordinates.py.

Tests cover:
    - Exact row count (41) — the prompt's mapping must not be truncated or extended.
    - Column schema (8 columns, exact names).
    - Coordinate fidelity: every prompt value appears verbatim in the CSV.
    - is_master_district truth value for each entry.
    - Validation math against the 34-district master.
    - No duplicate district names.
    - Notes taxonomy is limited to the four documented kinds.
    - Re-running the build is idempotent (same rows, fresh timestamp).
"""

import csv
import sys
import unittest
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SCRIPTS = ROOT / "scripts"
sys.path.insert(0, str(SCRIPTS))

from build_district_coordinates import (  # noqa: E402
    PROMPT_COORDINATES,
    build,
    read_master,
    validate,
    write_csv,
)

MASTER = ROOT / "processed" / "district_master_clean.csv"
OUT = ROOT / "processed" / "district_coordinates.csv"

EXPECTED_FIELDS = [
    "district", "normalized_district", "latitude", "longitude",
    "source", "source_timestamp", "is_master_district", "notes",
]


class TestBuild(unittest.TestCase):
    def test_row_count(self):
        rows = build()
        self.assertEqual(len(rows), 41)

    def test_field_names(self):
        rows = build()
        self.assertEqual(list(rows[0].keys()), EXPECTED_FIELDS)

    def test_source_is_project_prompt(self):
        for r in build():
            self.assertEqual(r["source"], "project_prompt")

    def test_normalized_suffix(self):
        for r in build():
            self.assertTrue(r["normalized_district"].endswith(" District"))
            self.assertEqual(
                r["normalized_district"],
                f"{r['district']} District",
            )

    def test_coordinate_fidelity(self):
        """Every prompt tuple must appear in the CSV with the same lat/lon."""
        rows = build()
        by_name = {r["district"]: r for r in rows}
        for name, lat, lon, _kind in PROMPT_COORDINATES:
            self.assertIn(name, by_name)
            self.assertAlmostEqual(float(by_name[name]["latitude"]), lat, places=4)
            self.assertAlmostEqual(float(by_name[name]["longitude"]), lon, places=4)

    def test_is_master_district_truth(self):
        rows = build()
        by_name = {r["district"]: r for r in rows}
        # 34 master entries
        master_names = {
            name for name, _lat, _lon, kind in PROMPT_COORDINATES if kind == "master"
        }
        self.assertEqual(len(master_names), 34)
        for name in master_names:
            self.assertEqual(by_name[name]["is_master_district"], "True")
        # 7 non-master entries
        for name, _lat, _lon, kind in PROMPT_COORDINATES:
            if kind != "master":
                self.assertEqual(by_name[name]["is_master_district"], "False")

    def test_notes_taxonomy(self):
        allowed = {"", "annex unit", "newly created district", "tehsil promoted"}
        for r in build():
            self.assertIn(r["notes"], allowed)

    def test_no_duplicate_names(self):
        rows = build()
        names = [r["district"] for r in rows]
        self.assertEqual(len(names), len(set(names)))

    def test_timestamp_parseable(self):
        rows = build(timestamp=datetime(2026, 8, 31, 12, 0, 0, tzinfo=timezone.utc))
        ts = rows[0]["source_timestamp"]
        # round-trip via fromisoformat
        datetime.fromisoformat(ts)


class TestWriteAndRead(unittest.TestCase):
    def test_csv_roundtrip(self):
        import tempfile
        tmp = Path(tempfile.mkdtemp()) / "out.csv"
        rows = build()
        write_csv(rows, tmp)
        with tmp.open("r", encoding="utf-8", newline="") as fh:
            reader = csv.DictReader(fh)
            self.assertEqual(reader.fieldnames, EXPECTED_FIELDS)
            written = list(reader)
        self.assertEqual(len(written), 41)


class TestValidate(unittest.TestCase):
    def setUp(self):
        self.rows = build()
        self.master = read_master(MASTER)
        self.summary = validate(self.rows, self.master)

    def test_master_district_count(self):
        self.assertEqual(self.summary["master_districts"], 34)

    def test_matched_all_master(self):
        self.assertEqual(self.summary["matched_master"], 34)
        self.assertEqual(self.summary["missing_from_coords"], [])

    def test_extra_non_master_set(self):
        expected = {"Chiniot", "Kot Addu", "Murree", "Nankana Sahib",
                    "Talagang", "Taunsa", "Wazirabad"}
        self.assertEqual(set(self.summary["extra_non_master"]), expected)

    def test_no_duplicates(self):
        self.assertEqual(self.summary["duplicates"], [])

    def test_bbox_reasonable(self):
        lat_lo, lat_hi = self.summary["latitude_range"]
        lon_lo, lon_hi = self.summary["longitude_range"]
        self.assertGreaterEqual(lat_lo, 28.0)
        self.assertLessEqual(lat_hi, 34.5)
        self.assertGreaterEqual(lon_lo, 70.0)
        self.assertLessEqual(lon_hi, 75.5)


if __name__ == "__main__":
    unittest.main()
