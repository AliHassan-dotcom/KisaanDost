"""Tests for the unified crop-disease manifest builder.

Covers:
- Source registry schema validation
- Image-root resolver behavior
- Manifest column schema and deterministic ordering
- MD5 hashing presence and non-empty values
- Corrupt-image handling
- Label-mapping coverage and is_healthy rules
- Source inventory counts
- Duplicate detection without silent deletion
- Report completeness and unmatched-class reporting

Tests do not require successful execution of all downloads; they pass even if
one or more datasets are skipped.

Stdlib + Pillow only.
"""

from __future__ import annotations

import csv
import importlib.util
import tempfile
from pathlib import Path
from typing import List

import pytest

ROOT = Path(__file__).resolve().parent.parent


@pytest.fixture(scope="module")
def unified_mod():
    script = ROOT / "scripts" / "01_build_unified_manifest.py"
    spec = importlib.util.spec_from_file_location("unified_module", script)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


# ── Module loading ──────────────────────────────────────────────────


class TestModuleLoads:
    def test_module_imports(self, unified_mod):
        assert unified_mod is not None

    def test_has_run(self, unified_mod):
        assert callable(getattr(unified_mod, "run", None))

    def test_has_scan_source(self, unified_mod):
        assert callable(getattr(unified_mod, "scan_source", None))

    def test_has_compute_md5(self, unified_mod):
        assert callable(getattr(unified_mod, "compute_md5", None))

    def test_has_find_duplicate_hashes(self, unified_mod):
        assert callable(getattr(unified_mod, "find_duplicate_hashes", None))

    def test_has_build_label_mapping(self, unified_mod):
        assert callable(getattr(unified_mod, "build_label_mapping", None))

    def test_has_canonical_label(self, unified_mod):
        assert callable(getattr(unified_mod, "canonical_label", None))

    def test_has_find_image_root(self, unified_mod):
        assert callable(getattr(unified_mod, "find_image_root", None))

    def test_has_write_manifest(self, unified_mod):
        assert callable(getattr(unified_mod, "write_manifest", None))

    def test_has_write_report(self, unified_mod):
        assert callable(getattr(unified_mod, "write_report", None))


# ── Source registry schema ──────────────────────────────────────────


class TestSourceRegistry:
    def test_registry_is_list(self, unified_mod):
        assert isinstance(unified_mod.SOURCE_REGISTRY, list)

    def test_registry_has_six_entries(self, unified_mod):
        assert len(unified_mod.SOURCE_REGISTRY) == 6

    def test_registry_entry_schema(self, unified_mod):
        required_keys = {"source_dataset", "kaggle_slug", "expected_crops", "notes"}
        for entry in unified_mod.SOURCE_REGISTRY:
            assert isinstance(entry, dict)
            assert required_keys.issubset(entry.keys())
            assert isinstance(entry["expected_crops"], list)
            assert len(entry["expected_crops"]) > 0

    def test_plantvillage_present(self, unified_mod):
        names = [e["source_dataset"] for e in unified_mod.SOURCE_REGISTRY]
        assert "PlantVillage" in names

    def test_all_slugs_unique(self, unified_mod):
        slugs = [e["kaggle_slug"] for e in unified_mod.SOURCE_REGISTRY]
        assert len(slugs) == len(set(slugs))


# ── Column schemas ──────────────────────────────────────────────────


class TestColumnSchemas:
    def test_manifest_columns(self, unified_mod):
        expected = [
            "image_path", "source_dataset", "source_class_name", "crop",
            "disease", "canonical_label", "is_healthy", "width", "height",
            "channels", "is_corrupt", "hash_md5",
        ]
        assert unified_mod.MANIFEST_COLUMNS == expected

    def test_inventory_columns(self, unified_mod):
        expected = [
            "source_dataset", "download_path", "detected_root", "total_images",
            "valid_images", "corrupt_images", "num_classes", "notes",
        ]
        assert unified_mod.INVENTORY_COLUMNS == expected

    def test_mapping_columns(self, unified_mod):
        expected = [
            "source_dataset", "source_class_name", "crop", "disease",
            "canonical_label", "is_healthy",
        ]
        assert unified_mod.MAPPING_COLUMNS == expected


# ── Image-root resolver ─────────────────────────────────────────────


