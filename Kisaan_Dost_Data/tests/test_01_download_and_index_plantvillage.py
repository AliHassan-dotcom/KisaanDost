"""Tests for 01_download_and_index_plantvillage.py — PlantVillage Step 1.

Covers:
- parse_class_name: crop/disease/healthy extraction
- Manifest shape: row count, columns, deterministic order
- Data quality: no corrupt, all RGB, all 256x256
- Class distribution: 15 classes, 3 crops
- No duplicate image paths
- Healthy class identification
"""

import csv
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
MANIFEST_PATH = ROOT / "data" / "raw" / "plantvillage_manifest.csv"
REPORT_PATH = ROOT / "reports" / "plantvillage_dataset_report.md"
SCRIPT_DIR = ROOT / "scripts"


def load_manifest():
    with MANIFEST_PATH.open("r", encoding="utf-8", newline="") as fh:
        return list(csv.DictReader(fh))


class TestParseClassName(unittest.TestCase):
    def setUp(self):
        import importlib.util
        spec = importlib.util.spec_from_file_location(
            "pv_script",
            SCRIPT_DIR / "01_download_and_index_plantvillage.py",
        )
        self.mod = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(self.mod)
        self.parse = self.mod.parse_class_name

    def test_pepper_bell_bacterial_spot(self):
        crop, disease, healthy = self.parse("Pepper__bell___Bacterial_spot")
        self.assertEqual(crop, "Pepper bell")
        self.assertEqual(disease, "Bacterial spot")
        self.assertFalse(healthy)

    def test_pepper_healthy(self):
        crop, disease, healthy = self.parse("Pepper__bell___healthy")
        self.assertEqual(crop, "Pepper bell")
        self.assertEqual(disease, "healthy")
        self.assertTrue(healthy)

    def test_potato_early_blight(self):
        crop, disease, healthy = self.parse("Potato___Early_blight")
        self.assertEqual(crop, "Potato")
        self.assertEqual(disease, "Early blight")
        self.assertFalse(healthy)

    def test_potato_healthy(self):
        crop, disease, healthy = self.parse("Potato___healthy")
        self.assertEqual(crop, "Potato")
        self.assertEqual(disease, "healthy")
        self.assertTrue(healthy)

    def test_tomato_single_underscore(self):
        crop, disease, healthy = self.parse("Tomato_Bacterial_spot")
        self.assertEqual(crop, "Tomato")
        self.assertEqual(disease, "Bacterial spot")
        self.assertFalse(healthy)

    def test_tomato_double_underscore(self):
        crop, disease, healthy = self.parse("Tomato__Target_Spot")
        self.assertEqual(crop, "Tomato")
        self.assertEqual(disease, "Target Spot")
        self.assertFalse(healthy)

    def test_tomato_yellow_leaf_curl_virus(self):
        crop, disease, healthy = self.parse("Tomato__Tomato_YellowLeaf__Curl_Virus")
        self.assertEqual(crop, "Tomato")
        self.assertIn("YellowLeaf", disease)
        self.assertIn("Curl Virus", disease)
        self.assertFalse(healthy)

    def test_tomato_healthy(self):
        crop, disease, healthy = self.parse("Tomato_healthy")
        self.assertEqual(crop, "Tomato")
        self.assertEqual(disease, "healthy")
        self.assertTrue(healthy)

    def test_spider_mites(self):
        crop, disease, healthy = self.parse(
            "Tomato_Spider_mites_Two_spotted_spider_mite"
        )
        self.assertEqual(crop, "Tomato")
        self.assertEqual(disease, "Spider mites Two spotted spider mite")
        self.assertFalse(healthy)


class TestManifestShape(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.rows = load_manifest()

    def test_row_count(self):
        self.assertEqual(len(self.rows), 20638)

    def test_columns(self):
        expected = [
            "image_path",
            "label",
            "class_name",
            "source_dataset",
            "crop",
            "disease",
            "is_healthy",
            "split",
            "width",
            "height",
            "channels",
            "is_corrupt",
        ]
        self.assertEqual(list(self.rows[0].keys()), expected)

    def test_no_duplicate_paths(self):
        paths = [r["image_path"] for r in self.rows]
        self.assertEqual(len(paths), len(set(paths)))

    def test_all_clean(self):
        corrupt = [r for r in self.rows if r["is_corrupt"] != "False"]
        self.assertEqual(len(corrupt), 0)

    def test_deterministic_order(self):
        labels = [r["class_name"] for r in self.rows]
        self.assertEqual(labels, sorted(labels))


class TestDataQuality(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.rows = load_manifest()

    def test_source_dataset(self):
        sources = {r["source_dataset"] for r in self.rows}
        self.assertEqual(sources, {"PlantVillage"})

    def test_all_rgb(self):
        channels = {r["channels"] for r in self.rows}
        self.assertEqual(channels, {"3"})

    def test_all_256x256(self):
        sizes = {(r["width"], r["height"]) for r in self.rows}
        self.assertEqual(sizes, {("256", "256")})

    def test_no_grayscale(self):
        grayscale = [r for r in self.rows if r["channels"] == "1"]
        self.assertEqual(len(grayscale), 0)


class TestClassDistribution(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.rows = load_manifest()
        from collections import Counter
        cls.class_counts = Counter(r["class_name"] for r in cls.rows)
        cls.crop_counts = Counter(r["crop"] for r in cls.rows)

    def test_num_classes(self):
        self.assertEqual(len(self.class_counts), 15)

    def test_num_crops(self):
        self.assertEqual(len(self.crop_counts), 3)
        self.assertIn("Tomato", self.crop_counts)
        self.assertIn("Potato", self.crop_counts)
        self.assertIn("Pepper bell", self.crop_counts)

    def test_healthy_classes_exist(self):
        healthy_rows = [r for r in self.rows if r["is_healthy"] == "True"]
        healthy_classes = {r["class_name"] for r in healthy_rows}
        self.assertEqual(len(healthy_classes), 3)
        for cls in healthy_classes:
            self.assertTrue(cls.endswith("healthy"))

    def test_all_classes_nonempty(self):
        for cls, count in self.class_counts.items():
            self.assertGreater(count, 0, f"empty class: {cls}")

    def test_split_column_empty(self):
        splits = {r["split"] for r in self.rows}
        self.assertEqual(splits, {""})


class TestReportExists(unittest.TestCase):
    def test_report_file_exists(self):
        self.assertTrue(REPORT_PATH.exists())

    def test_report_has_content(self):
        content = REPORT_PATH.read_text(encoding="utf-8")
        self.assertIn("PlantVillage", content)
        self.assertIn("20638", content)
        self.assertIn("15", content)


if __name__ == "__main__":
    unittest.main()
