"""Unit tests for scripts/parse_nasa_power_json.py.

Real-file tests use `Historical Data/2024-T2M.json` (leap year, 117 features,
366 days). Synthetic tests inject a mutated copy to exercise the fill-value
filter and the malformed-file gate.
"""

import json
import shutil
import sys
import tempfile
import unittest
from datetime import date
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SCRIPTS = ROOT / "scripts"
sys.path.insert(0, str(SCRIPTS))

from parse_nasa_power_json import (  # noqa: E402
    NasaPowerParseError,
    iter_records,
    parse_file,
    summarize_file,
)

REAL_FILE = ROOT / "Historical Data" / "2024-T2M.json"
REAL_FILE_2022 = ROOT / "Historical Data" / "2022-T2M.json"
REAL_FILE_2025 = ROOT / "Historical Data" / "2025-PRECTOTCORR.json"


@unittest.skipUnless(REAL_FILE.exists(), "real NASA POWER file not on disk")
class TestRealFileParsing(unittest.TestCase):
    def test_record_count_leap_year(self):
        recs = parse_file(REAL_FILE)
        self.assertEqual(len(recs), 117 * 366)

    def test_record_count_non_leap_2022(self):
        recs = parse_file(REAL_FILE_2022)
        self.assertEqual(len(recs), 117 * 365)

    def test_record_count_non_leap_2025(self):
        recs = parse_file(REAL_FILE_2025)
        self.assertEqual(len(recs), 117 * 365)

    def test_record_keys(self):
        rec = next(iter(iter_records(REAL_FILE)))
        expected = {
            "source", "file_path", "parameter", "units",
            "year", "month", "day", "date",
            "lon", "lat", "elevation_m", "value",
        }
        self.assertEqual(set(rec.keys()), expected)

    def test_source_and_parameter(self):
        rec = next(iter(iter_records(REAL_FILE)))
        self.assertEqual(rec["source"], "nasa_power_merra2")
        self.assertEqual(rec["parameter"], "T2M")
        self.assertEqual(rec["units"], "C")

    def test_prectotcorr_units(self):
        rec = next(iter(iter_records(REAL_FILE_2025)))
        self.assertEqual(rec["parameter"], "PRECTOTCORR")
        self.assertEqual(rec["units"], "mm/day")

    def test_first_and_last_date(self):
        dates = sorted({r["date"] for r in iter_records(REAL_FILE)})
        self.assertEqual(dates[0], "2024-01-01")
        self.assertEqual(dates[-1], "2024-12-31")

    def test_feb_29_present_in_leap_year(self):
        dates = {r["date"] for r in iter_records(REAL_FILE)}
        self.assertIn("2024-02-29", dates)

    def test_coordinate_spread(self):
        lons = sorted({r["lon"] for r in iter_records(REAL_FILE)})
        lats = sorted({r["lat"] for r in iter_records(REAL_FILE)})
        self.assertEqual(len(lons), 9)
        self.assertEqual(len(lats), 13)
        self.assertEqual(min(lons), 70.0)
        self.assertEqual(max(lons), 75.0)
        self.assertEqual(min(lats), 28.0)
        self.assertEqual(max(lats), 34.0)

    def test_value_is_finite(self):
        for rec in iter_records(REAL_FILE):
            self.assertNotEqual(rec["value"], -999.0)


@unittest.skipUnless(REAL_FILE.exists(), "real NASA POWER file not on disk")
class TestFillValueFiltering(unittest.TestCase):
    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp())
        self.mutated = self.tmp / "2024-T2M-mutated.json"
        shutil.copy(REAL_FILE, self.mutated)
        with self.mutated.open("r", encoding="utf-8") as fh:
            doc = json.load(fh)
        feat = doc["features"][0]
        param = list(feat["properties"]["parameter"].keys())[0]
        daily = feat["properties"]["parameter"][param]
        self.injected_key = "20240115"
        self.original_value = daily[self.injected_key]
        daily[self.injected_key] = -999
        with self.mutated.open("w", encoding="utf-8") as fh:
            json.dump(doc, fh)

    def tearDown(self):
        shutil.rmtree(self.tmp, ignore_errors=True)

    def test_fill_value_is_dropped(self):
        recs_for_point = [
            r for r in iter_records(self.mutated)
            if r["lon"] == 70.0 and r["lat"] == 28.0
        ]
        dates = {r["date"] for r in recs_for_point}
        self.assertNotIn("2024-01-15", dates)
        self.assertEqual(len(recs_for_point), 366 - 1)

    def test_other_points_unchanged(self):
        recs_other = [
            r for r in iter_records(self.mutated)
            if not (r["lon"] == 70.0 and r["lat"] == 28.0)
        ]
        self.assertEqual(len(recs_other), 116 * 366)


class TestMalformedFiles(unittest.TestCase):
    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp())

    def tearDown(self):
        shutil.rmtree(self.tmp, ignore_errors=True)

    def _write(self, name: str, payload) -> Path:
        p = self.tmp / name
        with p.open("w", encoding="utf-8") as fh:
            json.dump(payload, fh)
        return p

    def test_missing_features_key(self):
        p = self._write("bad.json", {"type": "FeatureCollection", "header": {}})
        with self.assertRaises(NasaPowerParseError):
            parse_file(p)

    def test_wrong_type(self):
        p = self._write(
            "bad.json",
            {"type": "Feature", "features": [], "header": {"fill_value": -999}},
        )
        with self.assertRaises(NasaPowerParseError):
            parse_file(p)

    def test_wrong_fill_value(self):
        p = self._write(
            "bad.json",
            {"type": "FeatureCollection", "features": [], "header": {"fill_value": 0}},
        )
        with self.assertRaises(NasaPowerParseError):
            parse_file(p)


@unittest.skipUnless(REAL_FILE.exists(), "real NASA POWER file not on disk")
class TestSummarize(unittest.TestCase):
    def test_summarize_counts(self):
        info = summarize_file(REAL_FILE)
        self.assertEqual(info["records"], 117 * 366)
        self.assertEqual(info["sample"]["parameter"], "T2M")


if __name__ == "__main__":
    unittest.main()
