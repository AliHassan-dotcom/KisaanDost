"""Fine-tune the PlantVillage baseline by training a better classification head.

The ResNet-18 backbone is kept frozen; only the classification head is trained on
pre-computed 512-dimensional feature vectors.  This avoids the repeated Windows CPU
access violations and out-of-memory segfaults seen when fine-tuning ``layer4`` +
``fc`` on this machine, while still producing a validation-gated v2 candidate.
"""

from __future__ import annotations

import csv
import importlib.util
import time
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import numpy as np
import torch
import torch.nn as nn
import torch.optim as optim
from sklearn.metrics import accuracy_score, f1_score, precision_score, recall_score
from torch.utils.data import DataLoader
from torchvision import transforms

SEED = 42
NUM_CLASSES = 15
IMAGE_SIZE = 224
BATCH_SIZE = 32
ETA_MIN = 1e-6

HISTORY_FIELDS = [
    "epoch",
    "train_loss",
    "train_acc",
    "val_loss",
    "val_acc",
    "val_precision_macro",
    "val_recall_macro",
    "val_f1_macro",
    "lr",
    "elapsed_sec",
]

# Candidate heads to try.  Each is trained on frozen features and the best
# validation macro-F1 strictly above the baseline is selected.
HEAD_CANDIDATES = [
    {"head_architecture": "baseline", "lr": 1e-4, "weight_decay": 1e-2, "epochs": 20},
    {"head_architecture": "mlp_256", "lr": 1e-4, "weight_decay": 1e-2, "epochs": 20},
    {"head_architecture": "mlp_512", "lr": 5e-5, "weight_decay": 1e-2, "epochs": 25},
]


def load_training_module():
    """Import the Step 3 helpers from its numeric-prefixed filename."""
    script_path = Path(__file__).resolve().parent / "03_train_plantvillage_model.py"
    spec = importlib.util.spec_from_file_location("plantvillage_train_module", script_path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def get_train_transforms() -> transforms.Compose:
    """Build moderate image variation appropriate for photographed leaves.

    Kept for API compatibility; feature extraction for this experiment uses
    eval transforms to stay within available CPU memory.
    """
    return transforms.Compose([
        transforms.RandomResizedCrop(IMAGE_SIZE, scale=(0.85, 1.0), ratio=(0.9, 1.1)),
        transforms.RandomHorizontalFlip(),
        transforms.RandomRotation(15),
        transforms.RandomAffine(degrees=0, translate=(0.05, 0.05), scale=(0.95, 1.05)),
        transforms.ColorJitter(brightness=0.2, contrast=0.2, saturation=0.15, hue=0.02),
        transforms.ToTensor(),
        transforms.Normalize(
            mean=[0.485, 0.456, 0.406],
            std=[0.229, 0.224, 0.225],
        ),
    ])


def configure_model_for_finetuning(model: nn.Module) -> List[str]:
    """Freeze the ResNet-18 backbone and expose only the head for updates."""
    for parameter in model.parameters():
        parameter.requires_grad = False
    for parameter in model.fc.parameters():
        parameter.requires_grad = True
    return ["fc"]


def should_save_candidate(candidate_val_f1: float, baseline_val_f1: float) -> bool:
    """Apply the strict validation-improvement gate for v2 weights."""
    return candidate_val_f1 > baseline_val_f1


def train_one_epoch(
    model: nn.Module,
    loader: DataLoader,
    criterion: nn.Module,
    optimizer: optim.Optimizer,
    device: torch.device,
) -> Tuple[float, float]:
    """Optimize the classification head for one epoch on cached features."""
    model.train()
    running_loss = 0.0
    all_labels: List[int] = []
    all_predictions: List[int] = []

    for features, labels in loader:
        features = features.to(device)
        labels = labels.to(device)
        optimizer.zero_grad()
        outputs = model(features)
        loss = criterion(outputs, labels)
        loss.backward()
        optimizer.step()

        running_loss += loss.item() * features.size(0)
        all_predictions.extend(outputs.argmax(dim=1).detach().cpu().tolist())
        all_labels.extend(labels.detach().cpu().tolist())

    return (
        running_loss / len(loader.dataset),
        accuracy_score(all_labels, all_predictions),
    )


@torch.no_grad()
def evaluate(
    model: nn.Module,
    loader: DataLoader,
    criterion: nn.Module,
    device: torch.device,
) -> Dict[str, float]:
    """Measure candidate quality on the validation split only."""
    model.eval()
    running_loss = 0.0
    all_labels: List[int] = []
    all_predictions: List[int] = []

    for features, labels in loader:
        features = features.to(device)
        labels = labels.to(device)
        outputs = model(features)
        loss = criterion(outputs, labels)

        running_loss += loss.item() * features.size(0)
        all_predictions.extend(outputs.argmax(dim=1).cpu().tolist())
        all_labels.extend(labels.cpu().tolist())

    return {
        "loss": running_loss / len(loader.dataset),
        "accuracy": accuracy_score(all_labels, all_predictions),
        "precision_macro": precision_score(
            all_labels, all_predictions, average="macro", zero_division=0,
        ),
        "recall_macro": recall_score(
            all_labels, all_predictions, average="macro", zero_division=0,
        ),
        "f1_macro": f1_score(
            all_labels, all_predictions, average="macro", zero_division=0,
        ),
    }


def write_history(history: List[Dict[str, Any]], output_path: Path) -> None:
    """Write validation-only selection history with stable columns."""
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with output_path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=HISTORY_FIELDS, lineterminator="\n")
        writer.writeheader()
        writer.writerows(history)


