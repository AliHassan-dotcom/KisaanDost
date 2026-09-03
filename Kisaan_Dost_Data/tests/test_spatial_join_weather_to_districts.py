"""Tests for spatial_join_weather_to_districts.py.

Tests cover:
- Ray-casting PIP algorithm (synthetic polygons)
- Haversine distance calculation
- Grid-point → district mapping logic
- Polygon vs fallback assignment
- Output CSV structure and validation
- Real-file integration (if input files exist)
"""

from __future__ import annotations

import csv
import math
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "scripts"))

from spatial_join_weather_to_districts import (
    EARTH_RADIUS_KM,
    OUTPUT_COLUMNS,
    build_grid_mapping,
    extract_grid_points,
    haversine_km,
    identify_fallback_districts,
    load_district_centroids,
    load_polygons,
    point_in_geometry,
    point_in_polygon,
    validate_join_keys,
)

HAS_INPUT_FILES = (
    (ROOT / "raw" / "arcgis" / "punjab_district_boundaries.geojson").exists()
    and (ROOT / "processed" / "district_coordinates.csv").exists()
    and (ROOT / "Historical Data").exists()
)


class TestPointInPolygon(unittest.TestCase):
    """Ray-casting PIP with synthetic polygons."""

    def test_square_inside(self):
        square = [(0, 0), (10, 0), (10, 10), (0, 10)]
        self.assertTrue(point_in_polygon(5, 5, square))

    def test_square_outside(self):
        square = [(0, 0), (10, 0), (10, 10), (0, 10)]
        self.assertFalse(point_in_polygon(15, 5, square))

    def test_square_on_edge(self):
        square = [(0, 0), (10, 0), (10, 10), (0, 10)]
        result = point_in_polygon(5, 0, square)
        self.assertIsInstance(result, bool)

    def test_triangle_inside(self):
        tri = [(0, 0), (10, 0), (5, 10)]
        self.assertTrue(point_in_polygon(5, 3, tri))

    def test_triangle_outside(self):
        tri = [(0, 0), (10, 0), (5, 10)]
        self.assertFalse(point_in_polygon(1, 8, tri))

    def test_concave_polygon(self):
        concave = [(0, 0), (10, 0), (10, 10), (5, 5), (0, 10)]
        self.assertTrue(point_in_polygon(2, 2, concave))
        self.assertFalse(point_in_polygon(5, 7, concave))


class TestPointInGeometry(unittest.TestCase):
    """MultiPolygon and Polygon geometry handling."""

    def test_polygon_geometry(self):
        geom = {
            "type": "Polygon",
            "coordinates": [[[0, 0], [10, 0], [10, 10], [0, 10], [0, 0]]],
        }
        self.assertTrue(point_in_geometry(5, 5, geom))
        self.assertFalse(point_in_geometry(15, 5, geom))

    def test_multipolygon_geometry(self):
        geom = {
            "type": "MultiPolygon",
            "coordinates": [
                [[[0, 0], [5, 0], [5, 5], [0, 5], [0, 0]]],
                [[[20, 20], [25, 20], [25, 25], [20, 25], [20, 20]]],
            ],
        }
        self.assertTrue(point_in_geometry(2, 2, geom))
        self.assertTrue(point_in_geometry(22, 22, geom))
        self.assertFalse(point_in_geometry(10, 10, geom))

    def test_unknown_geometry(self):
        geom = {"type": "LineString", "coordinates": [[0, 0], [1, 1]]}
        self.assertFalse(point_in_geometry(0.5, 0.5, geom))


class TestHaversine(unittest.TestCase):
    """Haversine distance calculation."""

    def test_zero_distance(self):
        self.assertAlmostEqual(haversine_km(31.0, 72.0, 31.0, 72.0), 0.0)

    def test_known_distance(self):
        d = haversine_km(31.5204, 74.3587, 31.4504, 73.1350)
        self.assertGreater(d, 100)
        self.assertLess(d, 130)

    def test_antipodal(self):
        d = haversine_km(0, 0, 0, 180)
        self.assertAlmostEqual(d, math.pi * EARTH_RADIUS_KM, delta=1)

    def test_symmetry(self):
        d1 = haversine_km(30.0, 71.0, 31.0, 72.0)
        d2 = haversine_km(31.0, 72.0, 30.0, 71.0)
        self.assertAlmostEqual(d1, d2, places=10)


@unittest.skipUnless(HAS_INPUT_FILES, "requires input files on disk")
class TestRealDataLoaders(unittest.TestCase):
    """Data loading with real ArcGIS + coordinate files."""

    def test_load_polygons(self):
        polygons = load_polygons()
        self.assertIsInstance(polygons, dict)
        self.assertEqual(len(polygons), 31)
        self.assertIn("Lahore", polygons)
        self.assertIn("Rahim Yar Khan", polygons)

    def test_load_district_centroids(self):
        centroids = load_district_centroids()
        self.assertIsInstance(centroids, dict)
        self.assertEqual(len(centroids), 34)
        self.assertIn("Lahore", centroids)
        self.assertIn("Bhakkar", centroids)

    def test_identify_fallback_districts(self):
        polygons = load_polygons()
        centroids = load_district_centroids()
        fallback = identify_fallback_districts(polygons, centroids)
        self.assertEqual(
            sorted(fallback),
            ["Bhakkar", "Jhang", "Layyah", "Muzaffargarh", "Okara"],
        )


