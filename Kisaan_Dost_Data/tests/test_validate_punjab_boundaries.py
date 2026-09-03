"""Unit tests for scripts/validate_punjab_boundaries.py.

Real-file tests use the saved GeoJSON at
`raw/arcgis/punjab_district_boundaries.geojson`. Malformed-file tests inject
synthetic JSON into a tempdir.
"""

import json
import shutil
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SCRIPTS = ROOT / "scripts"
sys.path.insert(0, str(SCRIPTS))

from validate_punjab_boundaries import (  # noqa: E402
    BoundaryValidationError,
    validate,
)

REAL_GEOJSON = ROOT / "raw" / "arcgis" / "punjab_district_boundaries.geojson"
MASTER = ROOT / "processed" / "district_master_clean.csv"


@unittest.skipUnless(REAL_GEOJSON.exists(), "boundary GeoJSON not on disk")
class TestRealFile(unittest.TestCase):
    def setUp(self):
        self.result = validate(REAL_GEOJSON, MASTER)

    def test_feature_count(self):
        self.assertEqual(self.result["feature_count"], 31)

    def test_crs_wgs84(self):
        self.assertIn("4326", self.result["crs"])

    def test_all_geometries_valid_type(self):
        for r in self.result["records"]:
            self.assertIn(r["geometry_type"], ("Polygon", "MultiPolygon"))

    def test_vertex_counts_reasonable(self):
        for r in self.result["records"]:
            self.assertGreaterEqual(r["vertex_count"], 100)
            self.assertLessEqual(r["vertex_count"], 50_000)

    def test_bboxes_inside_punjab_envelope(self):
        for r in self.result["records"]:
            self.assertGreaterEqual(r["bbox_lon_min"], 68.0)
            self.assertLessEqual(r["bbox_lon_max"], 77.0)
            self.assertGreaterEqual(r["bbox_lat_min"], 26.0)
            self.assertLessEqual(r["bbox_lat_max"], 36.0)

    def test_no_duplicate_names(self):
        names = [r["district"] for r in self.result["records"]]
        self.assertEqual(len(names), len(set(names)))

    def test_known_missing_districts(self):
        missing = set(self.result["coverage"]["missing_in_geojson"])
        self.assertEqual(
            missing,
            {"Bhakkar District", "Jhang District", "Layyah District",
             "Muzaffargarh District", "Okara District"},
        )

    def test_known_extra_districts(self):
        extras = set(self.result["coverage"]["extra_in_geojson"])
        self.assertEqual(extras, {"Chiniot", "Nankana Sahib"})

    def test_no_warnings(self):
        self.assertEqual(self.result["warnings"], [])


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

    def test_wrong_type(self):
        p = self._write("x.geojson", {"type": "Feature", "features": []})
        with self.assertRaises(BoundaryValidationError):
            validate(p, MASTER)

    def test_missing_district_property(self):
        p = self._write(
            "x.geojson",
            {
                "type": "FeatureCollection",
                "crs": {"type": "name", "properties": {"name": "EPSG:4326"}},
                "features": [
                    {
                        "type": "Feature",
                        "properties": {},
                        "geometry": {"type": "Polygon", "coordinates": [[[0, 0], [1, 0], [1, 1], [0, 0]]]},
                    }
                ],
            },
        )
        with self.assertRaises(BoundaryValidationError):
            validate(p, MASTER)

    def test_unsupported_geometry_type(self):
        p = self._write(
            "x.geojson",
            {
                "type": "FeatureCollection",
                "crs": {"type": "name", "properties": {"name": "EPSG:4326"}},
                "features": [
                    {
                        "type": "Feature",
                        "properties": {"DISTRICT": "Foo"},
                        "geometry": {"type": "Point", "coordinates": [72, 31]},
                    }
                ],
            },
        )
        with self.assertRaises(BoundaryValidationError):
            validate(p, MASTER)

    def test_duplicate_names_rejected(self):
        p = self._write(
            "x.geojson",
            {
                "type": "FeatureCollection",
                "crs": {"type": "name", "properties": {"name": "EPSG:4326"}},
                "features": [
                    {
                        "type": "Feature",
                        "properties": {"DISTRICT": "Lahore"},
                        "geometry": {"type": "Polygon", "coordinates": [[[0, 0], [1, 0], [1, 1], [0, 0]]]},
                    },
                    {
                        "type": "Feature",
                        "properties": {"DISTRICT": "Lahore"},
                        "geometry": {"type": "Polygon", "coordinates": [[[2, 2], [3, 2], [3, 3], [2, 2]]]},
                    },
                ],
            },
        )
        with self.assertRaises(BoundaryValidationError):
            validate(p, MASTER)


if __name__ == "__main__":
    unittest.main()
