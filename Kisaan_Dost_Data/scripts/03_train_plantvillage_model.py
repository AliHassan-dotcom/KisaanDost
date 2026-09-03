"""Train a plant disease classifier on the PlantVillage dataset.

Uses a feature-extraction approach for CPU feasibility:
1. Pre-compute ResNet-18 backbone features for all images (single pass).
2. Train only the linear classification head on cached feature vectors.
3. Save a combined checkpoint (backbone + head) for downstream evaluation.

Outputs:
- ``models/best_plantvillage_model.pt`` — best model weights
- ``models/training_history.csv`` — per-epoch metrics

Stdlib + PyTorch + torchvision + sklearn + numpy.
"""

from __future__ import annotations

import csv
import os
import random
import time
from collections import Counter
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import numpy as np
import torch
import torch.nn as nn
import torch.optim as optim
from torch.utils.data import DataLoader, Dataset
from torchvision import models, transforms
from sklearn.metrics import (
    accuracy_score,
    f1_score,
    precision_score,
    recall_score,
)

SEED = 42
NUM_CLASSES = 15
BATCH_SIZE = 32
NUM_EPOCHS = 10
LEARNING_RATE = 1e-4
WEIGHT_DECAY = 1e-2
IMAGE_SIZE = 224
FEATURE_BATCH_SIZE = 64

IMAGENET_MEAN = [0.485, 0.456, 0.406]
IMAGENET_STD = [0.229, 0.224, 0.225]


def set_seed(seed: int = SEED) -> None:
    random.seed(seed)
    np.random.seed(seed)
    torch.manual_seed(seed)
    if torch.cuda.is_available():
        torch.cuda.manual_seed_all(seed)


def get_device() -> torch.device:
    if torch.cuda.is_available():
        return torch.device("cuda")
    return torch.device("cpu")


def get_eval_transforms() -> transforms.Compose:
    return transforms.Compose([
        transforms.Resize(256),
        transforms.CenterCrop(IMAGE_SIZE),
        transforms.ToTensor(),
        transforms.Normalize(mean=IMAGENET_MEAN, std=IMAGENET_STD),
    ])


def build_head(architecture: str, in_features: int, num_classes: int) -> nn.Module:
    """Build a classification head by name.

    Supported architectures:
    - ``baseline``: Dropout(0.3) + Linear(in_features, num_classes)
    - ``mlp_256``: Dropout(0.3) + Linear(in_features, 256) + ReLU +
      Dropout(0.3) + Linear(256, num_classes)
    - ``mlp_512``: Dropout(0.3) + Linear(in_features, 512) + ReLU +
      Dropout(0.3) + Linear(512, num_classes)
    """
    if architecture == "baseline":
        return nn.Sequential(
            nn.Dropout(0.3),
            nn.Linear(in_features, num_classes),
        )
    if architecture == "mlp_256":
        return nn.Sequential(
            nn.Dropout(0.3),
            nn.Linear(in_features, 256),
            nn.ReLU(),
            nn.Dropout(0.3),
            nn.Linear(256, num_classes),
        )
    if architecture == "mlp_512":
        return nn.Sequential(
            nn.Dropout(0.3),
            nn.Linear(in_features, 512),
            nn.ReLU(),
            nn.Dropout(0.3),
            nn.Linear(512, num_classes),
        )
    raise ValueError(f"Unknown head architecture: {architecture}")


def build_model(
    num_classes: int = NUM_CLASSES,
    head: Optional[nn.Module] = None,
) -> nn.Module:
    """Build ResNet-18 with a new classification head."""
    model = models.resnet18(weights=models.ResNet18_Weights.IMAGENET1K_V1)
    in_features = model.fc.in_features
    if head is None:
        head = build_head("baseline", in_features, num_classes)
    model.fc = head
    return model


def load_manifest_and_mapping(
    manifest_path: Path,
    mapping_path: Path,
) -> Tuple[List[Dict[str, str]], Dict[str, int], List[str]]:
    """Load manifest rows and build class_to_id / id_to_class mappings."""
    with manifest_path.open("r", encoding="utf-8", newline="") as fh:
        all_rows = list(csv.DictReader(fh))

    with mapping_path.open("r", encoding="utf-8", newline="") as fh:
        mapping_rows = list(csv.DictReader(fh))

    class_to_id: Dict[str, int] = {}
    id_to_class: List[str] = []
    for m in mapping_rows:
        cid = int(m["class_id"])
        cname = m["class_name"]
        class_to_id[cname] = cid
        id_to_class.append(cname)

    id_to_class.sort(key=lambda c: class_to_id[c])
    return all_rows, class_to_id, id_to_class


