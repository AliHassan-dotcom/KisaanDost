"""Compare the immutable PlantVillage baseline with a validation-selected v2 model.

Baseline test metrics are read from the existing report. A held-out test pass is
performed only if the v2 checkpoint exists and records strict validation
improvement over the baseline.
"""

from __future__ import annotations

import csv
import importlib.util
import re
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import torch
from torch.utils.data import DataLoader

NUM_CLASSES = 15
LATE_BLIGHT = "Tomato_Late_blight"
EARLY_BLIGHT = "Tomato_Early_blight"
COMPARISON_FIELDS = [
    "model",
    "selection_status",
    "validation_macro_f1",
    "test_accuracy",
    "test_precision_macro",
    "test_recall_macro",
    "test_f1_macro",
    "tomato_late_to_early_count",
    "tomato_late_to_early_rate",
    "metric_source",
]


def load_evaluation_module():
    """Import Step 4 helpers from its numeric-prefixed filename."""
    script_path = Path(__file__).resolve().parent / "04_evaluate_plantvillage_model.py"
    spec = importlib.util.spec_from_file_location("plantvillage_eval_module", script_path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def parse_markdown_metric(report_text: str, label: str) -> float:
    """Read a numeric metric from a two-column Markdown report table."""
    pattern = rf"\| {re.escape(label)} \| ([0-9]+(?:\.[0-9]+)?) \|"
    match = re.search(pattern, report_text)
    if match is None:
        raise ValueError(f"Metric not found in baseline report: {label}")
    return float(match.group(1))


def parse_baseline_report(report_path: Path) -> Dict[str, float]:
    """Extract immutable validation and test metrics from the baseline report."""
    report_text = report_path.read_text(encoding="utf-8")
    return {
        "validation_macro_f1": parse_markdown_metric(report_text, "Val F1 (macro)"),
        "test_accuracy": parse_markdown_metric(report_text, "Accuracy"),
        "test_precision_macro": parse_markdown_metric(report_text, "Precision (macro)"),
        "test_recall_macro": parse_markdown_metric(report_text, "Recall (macro)"),
        "test_f1_macro": parse_markdown_metric(report_text, "F1 (macro)"),
    }


def load_confusion_matrix(csv_path: Path) -> Tuple[List[str], Dict[str, Dict[str, int]]]:
    """Load the Step 4 count matrix keyed by true and predicted class names."""
    with csv_path.open("r", encoding="utf-8", newline="") as handle:
        reader = csv.DictReader(handle)
        if not reader.fieldnames or reader.fieldnames[0] != "true_class":
            raise ValueError(f"Invalid confusion matrix header: {csv_path}")
        class_names = reader.fieldnames[1:]
        matrix = {
            row["true_class"]: {name: int(row[name]) for name in class_names}
            for row in reader
        }
    return class_names, matrix


def blight_confusion(
    matrix: Dict[str, Dict[str, int]],
    true_class: str = LATE_BLIGHT,
    predicted_class: str = EARLY_BLIGHT,
) -> Dict[str, float]:
    """Return the specified true-to-predicted count and row-normalized rate."""
    if true_class not in matrix or predicted_class not in matrix[true_class]:
        raise ValueError(f"Missing blight classes in confusion matrix: {true_class}, {predicted_class}")
    row = matrix[true_class]
    total = sum(row.values())
    count = row[predicted_class]
    return {
        "count": count,
        "rate": count / total if total else 0.0,
        "support": total,
    }


def load_history(history_path: Path) -> List[Dict[str, Any]]:
    """Load the v2 training history, if the candidate experiment was run."""
    if not history_path.exists():
        return []
    with history_path.open("r", encoding="utf-8", newline="") as handle:
        rows = list(csv.DictReader(handle))
    for row in rows:
        row["epoch"] = int(row["epoch"])
        for key in row:
            if key != "epoch":
                row[key] = float(row[key])
    return rows


def best_validation_record(history: List[Dict[str, Any]]) -> Optional[Dict[str, Any]]:
    """Find the strongest candidate epoch without accessing test data."""
    if not history:
        return None
    return max(history, key=lambda row: row["val_f1_macro"])


def evaluate_v2(
    checkpoint_path: Path,
    manifest_path: Path,
    mapping_path: Path,
    report_dir: Path,
    batch_size: int,
) -> Dict[str, Any]:
    """Perform the single permitted test pass for an accepted v2 checkpoint."""
    eval_mod = load_evaluation_module()
    train_mod = eval_mod.load_training_module()
    train_mod.set_seed(train_mod.SEED)
    device = train_mod.get_device()
    all_rows, class_to_id, id_to_class = train_mod.load_manifest_and_mapping(
        manifest_path, mapping_path,
    )
    _, _, test_rows = train_mod.split_manifest(all_rows)
    model = eval_mod.load_model(checkpoint_path, device)
    dataset = train_mod.PlantVillageDataset(
        test_rows, class_to_id, train_mod.get_eval_transforms(),
    )
    loader = DataLoader(dataset, batch_size=batch_size, shuffle=False, num_workers=0)
    predictions, labels = eval_mod.predict(model, loader, device)
    metrics = eval_mod.compute_metrics(labels, predictions)

    png_path = report_dir / "plantvillage_confusion_matrix_v2.png"
    csv_path = report_dir / "plantvillage_confusion_matrix_v2.csv"
    eval_mod.save_confusion_matrix_png(metrics["confusion_matrix"], id_to_class, png_path)
    eval_mod.save_confusion_matrix_csv(metrics["confusion_matrix"], id_to_class, csv_path)
    _, matrix = load_confusion_matrix(csv_path)
    return {
        "metrics": metrics,
        "blight": blight_confusion(matrix),
        "csv_path": str(csv_path),
        "png_path": str(png_path),
    }


def write_comparison_csv(rows: List[Dict[str, Any]], output_path: Path) -> None:
    """Save baseline and candidate measurements in a stable comparison format."""
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with output_path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=COMPARISON_FIELDS, lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)


