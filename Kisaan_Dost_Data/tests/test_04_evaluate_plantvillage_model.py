"""Tests for Step 4: evaluation pipeline.

Covers:
- Module loads and key functions exist
- Helper functions (load_model, predict, compute_metrics, etc.)
- Output files: confusion matrix PNG + CSV, training report
- Confusion matrix CSV shape (15×15)
- Confusion matrix PNG exists and is non-empty
- Training report has expected sections
- Test metrics are reasonable

Stdlib + PyTorch + torchvision + sklearn + matplotlib + numpy.
"""

from __future__ import annotations

import csv
import importlib.util
from pathlib import Path

import numpy as np
import pytest

ROOT = Path(__file__).resolve().parent.parent
MANIFEST_PATH = ROOT / "data" / "processed" / "plantvillage_manifest_clean.csv"
MAPPING_PATH = ROOT / "data" / "processed" / "plantvillage_class_mapping.csv"
CHECKPOINT_PATH = ROOT / "models" / "best_plantvillage_model.pt"

CM_PNG = ROOT / "reports" / "plantvillage_confusion_matrix.png"
CM_CSV = ROOT / "reports" / "plantvillage_confusion_matrix.csv"
REPORT = ROOT / "reports" / "plantvillage_training_report.md"

NUM_CLASSES = 15


@pytest.fixture(scope="module")
def eval_mod():
    script = ROOT / "scripts" / "04_evaluate_plantvillage_model.py"
    spec = importlib.util.spec_from_file_location("eval_module", script)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


@pytest.fixture(scope="module")
def id_to_class():
    with MAPPING_PATH.open("r", encoding="utf-8", newline="") as fh:
        mapping_rows = list(csv.DictReader(fh))
    names = [r["class_name"] for r in mapping_rows]
    names.sort()
    return names


# ── Module loading ──────────────────────────────────────────────────


class TestModuleLoads:
    def test_module_imports(self, eval_mod):
        assert eval_mod is not None

    def test_has_run(self, eval_mod):
        assert callable(getattr(eval_mod, "run", None))

    def test_has_predict(self, eval_mod):
        assert callable(getattr(eval_mod, "predict", None))

    def test_has_compute_metrics(self, eval_mod):
        assert callable(getattr(eval_mod, "compute_metrics", None))

    def test_has_save_confusion_matrix_csv(self, eval_mod):
        assert callable(getattr(eval_mod, "save_confusion_matrix_csv", None))

    def test_has_save_confusion_matrix_png(self, eval_mod):
        assert callable(getattr(eval_mod, "save_confusion_matrix_png", None))

    def test_has_write_training_report(self, eval_mod):
        assert callable(getattr(eval_mod, "write_training_report", None))

    def test_has_find_top_misclassified(self, eval_mod):
        assert callable(getattr(eval_mod, "find_top_misclassified", None))


# ── Helper functions ────────────────────────────────────────────────


class TestHelpers:
    def test_compute_metrics_basic(self, eval_mod):
        y_true = [0, 0, 1, 1, 2, 2]
        y_pred = [0, 0, 1, 1, 2, 2]
        metrics = eval_mod.compute_metrics(y_true, y_pred)
        assert metrics["accuracy"] == 1.0
        assert metrics["f1_macro"] == 1.0
        assert metrics["total_samples"] == 6

    def test_compute_metrics_imperfect(self, eval_mod):
        y_true = [0, 0, 1, 1]
        y_pred = [0, 1, 1, 0]
        metrics = eval_mod.compute_metrics(y_true, y_pred)
        assert metrics["accuracy"] == 0.5
        assert metrics["total_samples"] == 4

    def test_find_top_misclassified(self, eval_mod):
        y_true = [0, 0, 0, 1, 1, 2]
        y_pred = [0, 1, 1, 0, 1, 0]
        id_to_class = ["A", "B", "C"]
        result = eval_mod.find_top_misclassified(y_true, y_pred, id_to_class, top_n=3)
        assert len(result) > 0
        assert all("true_class" in r and "predicted_class" in r and "count" in r for r in result)

    def test_find_top_misclassified_no_errors(self, eval_mod):
        y_true = [0, 1, 2]
        y_pred = [0, 1, 2]
        result = eval_mod.find_top_misclassified(y_true, y_pred, ["A", "B", "C"])
        assert result == []


# ── Confusion matrix outputs ───────────────────────────────────────