class TestFindImageRoot:
    def test_single_child_traversal(self, unified_mod, tmp_path):
        """find_image_root walks into single-child directories."""
        level1 = tmp_path / "level1"
        level2 = level1 / "level2"
        level2.mkdir(parents=True)
        (level2 / "classA").mkdir()
        (level2 / "classB").mkdir()
        root = unified_mod.find_image_root(tmp_path)
        assert root == level2

    def test_nested_duplicate_skip(self, unified_mod, tmp_path):
        """find_image_root skips nested duplicate with same-named subfolder."""
        outer = tmp_path / "PlantVillage"
        outer.mkdir()
        (outer / "classA").mkdir()
        (outer / "classB").mkdir()
        inner = outer / "PlantVillage"
        inner.mkdir()
        (inner / "classA").mkdir()
        (inner / "classB").mkdir()
        root = unified_mod.find_image_root(tmp_path)
        assert root == outer

    def test_no_nesting(self, unified_mod, tmp_path):
        """find_image_root returns the directory itself when no single-child chain."""
        (tmp_path / "classA").mkdir()
        (tmp_path / "classB").mkdir()
        root = unified_mod.find_image_root(tmp_path)
        assert root == tmp_path


# ── MD5 hashing ─────────────────────────────────────────────────────


class TestComputeMD5:
    def test_md5_returns_hex_string(self, unified_mod, tmp_path):
        test_file = tmp_path / "test.txt"
        test_file.write_text("hello world", encoding="utf-8")
        result = unified_mod.compute_md5(test_file)
        assert isinstance(result, str)
        assert len(result) == 32
        assert all(c in "0123456789abcdef" for c in result)

    def test_md5_deterministic(self, unified_mod, tmp_path):
        test_file = tmp_path / "test.txt"
        test_file.write_text("test content", encoding="utf-8")
        hash1 = unified_mod.compute_md5(test_file)
        hash2 = unified_mod.compute_md5(test_file)
        assert hash1 == hash2

    def test_md5_changes_with_content(self, unified_mod, tmp_path):
        file1 = tmp_path / "file1.txt"
        file2 = tmp_path / "file2.txt"
        file1.write_text("content A", encoding="utf-8")
        file2.write_text("content B", encoding="utf-8")
        assert unified_mod.compute_md5(file1) != unified_mod.compute_md5(file2)


# ── Duplicate detection ─────────────────────────────────────────────


class TestFindDuplicateHashes:
    def test_no_duplicates(self, unified_mod):
        records = [
            {"hash_md5": "abc123", "image_path": "/a.jpg"},
            {"hash_md5": "def456", "image_path": "/b.jpg"},
        ]
        result = unified_mod.find_duplicate_hashes(records)
        assert result == []

    def test_detects_duplicates(self, unified_mod):
        records = [
            {"hash_md5": "abc123", "image_path": "/a.jpg"},
            {"hash_md5": "abc123", "image_path": "/b.jpg"},
            {"hash_md5": "def456", "image_path": "/c.jpg"},
        ]
        result = unified_mod.find_duplicate_hashes(records)
        assert len(result) == 1
        assert result[0]["hash_md5"] == "abc123"
        assert result[0]["count"] == 2
        assert len(result[0]["paths"]) == 2

    def test_skips_empty_hashes(self, unified_mod):
        records = [
            {"hash_md5": "", "image_path": "/a.jpg"},
            {"hash_md5": "", "image_path": "/b.jpg"},
        ]
        result = unified_mod.find_duplicate_hashes(records)
        assert result == []

    def test_multiple_duplicate_clusters(self, unified_mod):
        records = [
            {"hash_md5": "aaa", "image_path": "/a1.jpg"},
            {"hash_md5": "aaa", "image_path": "/a2.jpg"},
            {"hash_md5": "bbb", "image_path": "/b1.jpg"},
            {"hash_md5": "bbb", "image_path": "/b2.jpg"},
        ]
        result = unified_mod.find_duplicate_hashes(records)
        assert len(result) == 2


# ── Label mapping ───────────────────────────────────────────────────