@unittest.skipUnless(HAS_INPUT_FILES, "requires input files on disk")
class TestGridMapping(unittest.TestCase):
    """Grid-point → district mapping with real data."""

    @classmethod
    def setUpClass(cls):
        cls.polygons = load_polygons()
        cls.centroids = load_district_centroids()
        cls.fallback = identify_fallback_districts(cls.polygons, cls.centroids)
        cls.grid_points = extract_grid_points()
        cls.mapping = build_grid_mapping(
            cls.polygons, cls.centroids, cls.fallback, cls.grid_points
        )

    def test_grid_point_count(self):
        self.assertEqual(len(self.grid_points), 117)

    def test_mapping_covers_all_grid_points(self):
        self.assertEqual(len(self.mapping), 117)

    def test_all_mapping_keys_are_tuples(self):
        for key in self.mapping:
            self.assertIsInstance(key, tuple)
            self.assertEqual(len(key), 2)

    def test_polygon_matches_exist(self):
        polygon_count = sum(
            1 for v in self.mapping.values() if v["method"] == "polygon"
        )
        self.assertGreater(polygon_count, 0)

    def test_fallback_matches_exist(self):
        fallback_count = sum(
            1 for v in self.mapping.values() if v["method"] == "nearest_centroid"
        )
        self.assertGreater(fallback_count, 0)

    def test_polygon_matches_have_zero_distance(self):
        for v in self.mapping.values():
            if v["method"] == "polygon":
                self.assertEqual(v["distance_km"], 0.0)
                self.assertEqual(v["is_fallback"], "False")
                self.assertEqual(v["boundary_match_status"], "matched")

    def test_fallback_matches_have_positive_distance(self):
        for v in self.mapping.values():
            if v["method"] == "nearest_centroid":
                self.assertGreater(v["distance_km"], 0.0)
                self.assertEqual(v["is_fallback"], "True")
                self.assertEqual(
                    v["boundary_match_status"], "fallback_nearest_centroid"
                )

    def test_fallback_only_uses_named_districts(self):
        fallback_districts = {
            v["district"]
            for v in self.mapping.values()
            if v["method"] == "nearest_centroid"
        }
        self.assertTrue(fallback_districts.issubset(set(self.fallback)))

    def test_no_unassigned_points(self):
        unassigned = sum(
            1 for v in self.mapping.values() if v["method"] == "none"
        )
        self.assertEqual(unassigned, 0)

    def test_mapping_fields_complete(self):
        required_keys = {
            "district",
            "normalized_district",
            "method",
            "distance_km",
            "is_fallback",
            "boundary_match_status",
        }
        for v in self.mapping.values():
            self.assertEqual(set(v.keys()), required_keys)


@unittest.skipUnless(HAS_INPUT_FILES, "requires input files on disk")
class TestOutputCSV(unittest.TestCase):
    """Output CSV structure and content."""

    @classmethod
    def setUpClass(cls):
        cls.output_path = ROOT / "processed" / "weather_join_keys.csv"
        if not cls.output_path.exists():
            raise unittest.SkipTest("output CSV not yet generated")
        with cls.output_path.open("r", encoding="utf-8", newline="") as fh:
            cls.rows = list(csv.DictReader(fh))

    def test_output_has_rows(self):
        self.assertGreater(len(self.rows), 0)

    def test_output_columns_exact(self):
        self.assertEqual(list(self.rows[0].keys()), OUTPUT_COLUMNS)

    def test_no_duplicate_keys(self):
        stats = validate_join_keys(self.output_path)
        self.assertEqual(stats["duplicate_keys"], 0)

    def test_source_provider_consistent(self):
        providers = {r["source_provider"] for r in self.rows}
        self.assertEqual(providers, {"nasa_power_merra2"})

    def test_methods_are_valid(self):
        methods = {r["method"] for r in self.rows}
        self.assertTrue(methods.issubset({"polygon", "nearest_centroid"}))

    def test_statuses_are_valid(self):
        statuses = {r["boundary_match_status"] for r in self.rows}
        self.assertTrue(
            statuses.issubset({"matched", "fallback_nearest_centroid"})
        )

    def test_grid_coordinates_preserved(self):
        lons = {float(r["grid_lon"]) for r in self.rows}
        lats = {float(r["grid_lat"]) for r in self.rows}
        self.assertEqual(len(lons), 9)
        self.assertEqual(len(lats), 13)

    def test_date_format_iso(self):
        for r in self.rows[:100]:
            parts = r["source_date"].split("-")
            self.assertEqual(len(parts), 3)
            self.assertEqual(len(parts[0]), 4)

    def test_record_count_reasonable(self):
        self.assertGreater(len(self.rows), 500000)
        self.assertLess(len(self.rows), 520000)


if __name__ == "__main__":
    unittest.main()