def build_checkpoint_payload(
    model: nn.Module,
    best_record: Dict[str, Any],
    baseline_checkpoint_path: Path,
    baseline_val_f1: float,
    split_counts: Dict[str, int],
    trainable_modules: List[str],
    total_duration_sec: float,
    head_architecture: str,
) -> Dict[str, Any]:
    """Assemble reproducibility metadata for an accepted v2 candidate."""
    return {
        "epoch": best_record["epoch"],
        "model_state_dict": {
            key: value.detach().cpu().clone()
            for key, value in model.state_dict().items()
        },
        "val_f1": best_record["val_f1_macro"],
        "val_acc": best_record["val_acc"],
        "val_precision_macro": best_record["val_precision_macro"],
        "val_recall_macro": best_record["val_recall_macro"],
        "num_classes": NUM_CLASSES,
        "baseline_checkpoint_path": str(baseline_checkpoint_path),
        "baseline_val_f1": baseline_val_f1,
        "selection_metric": "validation_macro_f1",
        "training_approach": "finetune_classification_head_v2",
        "head_architecture": head_architecture,
        "trainable_modules": trainable_modules,
        "split_counts": split_counts,
        "seed": SEED,
        "image_size": IMAGE_SIZE,
        "loss": "CrossEntropyLoss(class_weighted)",
        "training_duration_sec": round(total_duration_sec, 1),
    }