class TestBuildLabelMapping:
    def test_one_row_per_source_class(self, unified_mod):
        records = [
            {
                "source_dataset": "PlantVillage",
                "source_class_name": "Tomato_Bacterial_spot",
                "crop": "Tomato",
                "disease": "Bacterial spot",
                "canonical_label": "Tomato__Bacterial spot",
                "is_healthy": "False",
            },
            {
                "source_dataset": "PlantVillage",
                "source_class_name": "Tomato_Bacterial_spot",
                "crop": "Tomato",
                "disease": "Bacterial spot",
                "canonical_label": "Tomato__Bacterial spot",
                "is_healthy": "False",
            },
        ]
        mapping = unified_mod.build_label_mapping(records)
        assert len(mapping) == 1

    def test_preserves_source_order(self, unified_mod):
        records = [
            {
                "source_dataset": "PlantVillage",
                "source_class_name": "ClassA",
                "crop": "CropA",
                "disease": "DiseaseA",
                "canonical_label": "CropA__DiseaseA",
                "is_healthy": "False",
            },
            {
                "source_dataset": "PlantVillage",
                "source_class_name": "ClassB",
                "crop": "CropB",
                "disease": "DiseaseB",
                "canonical_label": "CropB__DiseaseB",
                "is_healthy": "False",
            },
        ]
        mapping = unified_mod.build_label_mapping(records)
        assert mapping[0]["source_class_name"] == "ClassA"
        assert mapping[1]["source_class_name"] == "ClassB"

    def test_healthy_flag(self, unified_mod):
        records = [
            {
                "source_dataset": "PlantVillage",
                "source_class_name": "Tomato_healthy",
                "crop": "Tomato",
                "disease": "healthy",
                "canonical_label": "Tomato__healthy",
                "is_healthy": "True",
            },
        ]
        mapping = unified_mod.build_label_mapping(records)
        assert mapping[0]["is_healthy"] == "True"


# ── Canonical label ─────────────────────────────────────────────────


class TestCanonicalLabel:
    def test_healthy_label(self, unified_mod):
        result = unified_mod.canonical_label("Tomato", "healthy", True)
        assert result == "Tomato__healthy"

    def test_disease_label(self, unified_mod):
        result = unified_mod.canonical_label("Tomato", "Bacterial spot", False)
        assert result == "Tomato__Bacterial spot"

    def test_no_disease(self, unified_mod):
        result = unified_mod.canonical_label("Tomato", "", False)
        assert result == "Tomato"


# ── Source inventory ─────────────────────────────────────────────────


class TestBuildSourceInventory:
    def test_inventory_counts(self, unified_mod):
        records = [
            {"is_corrupt": "False", "source_class_name": "ClassA"},
            {"is_corrupt": "False", "source_class_name": "ClassA"},
            {"is_corrupt": "corrupt reason", "source_class_name": "ClassB"},
        ]
        inv = unified_mod.build_source_inventory(
            "TestSource", Path("/tmp"), Path("/tmp/root"), records, "test notes", "ok"
        )
        assert inv["total_images"] == 3
        assert inv["valid_images"] == 2
        assert inv["corrupt_images"] == 1
        assert inv["num_classes"] == 2

    def test_inventory_skipped_status(self, unified_mod):
        inv = unified_mod.build_source_inventory(
            "SkippedSource", None, None, [], "private dataset", "skipped"
        )
        assert "skipped" in inv["notes"]
        assert inv["total_images"] == 0


# ── Manifest writing ────────────────────────────────────────────────


class TestWriteManifest:
    def test_write_manifest_creates_file(self, unified_mod, tmp_path):
        records = [
            {
                "image_path": "/test.jpg",
                "source_dataset": "Test",
                "source_class_name": "TestClass",
                "crop": "TestCrop",
                "disease": "TestDisease",
                "canonical_label": "TestCrop__TestDisease",
                "is_healthy": "False",
                "width": "100",
                "height": "100",
                "channels": "3",
                "is_corrupt": "False",
                "hash_md5": "abc123",
            },
        ]
        manifest_path = tmp_path / "manifest.csv"
        unified_mod.write_manifest(records, manifest_path)
        assert manifest_path.exists()

    def test_manifest_csv_schema(self, unified_mod, tmp_path):
        records = [
            {
                "image_path": "/test.jpg",
                "source_dataset": "Test",
                "source_class_name": "TestClass",
                "crop": "TestCrop",
                "disease": "TestDisease",
                "canonical_label": "TestCrop__TestDisease",
                "is_healthy": "False",
                "width": "100",
                "height": "100",
                "channels": "3",
                "is_corrupt": "False",
                "hash_md5": "abc123",
            },
        ]
        manifest_path = tmp_path / "manifest.csv"
        unified_mod.write_manifest(records, manifest_path)
        with manifest_path.open("r", encoding="utf-8", newline="") as fh:
            reader = csv.DictReader(fh)
            rows = list(reader)
            assert len(rows) == 1
            assert set(rows[0].keys()) == set(unified_mod.MANIFEST_COLUMNS)


# ── Report writing ──────────────────────────────────────────────────


