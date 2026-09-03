"""Unit tests for scripts/build_open_meteo_url.py.

Coverage:
    - District lookup: success, case-insensitivity, ' District' suffix stripping,
      not-found error.
    - Raw lat/lng: direct pass-through, out-of-range rejection, partial-coords error.
    - Mutual exclusivity of district vs raw coords modes.
    - Parameter ordering exactly matches the project prompt template.
    - Variable lists contain the full template set (no drops).
    - Annex / tehsil-promoted districts are looked up and produce valid URLs.
    - `all_urls()` covers every row in the coordinate CSV (41 entries).
"""

import sys
from pathlib import Path
from urllib.parse import parse_qs, urlparse

ROOT = Path(__file__).resolve().parent.parent
SCRIPTS = ROOT / "scripts"
sys.path.insert(0, str(SCRIPTS))

import unittest  # noqa: E402
from build_open_meteo_url import (  # noqa: E402
    CURRENT_VARS,
    DAILY_VARS,
    HOURLY_VARS,
    MODELS,
    TIMEZONE,
    DistrictNotFoundError,
    all_urls,
    build_url,
    resolve_district,
)

COORDS = ROOT / "processed" / "district_coordinates.csv"

EXPECTED_ORDER = [
    "latitude", "longitude",
    "current", "hourly", "daily",
    "models", "timezone",
]


class TestDistrictLookup(unittest.TestCase):
    def test_lookup_master(self):
        row = resolve_district("Lahore")
        self.assertEqual(row["district"], "Lahore")
        self.assertEqual(row["is_master_district"], "True")
        self.assertEqual(float(row["latitude"]), 31.5204)
        self.assertEqual(float(row["longitude"]), 74.3587)

    def test_lookup_case_insensitive(self):
        self.assertEqual(resolve_district("lahore")["district"], "Lahore")
        self.assertEqual(resolve_district("LAHORE")["district"], "Lahore")

    def test_lookup_accepts_suffix(self):
        self.assertEqual(resolve_district("Lahore District")["district"], "Lahore")

    def test_lookup_multiword(self):
        row = resolve_district("Rahim Yar Khan")
        self.assertEqual(row["district"], "Rahim Yar Khan")
        self.assertEqual(float(row["latitude"]), 28.4212)

    def test_lookup_not_found(self):
        with self.assertRaises(DistrictNotFoundError):
            resolve_district("Not A District")

    def test_lookup_annex(self):
        row = resolve_district("Chiniot")
        self.assertEqual(row["is_master_district"], "False")
        self.assertEqual(row["notes"], "annex unit")

    def test_lookup_tehsil_promoted(self):
        row = resolve_district("Kot Addu")
        self.assertEqual(row["notes"], "tehsil promoted")


class TestBuildUrlDistrict(unittest.TestCase):
    def setUp(self):
        self.url = build_url(district="Lahore", coords_csv=COORDS)
        self.parsed = urlparse(self.url)
        self.qs = parse_qs(self.parsed.query, keep_blank_values=True)

    def test_base(self):
        self.assertEqual(self.parsed.scheme, "https")
        self.assertEqual(self.parsed.netloc, "api.open-meteo.com")
        self.assertEqual(self.parsed.path, "/v1/forecast")

    def test_parameter_ordering(self):
        # parse_qs does not preserve order; re-read from the raw query string
        raw = self.parsed.query
        seen = []
        for chunk in raw.split("&"):
            key = chunk.split("=", 1)[0]
            if key not in seen:
                seen.append(key)
        self.assertEqual(seen, EXPECTED_ORDER)

    def test_coordinates_match_master(self):
        self.assertEqual(self.qs["latitude"], ["31.5204"])
        self.assertEqual(self.qs["longitude"], ["74.3587"])

    def test_current_vars_complete(self):
        self.assertEqual(self.qs["current"][0].split(","), list(CURRENT_VARS))

    def test_hourly_vars_complete(self):
        self.assertEqual(self.qs["hourly"][0].split(","), list(HOURLY_VARS))

    def test_daily_vars_complete(self):
        self.assertEqual(self.qs["daily"][0].split(","), list(DAILY_VARS))

    def test_models(self):
        self.assertEqual(self.qs["models"][0].split(","), list(MODELS))

    def test_timezone_auto(self):
        self.assertEqual(self.qs["timezone"], [TIMEZONE])

    def test_no_percent_encoded_commas(self):
        self.assertNotIn("%2C", self.url)


class TestBuildUrlRaw(unittest.TestCase):
    def test_raw_passthrough(self):
        url = build_url(latitude=30.0, longitude=72.5, coords_csv=COORDS)
        qs = parse_qs(urlparse(url).query)
        self.assertEqual(qs["latitude"], ["30.0000"])
        self.assertEqual(qs["longitude"], ["72.5000"])

    def test_latitude_out_of_range(self):
        with self.assertRaises(ValueError):
            build_url(latitude=95.0, longitude=72.0)

    def test_longitude_out_of_range(self):
        with self.assertRaises(ValueError):
            build_url(latitude=31.0, longitude=200.0)

    def test_partial_coords_rejected(self):
        with self.assertRaises(ValueError):
            build_url(latitude=31.0)
        with self.assertRaises(ValueError):
            build_url(longitude=72.0)

    def test_district_and_coords_rejected(self):
        with self.assertRaises(ValueError):
            build_url(district="Lahore", latitude=31.0, longitude=74.0)

    def test_no_input_rejected(self):
        with self.assertRaises(ValueError):
            build_url()


class TestAllUrls(unittest.TestCase):
    def test_count(self):
        entries = all_urls(COORDS)
        self.assertEqual(len(entries), 41)

    def test_each_has_url(self):
        for e in all_urls(COORDS):
            self.assertTrue(e["url"].startswith("https://api.open-meteo.com/v1/forecast?"))
            qs = parse_qs(urlparse(e["url"]).query)
            self.assertEqual(len(qs["current"][0].split(",")), len(CURRENT_VARS))

    def test_master_and_annex_both_present(self):
        entries = all_urls(COORDS)
        master = [e for e in entries if e["is_master_district"] == "True"]
        annex  = [e for e in entries if e["notes"] == "annex unit"]
        self.assertEqual(len(master), 34)
        self.assertEqual(len(annex), 2)


class TestAnnexAndNonMaster(unittest.TestCase):
    def test_annex_url_builds(self):
        url = build_url(district="Nankana Sahib", coords_csv=COORDS)
        qs = parse_qs(urlparse(url).query)
        self.assertEqual(qs["latitude"], ["31.4492"])
        self.assertEqual(qs["longitude"], ["73.7124"])

    def test_tehsil_promoted_url_builds(self):
        url = build_url(district="Kot Addu", coords_csv=COORDS)
        qs = parse_qs(urlparse(url).query)
        self.assertEqual(qs["latitude"], ["30.4700"])


if __name__ == "__main__":
    unittest.main()
