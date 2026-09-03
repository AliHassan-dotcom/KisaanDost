"""Tests for Step 2: clean manifest + class mapping + split.

Covers:
- Row count preserved from raw manifest
- No duplicate rows
- No missing values in required columns
- Stratified split distribution (70/15/15 ± tolerance)
- Per-class split ratios within tolerance
- Class mapping table shape and consistency
- Source dataset preserved
- Split seed recorded
- Deterministic reproducibility
- Class balance preserved across splits

Stdlib only.
"""

from __future__ import annotations

import csv
from collections import Counter, defaultdict
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent.parent
CLEAN_PATH = ROOT / "data" / "processed" / "plantvillage_manifest_clean.csv"
MAPPING_PATH = ROOT / "data" / "processed" / "plantvillage_class_mapping.csv"
RAW_PATH = ROOT / "data" / "raw" / "plantvillage_manifest.csv"
REPORT_PATH = ROOT / "reports" / "plantvillage_clean_manifest_report.md"

EXPECTED_COLUMNS = [
    "image_path", "label", "class_name", "crop", "disease",
    "is_healthy", "source_dataset", "split", "split_seed",
]

SEED = 42
TRAIN_TARGET = 0.70
VAL_TARGET = 0.15
TEST_TARGET = 0.15
RATIO_TOLERANCE = 0.05  # allow ±5 percentage points per class


@pytest.fixture(scope="module")
def clean_rows() -> list[dict[str, str]]:
    with CLEAN_PATH.open("r", encoding="utf-8", newline="") as fh:
        return list(csv.DictReader(fh))


@pytest.fixture(scope="module")
def raw_rows() -> list[dict[str, str]]:
    with RAW_PATH.open("r", encoding="utf-8", newline="") as fh:
        return list(csv.DictReader(fh))


@pytest.fixture(scope="module")
def mapping_rows() -> list[dict[str, str]]:
    with MAPPING_PATH.open("r", encoding="utf-8", newline="") as fh:
        return list(csv.DictReader(fh))


class TestRowCount:
    def test_row_count_matches_raw(self, raw_rows, clean_rows):
        assert len(clean_rows) == len(raw_rows)

    def test_row_count_exact(self, clean_rows):
        assert len(clean_rows) == 20638


class TestNoDuplicates:
    def test_no_duplicate_image_paths(self, clean_rows):
        paths = [r["image_path"] for r in clean_rows]
        assert len(paths) == len(set(paths))

    def test_no_duplicate_rows(self, clean_rows):
        tuples = [tuple(r[c] for c in EXPECTED_COLUMNS) for r in clean_rows]
        assert len(tuples) == len(set(tuples))


class TestColumns:
    def test_columns_match_spec(self, clean_rows):
        assert list(clean_rows[0].keys()) == EXPECTED_COLUMNS

    def test_no_missing_values(self, clean_rows):
        for col in EXPECTED_COLUMNS:
            empty = sum(1 for r in clean_rows if not r.get(col, "").strip())
            assert empty == 0, f"Column {col} has {empty} empty values"


class TestSourceDataset:
    def test_all_plantvillage(self, clean_rows):
        sources = set(r["source_dataset"] for r in clean_rows)
        assert sources == {"PlantVillage"}

    def test_split_seed_recorded(self, clean_rows):
        seeds = set(r["split_seed"] for r in clean_rows)
        assert seeds == {str(SEED)}