class TestWriteReport:
    def test_report_has_required_sections(self, unified_mod, tmp_path):
        context = {
            "total_datasets_scanned": 6,
            "total_images_found": 1000,
            "total_valid_images": 950,
            "total_corrupt_images": 50,
            "total_duplicate_hashes": 5,
            "crops_covered": ["Tomato", "Potato"],
            "canonical_labels": ["Tomato__healthy", "Potato__Late blight"],
            "label_mapping_coverage": 15,
            "per_dataset_classes": {"PlantVillage": ["ClassA", "ClassB"]},
            "folder_trees": {"PlantVillage": {"ClassA": [], "ClassB": []}},
            "unmatched_source_classes": [],
            "duplicates": [],
        }
        report_path = tmp_path / "report.md"
        unified_mod.write_report(context, report_path)
        text = report_path.read_text(encoding="utf-8")
        assert "## Summary" in text
        assert "## Per-Dataset Class Counts" in text
        assert "## Crops Covered" in text
        assert "## Canonical Labels" in text
        assert "## Folder Structure Summary" in text
        assert "## Duplicate Hashes" in text
        assert "## Unmatched Source Classes" in text

    def test_report_unmatched_classes(self, unified_mod, tmp_path):
        context = {
            "total_datasets_scanned": 1,
            "total_images_found": 10,
            "total_valid_images": 10,
            "total_corrupt_images": 0,
            "total_duplicate_hashes": 0,
            "crops_covered": [],
            "canonical_labels": [],
            "label_mapping_coverage": 0,
            "per_dataset_classes": {},
            "folder_trees": {},
            "unmatched_source_classes": ["UnknownClass"],
            "duplicates": [],
        }
        report_path = tmp_path / "report.md"
        unified_mod.write_report(context, report_path)
        text = report_path.read_text(encoding="utf-8")
        assert "UnknownClass" in text


# ── Classify folder helper ──────────────────────────────────────────


class TestClassifyFolder:
    def test_healthy_detection(self, unified_mod, tmp_path):
        crop, disease, is_healthy = unified_mod._classify_folder(tmp_path, "Tomato_healthy")
        assert crop == "Tomato"
        assert disease == "healthy"
        assert is_healthy is True

    def test_disease_parsing(self, unified_mod, tmp_path):
        crop, disease, is_healthy = unified_mod._classify_folder(
            tmp_path, "Tomato_Bacterial_spot"
        )
        assert crop == "Tomato"
        assert disease == "Bacterial Spot"
        assert is_healthy is False

    def test_single_token(self, unified_mod, tmp_path):
        crop, disease, is_healthy = unified_mod._classify_folder(tmp_path, "Healthy")
        assert crop == "Healthy"
        assert disease == ""
        assert is_healthy is True


# ── Integration test with synthetic data ────────────────────────────


class TestScanSource:
    def test_scan_source_empty_directory(self, unified_mod, tmp_path):
        """scan_source handles empty directory gracefully."""
        records, tree = unified_mod.scan_source("TestSource", tmp_path)
        assert isinstance(records, list)
        assert isinstance(tree, dict)

    def test_scan_source_with_class_folders(self, unified_mod, tmp_path):
        """scan_source processes class folders correctly."""
        class_dir = tmp_path / "Tomato_healthy"
        class_dir.mkdir()
        # Create a minimal valid PNG
        from PIL import Image
        img = Image.new("RGB", (10, 10), color="red")
        img.save(class_dir / "img1.png")
        
        records, tree = unified_mod.scan_source("TestSource", tmp_path)
        assert len(records) == 1
        assert records[0]["source_dataset"] == "TestSource"
        assert records[0]["source_class_name"] == "Tomato_healthy"
        assert records[0]["crop"] == "Tomato"
        assert records[0]["disease"] == "healthy"
        assert records[0]["is_healthy"] == "True"
        assert records[0]["hash_md5"] != ""
        assert records[0]["is_corrupt"] == "False"

    def test_scan_source_corrupt_image(self, unified_mod, tmp_path):
        """scan_source flags corrupt images."""
        class_dir = tmp_path / "TestClass"
        class_dir.mkdir()
        corrupt_file = class_dir / "corrupt.jpg"
        corrupt_file.write_text("not an image", encoding="utf-8")
        
        records, tree = unified_mod.scan_source("TestSource", tmp_path)
        assert len(records) == 1
        assert records[0]["is_corrupt"] != "False"
        assert records[0]["hash_md5"] == ""
