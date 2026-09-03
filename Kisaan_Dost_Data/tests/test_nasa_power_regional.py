"""Tests for parse_nasa_power_regional.py.

Tests cover:
- Schema validation on the real regional file (2024-T2M-regional.json)
- Record count = 117 × 366 for 2024 (leap year)
- Date parsing correctness (first day, last day, Feb-29)
- Fill-value filtering (synthetic injection)
- Coordinate extraction (9 unique lons, 13 unique lats)
- Parameter metadata extraction
- Source field = "nasa_power_regional_merra2"
- Graceful error on malformed files
"""

from __future__ import annotations

import json
import shutil
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
REGIONAL_FILE = ROOT / "raw" / "regional" / "2024-T2M-regional.json"

sys.path.insert(0, str(ROOT / "scripts"))
from parse_nasa_power_regional import (
    FILL_VALUE,
    NasaPowerRegionalParseError,
    iter_records,
    parse_file,
    summarize_file,
)


@unittest.skipUnless(REGIONAL_FILE.exists(), "requires regional file on disk")
class TestRealFileParsing(unittest.TestCase):
    """Parse the real 2024-T2M-regional.json file."""

    @classmethod
    def setUpClass(cls):
        cls.records = parse_file(REGIONAL_FILE)

    def test_record_count(self):
        self.assertEqual(len(self.records), 117 * 366)

    def test_source_field(self):
        sources = {r["source"] for r in self.records}
        self.assertEqual(sources, {"nasa_power_regional_merra2"})

    def test_parameter_field(self):
        params = {r["parameter"] for r in self.records}
        self.assertEqual(params, {"T2M"})

    def test_units_field(self):
        units = {r["units"] for r in self.records}
        self.assertEqual(units, {"C"})

    def test_date_range(self):
        dates = {r["date"] for r in self.records}
        self.assertIn("2024-01-01", dates)
        self.assertIn("2024-12-31", dates)

    def test_feb_29_present(self):
        dates = {r["date"] for r in self.records}
        self.assertIn("2024-02-29", dates)

    def test_unique_grid_points(self):
        points = {(r["lon"], r["lat"]) for r in self.records}
        self.assertEqual(len(points), 117)

    def test_unique_longitudes(self):
        lons = {r["lon"] for r in self.records}
        self.assertEqual(len(lons), 9)

    def test_unique_latitudes(self):
        lats = {r["lat"] for r in self.records}
        self.assertEqual(len(lats), 13)

    def test_record_fields_complete(self):
        sample = self.records[0]
        required_keys = {
            "source",
            "file_path",
            "parameter",
            "units",
            "year",
            "month",
            "day",
            "date",
            "lon",
            "lat",
            "elevation_m",
            "value",
        }
        self.assertEqual(set(sample.keys()), required_keys)

    def test_value_is_float(self):
        for r in self.records[:10]:
            self.assertIsInstance(r["value"], float)


@unittest.skipUnless(REGIONAL_FILE.exists(), "requires regional file on disk")
class TestFillValueFiltering(unittest.TestCase):
    """Verify that fill values (-999) are filtered out."""

    def setUp(self):
        self.tmpdir = Path(tempfile.mkdtemp())
        self.tmpfile = self.tmpdir / "synthetic.json"
        shutil.copy(REGIONAL_FILE, self.tmpfile)

        with self.tmpfile.open("r", encoding="utf-8") as fh:
            doc = json.load(fh)

        feat = doc["features"][0]
        param_key = list(feat["properties"]["parameter"].keys())[0]
        first_date = list(feat["properties"]["parameter"][param_key].keys())[0]
        feat["properties"]["parameter"][param_key][first_date] = FILL_VALUE

        with self.tmpfile.open("w", encoding="utf-8") as fh:
            json.dump(doc, fh)

    def tearDown(self):
        shutil.rmtree(self.tmpdir)

    def test_fill_value_dropped(self):
        records = parse_file(self.tmpfile)
        self.assertEqual(len(records), 117 * 366 - 1)


@unittest.skipUnless(REGIONAL_FILE.exists(), "requires regional file on disk")
class TestMalformedFiles(unittest.TestCase):
    """Graceful error handling for malformed files."""

    def test_missing_features(self):
        tmpdir = Path(tempfile.mkdtemp())
        tmpfile = tmpdir / "bad.json"
        with REGIONAL_FILE.open("r", encoding="utf-8") as fh:
            doc = json.load(fh)
        del doc["features"]
        with tmpfile.open("w", encoding="utf-8") as fh:
            json.dump(doc, fh)

        with self.assertRaises(NasaPowerRegionalParseError):
            parse_file(tmpfile)
        shutil.rmtree(tmpdir)

    def test_wrong_type(self):
        tmpdir = Path(tempfile.mkdtemp())
        tmpfile = tmpdir / "bad.json"
        with REGIONAL_FILE.open("r", encoding="utf-8") as fh:
            doc = json.load(fh)
        doc["type"] = "NotAFeatureCollection"
        with tmpfile.open("w", encoding="utf-8") as fh:
            json.dump(doc, fh)

        with self.assertRaises(NasaPowerRegionalParseError):
            parse_file(tmpfile)
        shutil.rmtree(tmpdir)

    def test_wrong_fill_value(self):
        tmpdir = Path(tempfile.mkdtemp())
        tmpfile = tmpdir / "bad.json"
        with REGIONAL_FILE.open("r", encoding="utf-8") as fh:
            doc = json.load(fh)
        doc["header"]["fill_value"] = -9999
        with tmpfile.open("w", encoding="utf-8") as fh:
            json.dump(doc, fh)

        with self.assertRaises(NasaPowerRegionalParseError):
            parse_file(tmpfile)
        shutil.rmtree(tmpdir)


@unittest.skipUnless(REGIONAL_FILE.exists(), "requires regional file on disk")
class TestSummarize(unittest.TestCase):
    """Summarize API."""

    def test_summarize_returns_count(self):
        info = summarize_file(REGIONAL_FILE)
        self.assertEqual(info["records"], 117 * 366)
        self.assertIn("sample", info)
        self.assertIsNotNone(info["sample"])


if __name__ == "__main__":
    unittest.main()