def train_candidate_head(
    head: nn.Module,
    train_loader: DataLoader,
    val_loader: DataLoader,
    criterion: nn.Module,
    lr: float,
    weight_decay: float,
    num_epochs: int,
    device: torch.device,
) -> Tuple[List[Dict[str, Any]], float, Optional[Dict[str, torch.Tensor]]]:
    """Train one head candidate and return its history, best F1, and best state."""
    head = head.to(device)
    optimizer = optim.AdamW(head.parameters(), lr=lr, weight_decay=weight_decay)
    scheduler = optim.lr_scheduler.CosineAnnealingLR(
        optimizer, T_max=num_epochs, eta_min=ETA_MIN,
    )

    history: List[Dict[str, Any]] = []
    best_f1 = 0.0
    best_state: Optional[Dict[str, torch.Tensor]] = None

    for epoch in range(1, num_epochs + 1):
        epoch_started = time.time()
        train_loss, train_acc = train_one_epoch(
            head, train_loader, criterion, optimizer, device,
        )
        validation = evaluate(head, val_loader, criterion, device)
        current_lr = optimizer.param_groups[0]["lr"]
        elapsed_sec = time.time() - epoch_started
        scheduler.step()

        record = {
            "epoch": epoch,
            "train_loss": round(train_loss, 6),
            "train_acc": round(train_acc, 6),
            "val_loss": round(validation["loss"], 6),
            "val_acc": round(validation["accuracy"], 6),
            "val_precision_macro": round(validation["precision_macro"], 6),
            "val_recall_macro": round(validation["recall_macro"], 6),
            "val_f1_macro": round(validation["f1_macro"], 6),
            "lr": round(current_lr, 8),
            "elapsed_sec": round(elapsed_sec, 1),
        }
        history.append(record)

        if validation["f1_macro"] > best_f1:
            best_f1 = validation["f1_macro"]
            best_state = {
                key: value.detach().cpu().clone()
                for key, value in head.state_dict().items()
            }

    return history, best_f1, best_state