def split_manifest(
    all_rows: List[Dict[str, str]],
) -> Tuple[List[Dict[str, str]], List[Dict[str, str]], List[Dict[str, str]]]:
    """Split rows by the saved split column."""
    train, val, test = [], [], []
    for row in all_rows:
        if row["split"] == "train":
            train.append(row)
        elif row["split"] == "val":
            val.append(row)
        elif row["split"] == "test":
            test.append(row)
    return train, val, test


def compute_class_weights(
    train_rows: List[Dict[str, str]],
    class_to_id: Dict[str, int],
) -> torch.Tensor:
    """Compute inverse-frequency class weights."""
    counts = Counter(row["class_name"] for row in train_rows)
    total = len(train_rows)
    n_classes = len(class_to_id)
    weights = []
    for class_name, class_id in sorted(class_to_id.items(), key=lambda x: x[1]):
        count = counts.get(class_name, 1)
        w = total / (n_classes * count)
        weights.append(w)
    return torch.tensor(weights, dtype=torch.float32)


class PlantVillageDataset(Dataset):
    """Image-based dataset (kept for evaluation script compatibility)."""

    def __init__(
        self,
        manifest_rows: List[Dict[str, str]],
        class_to_id: Dict[str, int],
        transform: Optional[transforms.Compose] = None,
    ):
        self.rows = manifest_rows
        self.class_to_id = class_to_id
        self.transform = transform

    def __len__(self) -> int:
        return len(self.rows)

    def __getitem__(self, idx: int) -> Tuple[torch.Tensor, int]:
        from PIL import Image

        row = self.rows[idx]
        img_path = row["image_path"]
        label = self.class_to_id[row["class_name"]]

        img = Image.open(img_path).convert("RGB")
        if self.transform:
            img = self.transform(img)

        return img, label


@torch.no_grad()
def extract_features(
    backbone: nn.Module,
    dataset: Dataset,
    device: torch.device,
    batch_size: int = FEATURE_BATCH_SIZE,
) -> Tuple[torch.Tensor, torch.Tensor]:
    """Run the frozen backbone over all images and return (features, labels)."""
    backbone.eval()
    loader = DataLoader(
        dataset, batch_size=batch_size, shuffle=False,
        num_workers=0, pin_memory=False,
    )

    all_features: List[torch.Tensor] = []
    all_labels: List[torch.Tensor] = []

    for batch_idx, (images, labels) in enumerate(loader):
        images = images.to(device)
        features = backbone(images)
        all_features.append(features.cpu())
        all_labels.append(labels)

        if (batch_idx + 1) % 50 == 0:
            print(f"    Extracted {len(all_features) * batch_size} / {len(dataset)}")

    features_tensor = torch.cat(all_features, dim=0)
    labels_tensor = torch.cat(all_labels, dim=0)
    print(f"    Extracted {len(dataset)} feature vectors")
    return features_tensor, labels_tensor


class FeatureDataset(Dataset):
    """Dataset backed by pre-computed feature vectors."""

    def __init__(self, features: torch.Tensor, labels: torch.Tensor):
        self.features = features
        self.labels = labels

    def __len__(self) -> int:
        return len(self.labels)

    def __getitem__(self, idx: int) -> Tuple[torch.Tensor, int]:
        return self.features[idx], self.labels[idx].item()


def train_head_one_epoch(
    head: nn.Module,
    loader: DataLoader,
    criterion: nn.Module,
    optimizer: optim.Optimizer,
    device: torch.device,
) -> Tuple[float, float]:
    head.train()
    running_loss = 0.0
    all_preds: List[int] = []
    all_labels: List[int] = []

    for features, labels in loader:
        features = features.to(device)
        labels = labels.to(device)

        optimizer.zero_grad()
        outputs = head(features)
        loss = criterion(outputs, labels)
        loss.backward()
        optimizer.step()

        running_loss += loss.item() * features.size(0)
        preds = outputs.argmax(dim=1).cpu().tolist()
        all_preds.extend(preds)
        all_labels.extend(labels.cpu().tolist())

    epoch_loss = running_loss / len(loader.dataset)
    epoch_acc = accuracy_score(all_labels, all_preds)
    return epoch_loss, epoch_acc