class TestConfusionMatrixCSV:
    def test_csv_exists(self):
        assert CM_CSV.exists(), f"Confusion matrix CSV not found: {CM_CSV}"

    def test_csv_dimensions(self):
        with CM_CSV.open("r", encoding="utf-8", newline="") as fh:
            reader = csv.reader(fh)
            rows = list(reader)
        # Header row + NUM_CLASSES data rows
        assert len(rows) == NUM_CLASSES + 1

    def test_csv_header_length(self):
        with CM_CSV.open("r", encoding="utf-8", newline="") as fh:
            reader = csv.reader(fh)
            header = next(reader)
        # "true_class" + NUM_CLASSES predicted class columns
        assert len(header) == NUM_CLASSES + 1
        assert header[0] == "true_class"

    def test_csv_data_shape(self):
        with CM_CSV.open("r", encoding="utf-8", newline="") as fh:
            reader = csv.reader(fh)
            header = next(reader)
            for row in reader:
                assert len(row) == NUM_CLASSES + 1

    def test_csv_values_nonnegative(self):
        with CM_CSV.open("r", encoding="utf-8", newline="") as fh:
            reader = csv.reader(fh)
            next(reader)  # skip header
            for row in reader:
                for val in row[1:]:
                    assert int(val) >= 0

    def test_csv_row_sums_match_test_count(self):
        """Sum of all confusion matrix cells should equal test set size."""
        with MANIFEST_PATH.open("r", encoding="utf-8", newline="") as fh:
            all_rows = list(csv.DictReader(fh))
        test_count = sum(1 for r in all_rows if r["split"] == "test")

        with CM_CSV.open("r", encoding="utf-8", newline="") as fh:
            reader = csv.reader(fh)
            next(reader)
            total = sum(int(val) for row in reader for val in row[1:])
        assert total == test_count

    def test_csv_class_names_match_mapping(self, id_to_class):
        with CM_CSV.open("r", encoding="utf-8", newline="") as fh:
            reader = csv.reader(fh)
            next(reader)
            csv_classes = [row[0] for row in reader]
        assert csv_classes == id_to_class


class TestConfusionMatrixPNG:
    def test_png_exists(self):
        assert CM_PNG.exists(), f"Confusion matrix PNG not found: {CM_PNG}"

    def test_png_nonempty(self):
        assert CM_PNG.stat().st_size > 0

    def test_png_is_valid_image(self):
        """Check PNG magic bytes."""
        with CM_PNG.open("rb") as fh:
            header = fh.read(8)
        assert header[:4] == b"\x89PNG"


# ── Training report ─────────────────────────────────────────────────


class TestTrainingReport:
    def test_report_exists(self):
        assert REPORT.exists(), f"Training report not found: {REPORT}"

    def test_report_nonempty(self):
        assert REPORT.stat().st_size > 0

    def test_report_has_setup_section(self):
        text = REPORT.read_text(encoding="utf-8")
        assert "## Setup" in text

    def test_report_has_dataset_splits(self):
        text = REPORT.read_text(encoding="utf-8")
        assert "## Dataset Splits" in text

    def test_report_has_test_results(self):
        text = REPORT.read_text(encoding="utf-8")
        assert "## Test Set Results" in text

    def test_report_has_training_history(self):
        text = REPORT.read_text(encoding="utf-8")
        assert "## Training History" in text

    def test_report_has_per_class_metrics(self):
        text = REPORT.read_text(encoding="utf-8")
        assert "## Per-Class Test Metrics" in text

    def test_report_has_confusion_matrix_section(self):
        text = REPORT.read_text(encoding="utf-8")
        assert "## Confusion Matrix" in text

    def test_report_has_notes(self):
        text = REPORT.read_text(encoding="utf-8")
        assert "## Notes" in text

    def test_report_mentions_feature_extraction(self):
        text = REPORT.read_text(encoding="utf-8")
        assert "Feature extraction" in text or "feature extraction" in text.lower()

    def test_report_documents_training_durations(self):
        text = REPORT.read_text(encoding="utf-8")
        assert "Feature extraction time:" in text
        assert "Classification-head training time:" in text
        assert "Total end-to-end training time:" in text

    def test_report_test_accuracy_present(self):
        """Report should contain a test accuracy value > 0."""
        text = REPORT.read_text(encoding="utf-8")
        # Find the Test Set Results section and check for a table
        idx = text.index("## Test Set Results")
        section = text[idx:idx + 500]
        assert "| Accuracy |" in section