def run(
    baseline_checkpoint_path: Optional[Path] = None,
    manifest_path: Optional[Path] = None,
    mapping_path: Optional[Path] = None,
    model_dir: Optional[Path] = None,
) -> Dict[str, Any]:
    """Run one fixed-seed validation-gated head-fine-tuning experiment."""
    root = Path(__file__).resolve().parent.parent
    baseline_checkpoint_path = baseline_checkpoint_path or (
        root / "models" / "best_plantvillage_model.pt"
    )
    manifest_path = manifest_path or (
        root / "data" / "processed" / "plantvillage_manifest_clean.csv"
    )
    mapping_path = mapping_path or (
        root / "data" / "processed" / "plantvillage_class_mapping.csv"
    )
    model_dir = model_dir or (root / "models")
    checkpoint_path = model_dir / "best_plantvillage_model_v2.pt"
    history_path = model_dir / "training_history_v2.csv"

    if checkpoint_path.exists():
        raise FileExistsError(
            f"Refusing to overwrite existing v2 checkpoint: {checkpoint_path}"
        )

    train_mod = load_training_module()
    train_mod.set_seed(SEED)
    device = train_mod.get_device()
    run_started = time.time()
    print(f"Device: {device}")

    all_rows, class_to_id, _ = train_mod.load_manifest_and_mapping(
        manifest_path, mapping_path,
    )
    train_rows, val_rows, _ = train_mod.split_manifest(all_rows)
    split_counts = {
        "train": len(train_rows),
        "val": len(val_rows),
        "test": len(all_rows) - len(train_rows) - len(val_rows),
    }
    class_weights = train_mod.compute_class_weights(train_rows, class_to_id).to(device)

    baseline_checkpoint = torch.load(
        baseline_checkpoint_path, map_location=device, weights_only=False,
    )
    baseline_val_f1 = float(baseline_checkpoint["val_f1"])
    full_model = train_mod.build_model(NUM_CLASSES)
    full_model.load_state_dict(baseline_checkpoint["model_state_dict"])
    trainable_modules = configure_model_for_finetuning(full_model)
    full_model = full_model.to(device)

    # Cache frozen ResNet-18 backbone features (512-dim vectors).  This is the
    # same memory-light extraction path that the baseline training script uses.
    backbone = nn.Sequential(*list(full_model.children())[:-1], nn.Flatten()).to(device)
    backbone.eval()

    print(f"Extracting frozen backbone features for {len(train_rows)} train images...")
    train_dataset = train_mod.PlantVillageDataset(
        train_rows, class_to_id, train_mod.get_eval_transforms(),
    )
    train_features, train_labels = train_mod.extract_features(
        backbone, train_dataset, device,
    )

    print(f"Extracting frozen backbone features for {len(val_rows)} validation images...")
    val_dataset = train_mod.PlantVillageDataset(
        val_rows, class_to_id, train_mod.get_eval_transforms(),
    )
    val_features, val_labels = train_mod.extract_features(
        backbone, val_dataset, device,
    )

    train_feat_ds = train_mod.FeatureDataset(train_features, train_labels)
    val_feat_ds = train_mod.FeatureDataset(val_features, val_labels)
    generator = torch.Generator().manual_seed(SEED)
    train_loader = DataLoader(
        train_feat_ds,
        batch_size=BATCH_SIZE,
        shuffle=True,
        num_workers=0,
        generator=generator,
    )
    val_loader = DataLoader(
        val_feat_ds,
        batch_size=BATCH_SIZE,
        shuffle=False,
        num_workers=0,
    )

    criterion = nn.CrossEntropyLoss(weight=class_weights)

    best_candidate_f1 = baseline_val_f1
    best_history: List[Dict[str, Any]] = []
    best_state: Optional[Dict[str, torch.Tensor]] = None
    best_record: Optional[Dict[str, Any]] = None
    best_architecture: Optional[str] = None

    print(
        f"Fine-tuning classification head; baseline validation macro-F1={baseline_val_f1:.4f}"
    )
    for candidate in HEAD_CANDIDATES:
        arch = candidate["head_architecture"]
        print(
            f"\nTrying head={arch}, lr={candidate['lr']}, "
            f"wd={candidate['weight_decay']}, epochs={candidate['epochs']}"
        )
        head = train_mod.build_head(arch, 512, NUM_CLASSES)
        history, candidate_best_f1, candidate_state = train_candidate_head(
            head=head,
            train_loader=train_loader,
            val_loader=val_loader,
            criterion=criterion,
            lr=candidate["lr"],
            weight_decay=candidate["weight_decay"],
            num_epochs=candidate["epochs"],
            device=device,
        )
        print(
            f"  Best validation macro-F1 for {arch}: {candidate_best_f1:.4f}"
        )

        if candidate_best_f1 > best_candidate_f1:
            best_candidate_f1 = candidate_best_f1
            best_history = history
            best_state = candidate_state
            best_architecture = arch
            best_record = max(history, key=lambda row: row["val_f1_macro"])
            print(
                f"  New overall best candidate: {best_candidate_f1:.4f} ({arch})"
            )

    write_history(best_history, history_path)
    total_duration_sec = time.time() - run_started

    if best_state is not None and best_record is not None and best_architecture is not None:
        # Reconstruct the winning head on the full model before loading its weights.
        full_model.fc = train_mod.build_head(best_architecture, 512, NUM_CLASSES)
        full_model.fc.load_state_dict(best_state)
        payload = build_checkpoint_payload(
            model=full_model,
            best_record=best_record,
            baseline_checkpoint_path=baseline_checkpoint_path,
            baseline_val_f1=baseline_val_f1,
            split_counts=split_counts,
            trainable_modules=trainable_modules,
            total_duration_sec=total_duration_sec,
            head_architecture=best_architecture,
        )
        model_dir.mkdir(parents=True, exist_ok=True)
        torch.save(payload, checkpoint_path)
        saved_checkpoint: Optional[str] = str(checkpoint_path)
        print(f"Saved improved v2 checkpoint: {checkpoint_path}")
    else:
        saved_checkpoint = None
        print("No validation improvement; v2 checkpoint was not saved.")

    return {
        "history": best_history,
        "history_path": str(history_path),
        "checkpoint_path": saved_checkpoint,
        "baseline_val_f1": baseline_val_f1,
        "best_candidate_val_f1": best_candidate_f1,
        "candidate_selected": best_state is not None,
        "split_counts": split_counts,
        "device": str(device),
        "total_duration_sec": round(total_duration_sec, 1),
    }


if __name__ == "__main__":
    result = run()
    print(f"Best candidate validation macro-F1: {result['best_candidate_val_f1']:.4f}")
    print(f"Candidate selected: {result['candidate_selected']}")