@torch.no_grad()
def eval_head(
    head: nn.Module,
    loader: DataLoader,
    criterion: nn.Module,
    device: torch.device,
) -> Tuple[float, float, float]:
    head.eval()
    running_loss = 0.0
    all_preds: List[int] = []
    all_labels: List[int] = []

    for features, labels in loader:
        features = features.to(device)
        labels = labels.to(device)

        outputs = head(features)
        loss = criterion(outputs, labels)

        running_loss += loss.item() * features.size(0)
        preds = outputs.argmax(dim=1).cpu().tolist()
        all_preds.extend(preds)
        all_labels.extend(labels.cpu().tolist())

    epoch_loss = running_loss / len(loader.dataset)
    epoch_acc = accuracy_score(all_labels, all_preds)
    epoch_f1 = f1_score(all_labels, all_preds, average="macro", zero_division=0)
    return epoch_loss, epoch_acc, epoch_f1


def run(
    manifest_path: Optional[Path] = None,
    mapping_path: Optional[Path] = None,
    model_dir: Optional[Path] = None,
    num_epochs: int = NUM_EPOCHS,
) -> Dict[str, Any]:
    """Full feature-extraction training pipeline."""
    root = Path(__file__).resolve().parent.parent
    manifest_path = manifest_path or (root / "data" / "processed" / "plantvillage_manifest_clean.csv")
    mapping_path = mapping_path or (root / "data" / "processed" / "plantvillage_class_mapping.csv")
    model_dir = model_dir or (root / "models")

    set_seed(SEED)
    torch.set_num_threads(min(os.cpu_count() or 4, 16))
    device = get_device()
    print(f"Device: {device}")

    print("Loading manifest and class mapping...")
    all_rows, class_to_id, id_to_class = load_manifest_and_mapping(manifest_path, mapping_path)
    print(f"  {len(all_rows)} total rows, {len(class_to_id)} classes")

    print("Splitting manifest...")
    train_rows, val_rows, test_rows = split_manifest(all_rows)
    print(f"  Train: {len(train_rows)}, Val: {len(val_rows)}, Test: {len(test_rows)}")

    print("Computing class weights...")
    class_weights = compute_class_weights(train_rows, class_to_id)
    class_weights = class_weights.to(device)
    print(f"  Weights: {class_weights.tolist()}")

    # Phase 1: Feature extraction (single pass through frozen backbone)
    print("\n=== Phase 1: Feature extraction (ResNet-18 backbone) ===")
    print("Building backbone...")
    full_model = build_model(NUM_CLASSES)
    backbone = nn.Sequential(*list(full_model.children())[:-1], nn.Flatten())
    backbone = backbone.to(device)
    backbone.eval()
    print(f"  Backbone output dim: 512")

    eval_tf = get_eval_transforms()

    print(f"Extracting train features ({len(train_rows)} images)...")
    train_ds = PlantVillageDataset(train_rows, class_to_id, eval_tf)
    t0 = time.time()
    train_feats, train_labs = extract_features(backbone, train_ds, device)
    t1 = time.time()
    print(f"  Train features: {train_feats.shape} in {t1 - t0:.1f}s")

    print(f"Extracting val features ({len(val_rows)} images)...")
    val_ds = PlantVillageDataset(val_rows, class_to_id, eval_tf)
    val_feats, val_labs = extract_features(backbone, val_ds, device)
    t2 = time.time()
    print(f"  Val features: {val_feats.shape} in {t2 - t1:.1f}s")

    extraction_time = t2 - t0
    print(f"  Total extraction time: {extraction_time:.1f}s")

    del backbone, full_model

    # Phase 2: Train classification head on cached features
    print(f"\n=== Phase 2: Training classification head ({num_epochs} epochs) ===")
    train_feat_ds = FeatureDataset(train_feats, train_labs)
    val_feat_ds = FeatureDataset(val_feats, val_labs)

    train_loader = DataLoader(
        train_feat_ds, batch_size=BATCH_SIZE, shuffle=True, num_workers=0,
    )
    val_loader = DataLoader(
        val_feat_ds, batch_size=BATCH_SIZE, shuffle=False, num_workers=0,
    )

    feature_dim = train_feats.shape[1]
    head = nn.Sequential(
        nn.Dropout(0.3),
        nn.Linear(feature_dim, NUM_CLASSES),
    ).to(device)

    criterion = nn.CrossEntropyLoss(weight=class_weights)
    optimizer = optim.AdamW(head.parameters(), lr=LEARNING_RATE, weight_decay=WEIGHT_DECAY)
    scheduler = optim.lr_scheduler.CosineAnnealingLR(optimizer, T_max=num_epochs, eta_min=1e-6)

    best_val_f1 = 0.0
    best_epoch = 0
    best_head_state = None
    history: List[Dict[str, Any]] = []

    t_train_start = time.time()
    for epoch in range(1, num_epochs + 1):
        epoch_start = time.time()

        train_loss, train_acc = train_head_one_epoch(
            head, train_loader, criterion, optimizer, device,
        )
        val_loss, val_acc, val_f1 = eval_head(
            head, val_loader, criterion, device,
        )

        current_lr = optimizer.param_groups[0]["lr"]
        scheduler.step()
        elapsed = time.time() - epoch_start

        record = {
            "epoch": epoch,
            "train_loss": round(train_loss, 6),
            "train_acc": round(train_acc, 6),
            "val_loss": round(val_loss, 6),
            "val_acc": round(val_acc, 6),
            "val_f1": round(val_f1, 6),
            "lr": round(current_lr, 8),
            "elapsed_sec": round(elapsed, 1),
        }
        history.append(record)

        print(
            f"  Epoch {epoch}/{num_epochs}: "
            f"train_loss={train_loss:.4f} train_acc={train_acc:.4f} | "
            f"val_loss={val_loss:.4f} val_acc={val_acc:.4f} val_f1={val_f1:.4f} | "
            f"lr={current_lr:.6f} | {elapsed:.1f}s"
        )

        if val_f1 > best_val_f1:
            best_val_f1 = val_f1
            best_epoch = epoch
            best_head_state = {k: v.cpu().clone() for k, v in head.state_dict().items()}
            print(f"  -> New best val_f1={val_f1:.4f}")

    head_training_time = time.time() - t_train_start
    print(f"  Head training time: {head_training_time:.1f}s")

    # Phase 3: Save combined checkpoint (backbone + head)
    print("\n=== Phase 3: Saving checkpoint ===")
    combined_model = build_model(NUM_CLASSES)
    combined_state = combined_model.state_dict()
    for key, value in best_head_state.items():
        combined_state[f"fc.{key}"] = value
    combined_model.load_state_dict(combined_state)

    checkpoint_path = model_dir / "best_plantvillage_model.pt"
    checkpoint_path.parent.mkdir(parents=True, exist_ok=True)
    torch.save({
        "epoch": best_epoch,
        "model_state_dict": combined_model.state_dict(),
        "val_f1": best_val_f1,
        "val_acc": max(h["val_acc"] for h in history),
        "num_classes": NUM_CLASSES,
        "training_duration_sec": round(total_elapsed, 1),
        "feature_extraction_sec": round(extraction_time, 1),
        "head_training_sec": round(head_training_time, 1),
        "training_approach": "feature_extraction",
    }, checkpoint_path)
    print(f"  Checkpoint: {checkpoint_path}")

    history_path = model_dir / "training_history.csv"
    with history_path.open("w", encoding="utf-8", newline="") as fh:
        writer = csv.DictWriter(
            fh,
            fieldnames=["epoch", "train_loss", "train_acc", "val_loss", "val_acc", "val_f1", "lr", "elapsed_sec"],
            lineterminator="\n",
        )
        writer.writeheader()
        writer.writerows(history)
    print(f"  History: {history_path}")

    total_elapsed = time.time() - t0
    result = {
        "history": history,
        "best_epoch": best_epoch,
        "best_val_f1": best_val_f1,
        "best_val_acc": max(h["val_acc"] for h in history),
        "train_count": len(train_rows),
        "val_count": len(val_rows),
        "test_count": len(test_rows),
        "num_classes": NUM_CLASSES,
        "checkpoint_path": str(checkpoint_path),
        "history_path": str(history_path),
        "device": str(device),
        "total_elapsed_sec": round(total_elapsed, 1),
        "extraction_sec": round(extraction_time, 1),
        "head_training_sec": round(head_training_time, 1),
        "id_to_class": id_to_class,
        "class_to_id": class_to_id,
    }

    print(f"\nTraining complete in {total_elapsed:.1f}s")
    print(f"  Feature extraction: {extraction_time:.1f}s")
    print(f"  Head training: {head_training_time:.1f}s")
    print(f"  Best epoch: {best_epoch}")
    print(f"  Best val F1: {best_val_f1:.4f}")

    return result


if __name__ == "__main__":
    result = run()