class TestSplitDistribution:
    def test_global_split_counts(self, clean_rows):
        counts = Counter(r["split"] for r in clean_rows)
        total = len(clean_rows)
        assert set(counts.keys()) == {"train", "val", "test"}
        assert abs(counts["train"] / total - TRAIN_TARGET) < 0.02
        assert abs(counts["val"] / total - VAL_TARGET) < 0.02
        assert abs(counts["test"] / total - TEST_TARGET) < 0.02

    def test_splits_sum_to_total(self, clean_rows):
        counts = Counter(r["split"] for r in clean_rows)
        assert sum(counts.values()) == len(clean_rows)

    def test_per_class_split_ratios(self, clean_rows):
        """Each class should have roughly 70/15/15 split within tolerance."""
        class_groups: dict[str, list[str]] = defaultdict(list)
        for r in clean_rows:
            class_groups[r["class_name"]].append(r["split"])

        for cls, splits in class_groups.items():
            n = len(splits)
            counts = Counter(splits)
            train_ratio = counts["train"] / n
            val_ratio = counts["val"] / n
            test_ratio = counts["test"] / n

            assert abs(train_ratio - TRAIN_TARGET) < RATIO_TOLERANCE, (
                f"{cls}: train ratio {train_ratio:.2f} outside tolerance"
            )
            assert abs(val_ratio - VAL_TARGET) < RATIO_TOLERANCE, (
                f"{cls}: val ratio {val_ratio:.2f} outside tolerance"
            )
            assert abs(test_ratio - TEST_TARGET) < RATIO_TOLERANCE, (
                f"{cls}: test ratio {test_ratio:.2f} outside tolerance"
            )

    def test_every_class_has_all_splits(self, clean_rows):
        class_splits: dict[str, set[str]] = defaultdict(set)
        for r in clean_rows:
            class_splits[r["class_name"]].add(r["split"])

        for cls, splits in class_splits.items():
            assert splits == {"train", "val", "test"}, (
                f"{cls} missing splits: {splits}"
            )


class TestClassBalance:
    def test_class_counts_preserved(self, raw_rows, clean_rows):
        raw_counts = Counter(r["class_name"] for r in raw_rows)
        clean_counts = Counter(r["class_name"] for r in clean_rows)
        assert dict(raw_counts) == dict(clean_counts)

    def test_all_15_classes_present(self, clean_rows):
        classes = set(r["class_name"] for r in clean_rows)
        assert len(classes) == 15

    def test_all_3_crops_present(self, clean_rows):
        crops = set(r["crop"] for r in clean_rows)
        assert len(crops) == 3


class TestClassMapping:
    def test_mapping_row_count(self, mapping_rows):
        assert len(mapping_rows) == 15

    def test_mapping_columns(self, mapping_rows):
        expected = [
            "class_id", "class_name", "crop", "disease", "is_healthy",
            "num_images", "num_train", "num_val", "num_test",
        ]
        assert list(mapping_rows[0].keys()) == expected

    def test_class_ids_sequential(self, mapping_rows):
        ids = [int(r["class_id"]) for r in mapping_rows]
        assert ids == list(range(15))

    def test_class_names_unique(self, mapping_rows):
        names = [r["class_name"] for r in mapping_rows]
        assert len(names) == len(set(names))

    def test_split_counts_sum_to_total(self, mapping_rows):
        for row in mapping_rows:
            total = int(row["num_images"])
            split_sum = (
                int(row["num_train"])
                + int(row["num_val"])
                + int(row["num_test"])
            )
            assert split_sum == total, (
                f"{row['class_name']}: {split_sum} != {total}"
            )

    def test_total_images_sum(self, mapping_rows):
        total = sum(int(r["num_images"]) for r in mapping_rows)
        assert total == 20638


class TestDeterministic:
    def test_reproducible_split(self, clean_rows):
        """Re-running stratified_split with same seed produces same result."""
        import importlib.util

        script_path = ROOT / "scripts" / "02_clean_manifest_and_split.py"
        spec = importlib.util.spec_from_file_location("step02", script_path)
        mod = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(mod)

        raw = mod.load_raw_manifest(RAW_PATH)
        re_split = mod.stratified_split(raw)

        for orig, rerun in zip(clean_rows, re_split):
            assert orig["image_path"] == rerun["image_path"]
            assert orig["split"] == rerun["split"]


class TestReportExists:
    def test_report_file_exists(self):
        assert REPORT_PATH.exists()

    def test_report_has_content(self):
        content = REPORT_PATH.read_text(encoding="utf-8")
        assert "PlantVillage Clean Manifest Report" in content
        assert "Split Distribution" in content
        assert "Per-Class Split Distribution" in content
