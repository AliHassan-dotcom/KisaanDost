"""Tests for PlantVillage baseline-to-v2 comparison and leakage guard."""

from __future__ import annotations

import csv
import importlib.util
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent.parent
BASELINE_REPORT = ROOT / "reports" / "plantvillage_training_report.md"
BASELINE_MATRIX = ROOT / "reports" / "plantvillage_confusion_matrix.csv"


@pytest.fixture(scope="module")
def compare_mod():
    script = ROOT / "scripts" / "06_compare_plantvillage_models.py"
    spec = importlib.util.spec_from_file_location("compare_module", script)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class TestBaselineSources:
    def test_parses_existing_baseline_report(self, compare_mod):
        metrics = compare_mod.parse_baseline_report(BASELINE_REPORT)
        assert metrics == {
            "validation_macro_f1": 0.8332,
            "test_accuracy": 0.8507,
            "test_precision_macro": 0.8157,
            "test_recall_macro": 0.8497,
            "test_f1_macro": 0.8281,
        }

    def test_loads_baseline_confusion_matrix(self, compare_mod):
        classes, matrix = compare_mod.load_confusion_matrix(BASELINE_MATRIX)
        assert len(classes) == 15
        assert len(matrix) == 15
        assert matrix["Tomato_Late_blight"]["Tomato_Early_blight"] == 43

    def test_measures_target_blight_confusion(self, compare_mod):
        _, matrix = compare_mod.load_confusion_matrix(BASELINE_MATRIX)
        result = compare_mod.blight_confusion(matrix)
        assert result["count"] == 43
        assert result["support"] == 287
        assert result["rate"] == pytest.approx(43 / 287)


class TestCandidateHistory:
    def test_best_validation_record(self, compare_mod):
        history = [
            {"epoch": 1, "val_f1_macro": 0.82},
            {"epoch": 2, "val_f1_macro": 0.85},
            {"epoch": 3, "val_f1_macro": 0.84},
        ]
        assert compare_mod.best_validation_record(history) == history[1]

    def test_empty_history_has_no_candidate(self, compare_mod):
        assert compare_mod.best_validation_record([]) is None

    def test_load_history_converts_values(self, compare_mod, tmp_path):
        history_path = tmp_path / "history.csv"
        history_path.write_text(
            "epoch,val_f1_macro,elapsed_sec\n1,0.84,2.5\n",
            encoding="utf-8",
        )
        rows = compare_mod.load_history(history_path)
        assert rows == [{"epoch": 1, "val_f1_macro": 0.84, "elapsed_sec": 2.5}]


class TestComparisonOutputs:
    def test_comparison_csv_schema(self, compare_mod, tmp_path):
        path = tmp_path / "comparison.csv"
        row = {field: "" for field in compare_mod.COMPARISON_FIELDS}
        row["model"] = "baseline"
        compare_mod.write_comparison_csv([row], path)
        with path.open("r", encoding="utf-8", newline="") as handle:
            reader = csv.DictReader(handle)
            assert reader.fieldnames == compare_mod.COMPARISON_FIELDS
            assert list(reader)[0]["model"] == "baseline"

    def test_no_improvement_report_skips_test_claim(self, compare_mod, tmp_path):
        output_path = tmp_path / "report.md"
        baseline = {
            "validation_macro_f1": 0.8332,
            "test_accuracy": 0.8507,
            "test_precision_macro": 0.8157,
            "test_recall_macro": 0.8497,
            "test_f1_macro": 0.8281,
        }
        blight = {"count": 43, "support": 287, "rate": 43 / 287}
        compare_mod.write_improvement_report(
            baseline,
            blight,
            {"epoch": 2, "val_f1_macro": 0.83},
            None,
            output_path,
        )
        report = output_path.read_text(encoding="utf-8")
        assert "No v2 held-out test evaluation was run" in report
        assert "Tomato Late blight → Tomato Early blight" in report
        assert "Leakage Guard" in report

    def test_selected_report_includes_v2_test_comparison(self, compare_mod, tmp_path):
        output_path = tmp_path / "report.md"
        baseline = {
            "validation_macro_f1": 0.8332,
            "test_accuracy": 0.8507,
            "test_precision_macro": 0.8157,
            "test_recall_macro": 0.8497,
            "test_f1_macro": 0.8281,
        }
        blight = {"count": 43, "support": 287, "rate": 43 / 287}
        evaluation = {
            "metrics": {
                "accuracy": 0.86,
                "precision_macro": 0.83,
                "recall_macro": 0.85,
                "f1_macro": 0.84,
            },
            "blight": {"count": 30, "support": 287, "rate": 30 / 287},
        }
        compare_mod.write_improvement_report(
            baseline,
            blight,
            {"epoch": 2, "val_f1_macro": 0.84},
            evaluation,
            output_path,
        )
        report = output_path.read_text(encoding="utf-8")
        assert "| Accuracy | 0.8507 | 0.8600 | +0.0093 |" in report
        assert "30 / 287" in report
