"""Evaluate the trained plant disease classifier on the test set.

Loads the best checkpoint from Step 3, runs inference on the test split,
and generates a confusion matrix + per-class metrics + training report.

Outputs:
- ``reports/plantvillage_confusion_matrix.png``
- ``reports/plantvillage_confusion_matrix.csv``
- ``reports/plantvillage_training_report.md``

Stdlib + PyTorch + torchvision + sklearn + matplotlib + numpy.
"""

from __future__ import annotations

import csv
import importlib.util
from collections import Counter
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import numpy as np
import torch
import torch.nn as nn
from torch.utils.data import DataLoader
from sklearn.metrics import (
    accuracy_score,
    classification_report,
    confusion_matrix,
    f1_score,
    precision_score,
    recall_score,
)

NUM_CLASSES = 15


def load_training_module():
    """Import the training module dynamically (filename starts with digit)."""
    script_path = Path(__file__).resolve().parent / "03_train_plantvillage_model.py"
    spec = importlib.util.spec_from_file_location("train_module", script_path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def load_model(
    checkpoint_path: Path,
    device: torch.device,
) -> nn.Module:
    """Load the model architecture and restore weights from checkpoint."""
    checkpoint = torch.load(checkpoint_path, map_location=device, weights_only=False)
    train_mod = load_training_module()
    num_classes = checkpoint.get("num_classes", NUM_CLASSES)
    head_architecture = checkpoint.get("head_architecture", "baseline")
    # ResNet-18 fc in_features is lost once the head is replaced; recover it
    # from the first Linear layer in a freshly built default head.
    temp_model = train_mod.build_model(num_classes)
    in_features = None
    for module in temp_model.fc.modules():
        if isinstance(module, nn.Linear):
            in_features = module.in_features
            break
    if in_features is None:
        raise ValueError("Could not determine backbone output features from default head")
    head = train_mod.build_head(head_architecture, in_features, num_classes)
    model = train_mod.build_model(num_classes, head=head)
    model.load_state_dict(checkpoint["model_state_dict"])
    model = model.to(device)
    model.eval()
    return model


@torch.no_grad()
def predict(
    model: nn.Module,
    loader: DataLoader,
    device: torch.device,
) -> Tuple[List[int], List[int]]:
    """Run inference and return (predictions, ground_truth)."""
    all_preds: List[int] = []
    all_labels: List[int] = []

    for images, labels in loader:
        images = images.to(device)
        outputs = model(images)
        preds = outputs.argmax(dim=1).cpu().tolist()
        all_preds.extend(preds)
        all_labels.extend(labels.tolist())

    return all_preds, all_labels


def compute_metrics(
    y_true: List[int],
    y_pred: List[int],
) -> Dict[str, Any]:
    """Compute overall and per-class metrics."""
    acc = accuracy_score(y_true, y_pred)
    prec = precision_score(y_true, y_pred, average="macro", zero_division=0)
    rec = recall_score(y_true, y_pred, average="macro", zero_division=0)
    f1 = f1_score(y_true, y_pred, average="macro", zero_division=0)

    per_class = classification_report(
        y_true, y_pred, output_dict=True, zero_division=0
    )

    cm = confusion_matrix(y_true, y_pred)

    return {
        "accuracy": acc,
        "precision_macro": prec,
        "recall_macro": rec,
        "f1_macro": f1,
        "per_class": per_class,
        "confusion_matrix": cm,
        "total_samples": len(y_true),
    }


def find_top_misclassified(
    y_true: List[int],
    y_pred: List[int],
    id_to_class: List[str],
    top_n: int = 5,
) -> List[Dict[str, Any]]:
    """Find the most common misclassification pairs."""
    misclass: Counter = Counter()
    for t, p in zip(y_true, y_pred):
        if t != p:
            misclass[(t, p)] += 1

    results = []
    for (true_id, pred_id), count in misclass.most_common(top_n):
        results.append({
            "true_class": id_to_class[true_id],
            "predicted_class": id_to_class[pred_id],
            "count": count,
        })
    return results


def save_confusion_matrix_csv(
    cm: np.ndarray,
    id_to_class: List[str],
    output_path: Path,
) -> None:
    """Save confusion matrix as CSV."""
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with output_path.open("w", encoding="utf-8", newline="") as fh:
        writer = csv.writer(fh, lineterminator="\n")
        header = ["true_class"] + id_to_class
        writer.writerow(header)
        for i, class_name in enumerate(id_to_class):
            row = [class_name] + cm[i].tolist()
            writer.writerow(row)


def save_confusion_matrix_png(
    cm: np.ndarray,
    id_to_class: List[str],
    output_path: Path,
) -> None:
    """Save confusion matrix as a PNG heatmap."""
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    output_path.parent.mkdir(parents=True, exist_ok=True)

    # Normalize rows (true labels) to show proportions
    cm_norm = cm.astype(float) / cm.sum(axis=1, keepdims=True)
    cm_norm = np.nan_to_num(cm_norm)

    short_names = []
    for name in id_to_class:
        # Shorten for readability
        short = name.replace("__", " ").replace("_", " ")
        if len(short) > 20:
            short = short[:17] + "..."
        short_names.append(short)

    fig, ax = plt.subplots(figsize=(14, 12))
    im = ax.imshow(cm_norm, interpolation="nearest", cmap=plt.cm.Blues, vmin=0, vmax=1)
    ax.figure.colorbar(im, ax=ax, fraction=0.046, pad=0.04)

    ax.set(
        xticks=range(len(short_names)),
        yticks=range(len(short_names)),
        xticklabels=short_names,
        yticklabels=short_names,
        ylabel="True label",
        xlabel="Predicted label",
        title="PlantVillage Confusion Matrix (Normalized)",
    )
    plt.setp(ax.get_xticklabels(), rotation=45, ha="right", rotation_mode="anchor")

    # Add text annotations
    thresh = cm_norm.max() / 2.0
    for i in range(cm.shape[0]):
        for j in range(cm.shape[1]):
            ax.text(
                j, i, f"{cm[i, j]}\n({cm_norm[i, j]:.2f})",
                ha="center", va="center",
                color="white" if cm_norm[i, j] > thresh else "black",
                fontsize=7,
            )

    fig.tight_layout()
    fig.savefig(output_path, dpi=150)
    plt.close(fig)


def write_training_report(
    training_result: Dict[str, Any],
    eval_metrics: Dict[str, Any],
    top_misclassified: List[Dict[str, Any]],
    id_to_class: List[str],
    report_path: Path,
) -> None:
    """Write the combined training + evaluation report."""
    report_path.parent.mkdir(parents=True, exist_ok=True)

    history = training_result["history"]
    best_epoch = training_result["best_epoch"]
    best_row = history[best_epoch - 1]

    lines = [
        "# PlantVillage Training Report",
        "",
        "## Setup",
        "",
        "| Parameter | Value |",
        "|-----------|-------|",
        "| Model | ResNet-18 (ImageNet pretrained) |",
        "| Approach | Feature extraction (frozen backbone + linear head) |",
        f"| Device | {training_result['device']} |",
        "| Optimizer | AdamW |",
        "| Learning rate | 1e-4 |",
        "| Weight decay | 1e-2 |",
        "| Scheduler | CosineAnnealingLR |",
        f"| Loss | CrossEntropyLoss (class-weighted) |",
        f"| Epochs | {len(history)} |",
        f"| Batch size | 32 |",
        f"| Image size | 224×224 |",
        f"| Seed | 42 |",
        "",
        "## Dataset Splits",
        "",
        "| Split | Count |",
        "|-------|-------|",
        f"| Train | {training_result['train_count']} |",
        f"| Val | {training_result['val_count']} |",
        f"| Test | {training_result['test_count']} |",
        f"| Total | {training_result['train_count'] + training_result['val_count'] + training_result['test_count']} |",
        f"| Classes | {training_result['num_classes']} |",
        "",
        "## Best Epoch",
        "",
        "| Metric | Value |",
        "|--------|-------|",
        f"| Best epoch | {best_epoch} |",
        f"| Train loss | {best_row['train_loss']:.4f} |",
        f"| Train accuracy | {best_row['train_acc']:.4f} |",
        f"| Val loss | {best_row['val_loss']:.4f} |",
        f"| Val accuracy | {best_row['val_acc']:.4f} |",
        f"| Val F1 (macro) | {best_row['val_f1']:.4f} |",
        "",
        "## Test Set Results",
        "",
        "| Metric | Value |",
        "|--------|-------|",
        f"| Accuracy | {eval_metrics['accuracy']:.4f} |",
        f"| Precision (macro) | {eval_metrics['precision_macro']:.4f} |",
        f"| Recall (macro) | {eval_metrics['recall_macro']:.4f} |",
        f"| F1 (macro) | {eval_metrics['f1_macro']:.4f} |",
        f"| Samples evaluated | {eval_metrics['total_samples']} |",
        "",
        "## Training History",
        "",
        "| Epoch | Train Loss | Train Acc | Val Loss | Val Acc | Val F1 | LR | Time (s) |",
        "|-------|-----------|-----------|----------|---------|--------|-----|----------|",
    ]

    for h in history:
        lines.append(
            f"| {h['epoch']} | {h['train_loss']:.4f} | {h['train_acc']:.4f} "
            f"| {h['val_loss']:.4f} | {h['val_acc']:.4f} | {h['val_f1']:.4f} "
            f"| {h['lr']:.6f} | {h['elapsed_sec']} |"
        )

    lines += [
        "",
        "## Per-Class Test Metrics",
        "",
        "| Class | Precision | Recall | F1 | Support |",
        "|-------|-----------|--------|-----|---------|",
    ]

    per_class = eval_metrics["per_class"]
    for i, class_name in enumerate(id_to_class):
        key = str(i)
        if key in per_class:
            m = per_class[key]
            support = int(m.get("support", 0))
            lines.append(
                f"| {class_name} | {m['precision']:.4f} | {m['recall']:.4f} "
                f"| {m['f1-score']:.4f} | {support} |"
            )

    lines += [
        "",
        "## Top Misclassified Pairs",
        "",
        "| True Class | Predicted Class | Count |",
        "|------------|-----------------|-------|",
    ]

    if top_misclassified:
        for entry in top_misclassified:
            lines.append(
                f"| {entry['true_class']} | {entry['predicted_class']} | {entry['count']} |"
            )
    else:
        lines.append("| (none) | — | 0 |")

    lines += [
        "",
        "## Confusion Matrix",
        "",
        f"- PNG: `reports/plantvillage_confusion_matrix.png`",
        f"- CSV: `reports/plantvillage_confusion_matrix.csv`",
        f"- Dimensions: {eval_metrics['confusion_matrix'].shape[0]}×{eval_metrics['confusion_matrix'].shape[1]}",
        "",
        "## Saved Artifacts",
        "",
        f"- Model weights: `{training_result['checkpoint_path']}`",
        f"- Training history: `{training_result['history_path']}`",
        f"- This report: `reports/plantvillage_training_report.md`",
        "",
        "## Notes",
        "",
        "- Feature-extraction approach: ResNet-18 backbone frozen, features pre-computed once.",
        "- Classification head (Dropout(0.3) + Linear) trained on cached 512-dim features.",
        "- Class weights computed as inverse frequency to handle imbalance.",
        "- Best checkpoint selected by validation macro-F1.",
        "- Test set never used for training or model selection.",
        f"- Feature extraction time: {training_result['feature_extraction_sec']:.1f}s.",
        f"- Classification-head training time: {training_result['head_training_sec']:.1f}s.",
        f"- Total end-to-end training time: {training_result['total_elapsed_sec']:.1f}s.",
    ]

    with report_path.open("w", encoding="utf-8") as fh:
        fh.write("\n".join(lines) + "\n")


def run(
    checkpoint_path: Optional[Path] = None,
    manifest_path: Optional[Path] = None,
    mapping_path: Optional[Path] = None,
    report_dir: Optional[Path] = None,
    batch_size: int = 32,
) -> Dict[str, Any]:
    """Full evaluation pipeline."""
    root = Path(__file__).resolve().parent.parent
    checkpoint_path = checkpoint_path or (root / "models" / "best_plantvillage_model.pt")
    manifest_path = manifest_path or (root / "data" / "processed" / "plantvillage_manifest_clean.csv")
    mapping_path = mapping_path or (root / "data" / "processed" / "plantvillage_class_mapping.csv")
    report_dir = report_dir or (root / "reports")

    train_mod = load_training_module()
    train_mod.set_seed(train_mod.SEED)
    device = train_mod.get_device()
    print(f"Device: {device}")

    print("Loading manifest and class mapping...")
    all_rows, class_to_id, id_to_class = train_mod.load_manifest_and_mapping(
        manifest_path, mapping_path
    )
    _, _, test_rows = train_mod.split_manifest(all_rows)
    print(f"  Test samples: {len(test_rows)}")

    print("Loading model...")
    model = load_model(checkpoint_path, device)
    print(f"  Loaded checkpoint from {checkpoint_path}")

    print("Building test dataloader...")
    test_ds = train_mod.PlantVillageDataset(
        test_rows, class_to_id, train_mod.get_eval_transforms()
    )
    test_loader = DataLoader(
        test_ds, batch_size=batch_size, shuffle=False, num_workers=0
    )

    print("Running inference on test set...")
    y_pred, y_true = predict(model, test_loader, device)
    print(f"  Predicted {len(y_pred)} samples")

    print("Computing metrics...")
    metrics = compute_metrics(y_true, y_pred)
    print(f"  Accuracy: {metrics['accuracy']:.4f}")
    print(f"  F1 (macro): {metrics['f1_macro']:.4f}")

    print("Finding top misclassified pairs...")
    top_mis = find_top_misclassified(y_true, y_pred, id_to_class)
    for m in top_mis:
        print(f"  {m['true_class']} -> {m['predicted_class']}: {m['count']}")

    print("Saving confusion matrix...")
    cm_png = report_dir / "plantvillage_confusion_matrix.png"
    cm_csv = report_dir / "plantvillage_confusion_matrix.csv"
    save_confusion_matrix_png(metrics["confusion_matrix"], id_to_class, cm_png)
    save_confusion_matrix_csv(metrics["confusion_matrix"], id_to_class, cm_csv)
    print(f"  PNG: {cm_png}")
    print(f"  CSV: {cm_csv}")

    # Load training history and checkpoint metadata for the report
    checkpoint_metadata = torch.load(checkpoint_path, map_location="cpu", weights_only=False)
    history_path = checkpoint_path.parent / "training_history.csv"
    history = []
    if history_path.exists():
        with history_path.open("r", encoding="utf-8", newline="") as fh:
            history = list(csv.DictReader(fh))
        for h in history:
            for k in ("epoch", "elapsed_sec"):
                h[k] = int(h[k]) if k == "epoch" else float(h[k])
            for k in ("train_loss", "train_acc", "val_loss", "val_acc", "val_f1", "lr"):
                h[k] = float(h[k])

    best_epoch = 0
    best_f1 = 0.0
    for h in history:
        if h["val_f1"] > best_f1:
            best_f1 = h["val_f1"]
            best_epoch = h["epoch"]

    train_counts = Counter(r["class_name"] for r in all_rows if r["split"] == "train")
    val_counts = Counter(r["class_name"] for r in all_rows if r["split"] == "val")
    test_counts = Counter(r["class_name"] for r in all_rows if r["split"] == "test")

    training_result = {
        "history": history,
        "best_epoch": best_epoch,
        "best_val_f1": best_f1,
        "train_count": sum(train_counts.values()),
        "val_count": sum(val_counts.values()),
        "test_count": sum(test_counts.values()),
        "num_classes": NUM_CLASSES,
        "checkpoint_path": str(checkpoint_path),
        "history_path": str(history_path),
        "device": str(device),
        "total_elapsed_sec": checkpoint_metadata.get(
            "training_duration_sec", sum(h.get("elapsed_sec", 0) for h in history)
        ),
        "feature_extraction_sec": checkpoint_metadata.get("feature_extraction_sec", 0.0),
        "head_training_sec": checkpoint_metadata.get(
            "head_training_sec", sum(h.get("elapsed_sec", 0) for h in history)
        ),
    }

    print("Writing training report...")
    report_path = report_dir / "plantvillage_training_report.md"
    write_training_report(
        training_result, metrics, top_mis, id_to_class, report_path
    )
    print(f"  Report: {report_path}")

    return {
        "metrics": metrics,
        "top_misclassified": top_mis,
        "report_path": str(report_path),
        "cm_png": str(cm_png),
        "cm_csv": str(cm_csv),
        "training_result": training_result,
    }


if __name__ == "__main__":
    result = run()
    m = result["metrics"]
    print(f"\nFinal test results:")
    print(f"  Accuracy:  {m['accuracy']:.4f}")
    print(f"  Precision: {m['precision_macro']:.4f}")
    print(f"  Recall:    {m['recall_macro']:.4f}")
    print(f"  F1:        {m['f1_macro']:.4f}")