def write_improvement_report(
    baseline: Dict[str, float],
    baseline_blight: Dict[str, float],
    candidate_record: Optional[Dict[str, Any]],
    candidate_evaluation: Optional[Dict[str, Any]],
    output_path: Path,
) -> None:
    """Document validation selection and the conditional held-out comparison."""
    output_path.parent.mkdir(parents=True, exist_ok=True)
    lines = [
        "# PlantVillage Model Improvement Report",
        "",
        "## Validation Selection",
        "",
        "| Model | Validation macro-F1 | Status |",
        "|-------|---------------------|--------|",
        f"| Baseline | {baseline['validation_macro_f1']:.4f} | Immutable reference |",
    ]

    if candidate_record is None:
        lines.append("| V2 candidate | — | No v2 training history found |")
    elif candidate_evaluation is None:
        lines.append(
            f"| V2 candidate | {candidate_record['val_f1_macro']:.4f} | "
            "Not selected; did not strictly exceed baseline |"
        )
    else:
        lines.append(
            f"| V2 candidate | {candidate_record['val_f1_macro']:.4f} | "
            "Selected; strictly exceeded baseline |"
        )

    lines += [
        "",
        "The baseline metrics were read from `reports/plantvillage_training_report.md`; "
        "the baseline was not re-evaluated.",
        "",
        "## Test-Set Comparison",
        "",
    ]

    if candidate_evaluation is None:
        lines += [
            "No v2 held-out test evaluation was run because no candidate passed the "
            "validation gate.",
            "",
        ]
    else:
        metrics = candidate_evaluation["metrics"]
        lines += [
            "| Metric | Baseline | V2 | Delta (V2 - Baseline) |",
            "|--------|----------|----|-----------------------|",
            f"| Accuracy | {baseline['test_accuracy']:.4f} | {metrics['accuracy']:.4f} | {metrics['accuracy'] - baseline['test_accuracy']:+.4f} |",
            f"| Precision (macro) | {baseline['test_precision_macro']:.4f} | {metrics['precision_macro']:.4f} | {metrics['precision_macro'] - baseline['test_precision_macro']:+.4f} |",
            f"| Recall (macro) | {baseline['test_recall_macro']:.4f} | {metrics['recall_macro']:.4f} | {metrics['recall_macro'] - baseline['test_recall_macro']:+.4f} |",
            f"| F1 (macro) | {baseline['test_f1_macro']:.4f} | {metrics['f1_macro']:.4f} | {metrics['f1_macro'] - baseline['test_f1_macro']:+.4f} |",
            "",
        ]

    lines += [
        "## Tomato Blight Confusion",
        "",
        "| True → Predicted | Baseline count / support | Baseline rate | V2 count / support | V2 rate |",
        "|------------------|--------------------------|---------------|--------------------|---------|",
    ]
    if candidate_evaluation is None:
        lines.append(
            f"| Tomato Late blight → Tomato Early blight | "
            f"{baseline_blight['count']} / {baseline_blight['support']} | "
            f"{baseline_blight['rate']:.4f} | — | — |"
        )
    else:
        v2_blight = candidate_evaluation["blight"]
        lines.append(
            f"| Tomato Late blight → Tomato Early blight | "
            f"{baseline_blight['count']} / {baseline_blight['support']} | "
            f"{baseline_blight['rate']:.4f} | {v2_blight['count']} / "
            f"{v2_blight['support']} | {v2_blight['rate']:.4f} |"
        )

    lines += [
        "",
        "## Artifacts",
        "",
        "- Comparison CSV: `reports/plantvillage_model_comparison.csv`",
        "- Improvement report: `reports/plantvillage_model_improvement_report.md`",
    ]
    if candidate_evaluation is not None:
        lines += [
            "- V2 confusion matrix CSV: `reports/plantvillage_confusion_matrix_v2.csv`",
            "- V2 confusion matrix PNG: `reports/plantvillage_confusion_matrix_v2.png`",
        ]
    lines += [
        "",
        "## Leakage Guard",
        "",
        "- V2 selection used validation macro-F1 only.",
        "- The test split was evaluated once only after the validation gate accepted v2.",
    ]
    output_path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def run(
    baseline_report_path: Optional[Path] = None,
    baseline_confusion_path: Optional[Path] = None,
    v2_checkpoint_path: Optional[Path] = None,
    v2_history_path: Optional[Path] = None,
    manifest_path: Optional[Path] = None,
    mapping_path: Optional[Path] = None,
    report_dir: Optional[Path] = None,
    batch_size: int = 32,
) -> Dict[str, Any]:
    """Compare baseline to v2 and conditionally evaluate the accepted candidate."""
    root = Path(__file__).resolve().parent.parent
    baseline_report_path = baseline_report_path or (
        root / "reports" / "plantvillage_training_report.md"
    )
    baseline_confusion_path = baseline_confusion_path or (
        root / "reports" / "plantvillage_confusion_matrix.csv"
    )
    v2_checkpoint_path = v2_checkpoint_path or (
        root / "models" / "best_plantvillage_model_v2.pt"
    )
    v2_history_path = v2_history_path or (
        root / "models" / "training_history_v2.csv"
    )
    manifest_path = manifest_path or (
        root / "data" / "processed" / "plantvillage_manifest_clean.csv"
    )
    mapping_path = mapping_path or (
        root / "data" / "processed" / "plantvillage_class_mapping.csv"
    )
    report_dir = report_dir or (root / "reports")

    baseline = parse_baseline_report(baseline_report_path)
    _, baseline_matrix = load_confusion_matrix(baseline_confusion_path)
    baseline_blight = blight_confusion(baseline_matrix)
    history = load_history(v2_history_path)
    candidate_record = best_validation_record(history)
    candidate_evaluation: Optional[Dict[str, Any]] = None

    if v2_checkpoint_path.exists():
        checkpoint = torch.load(v2_checkpoint_path, map_location="cpu", weights_only=False)
        checkpoint_f1 = float(checkpoint["val_f1"])
        if checkpoint_f1 <= baseline["validation_macro_f1"]:
            raise ValueError("Refusing v2 test evaluation without strict validation improvement")
        candidate_evaluation = evaluate_v2(
            v2_checkpoint_path,
            manifest_path,
            mapping_path,
            report_dir,
            batch_size,
        )
        if candidate_record is None:
            candidate_record = {
                "epoch": checkpoint["epoch"],
                "val_f1_macro": checkpoint_f1,
            }

    baseline_row: Dict[str, Any] = {
        "model": "baseline",
        "selection_status": "immutable_reference",
        "validation_macro_f1": f"{baseline['validation_macro_f1']:.4f}",
        "test_accuracy": f"{baseline['test_accuracy']:.4f}",
        "test_precision_macro": f"{baseline['test_precision_macro']:.4f}",
        "test_recall_macro": f"{baseline['test_recall_macro']:.4f}",
        "test_f1_macro": f"{baseline['test_f1_macro']:.4f}",
        "tomato_late_to_early_count": baseline_blight["count"],
        "tomato_late_to_early_rate": f"{baseline_blight['rate']:.4f}",
        "metric_source": "existing_baseline_report_and_confusion_matrix",
    }
    if candidate_evaluation is None:
        v2_row: Dict[str, Any] = {
            "model": "v2",
            "selection_status": "not_selected",
            "validation_macro_f1": (
                f"{candidate_record['val_f1_macro']:.4f}" if candidate_record else ""
            ),
            "test_accuracy": "",
            "test_precision_macro": "",
            "test_recall_macro": "",
            "test_f1_macro": "",
            "tomato_late_to_early_count": "",
            "tomato_late_to_early_rate": "",
            "metric_source": "validation_history_only_no_test_evaluation",
        }
    else:
        metrics = candidate_evaluation["metrics"]
        blight = candidate_evaluation["blight"]
        v2_row = {
            "model": "v2",
            "selection_status": "selected",
            "validation_macro_f1": f"{candidate_record['val_f1_macro']:.4f}",
            "test_accuracy": f"{metrics['accuracy']:.4f}",
            "test_precision_macro": f"{metrics['precision_macro']:.4f}",
            "test_recall_macro": f"{metrics['recall_macro']:.4f}",
            "test_f1_macro": f"{metrics['f1_macro']:.4f}",
            "tomato_late_to_early_count": blight["count"],
            "tomato_late_to_early_rate": f"{blight['rate']:.4f}",
            "metric_source": "single_v2_held_out_test_evaluation",
        }

    comparison_path = report_dir / "plantvillage_model_comparison.csv"
    improvement_path = report_dir / "plantvillage_model_improvement_report.md"
    write_comparison_csv([baseline_row, v2_row], comparison_path)
    write_improvement_report(
        baseline,
        baseline_blight,
        candidate_record,
        candidate_evaluation,
        improvement_path,
    )
    return {
        "baseline": baseline,
        "candidate_record": candidate_record,
        "candidate_evaluation": candidate_evaluation,
        "comparison_path": str(comparison_path),
        "improvement_path": str(improvement_path),
    }


if __name__ == "__main__":
    result = run()
    print(f"Comparison: {result['comparison_path']}")
    print(f"Improvement report: {result['improvement_path']}")
