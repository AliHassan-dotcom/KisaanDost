"""Disease model inference interface.

Loads ``models/best_plantvillage_model_v2.pt`` only; never trains.
Returns predicted class, confidence, model version, and an uncertainty warning
when confidence is below the configured threshold.
"""

from __future__ import annotations

import csv
from pathlib import Path
from typing import Dict, List, Optional, Tuple

import torch
import torch.nn as nn
from PIL import Image
from torchvision import models, transforms

from app.config import settings

_NUM_CLASSES = 15
_IMAGE_SIZE = 224

_IMAGENET_MEAN = [0.485, 0.456, 0.406]
_IMAGENET_STD = [0.229, 0.224, 0.225]

_eval_transform = transforms.Compose(
    [
        transforms.Resize(256),
        transforms.CenterCrop(_IMAGE_SIZE),
        transforms.ToTensor(),
        transforms.Normalize(mean=_IMAGENET_MEAN, std=_IMAGENET_STD),
    ]
)

_model: Optional[nn.Module] = None
_id_to_class: Optional[List[str]] = None
_model_version: Optional[str] = None


def _build_head(architecture: str, in_features: int, num_classes: int) -> nn.Module:
    if architecture == "baseline":
        return nn.Sequential(nn.Dropout(0.3), nn.Linear(in_features, num_classes))
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


def _load_class_mapping(path: Path) -> List[str]:
    id_to_class = [""] * _NUM_CLASSES
    with open(path, "r", encoding="utf-8", newline="") as fh:
        for row in csv.DictReader(fh):
            class_id = int(row["class_id"])
            id_to_class[class_id] = row["class_name"]
    return id_to_class


def reset_cached_model() -> None:
    """Reset the module-level cached model (used for isolated testing)."""
    global _model, _id_to_class, _model_version
    _model = None
    _id_to_class = None
    _model_version = None


def load_model() -> Tuple[nn.Module, List[str], str]:
    """Lazy-load the v2 model and class mapping once per process."""
    global _model, _id_to_class, _model_version
    if _model is None:
        checkpoint_path = settings.model_full_path()
        if not checkpoint_path.exists():
            raise FileNotFoundError(f"Model checkpoint not found: {checkpoint_path}")
        if not checkpoint_path.is_file():
            raise FileNotFoundError(f"Model checkpoint is not a regular file: {checkpoint_path}")

        resolved_root = settings.project_root.resolve()
        try:
            checkpoint_path.resolve().relative_to(resolved_root)
        except ValueError:
            raise PermissionError(f"Model checkpoint path is outside trusted project directory: {checkpoint_path}")

        mapping_path = settings.class_mapping_full_path()
        if not mapping_path.exists():
            raise FileNotFoundError(f"Class mapping not found: {mapping_path}")
        if not mapping_path.is_file():
            raise FileNotFoundError(f"Class mapping is not a regular file: {mapping_path}")
        try:
            mapping_path.resolve().relative_to(resolved_root)
        except ValueError:
            raise PermissionError(f"Class mapping path is outside trusted project directory: {mapping_path}")

        checkpoint = torch.load(checkpoint_path, map_location="cpu", weights_only=False)
        if not isinstance(checkpoint, dict) or "model_state_dict" not in checkpoint:
            raise ValueError("Invalid checkpoint: missing model_state_dict")

        head_architecture = checkpoint.get("head_architecture") or "baseline"
        num_classes = checkpoint.get("num_classes", _NUM_CLASSES)

        model = models.resnet18(weights=None)
        in_features = model.fc.in_features
        model.fc = _build_head(head_architecture, in_features, num_classes)
        model.load_state_dict(checkpoint["model_state_dict"])
        model.eval()

        id_to_class = _load_class_mapping(mapping_path)

        _model = model
        _id_to_class = id_to_class
        if head_architecture and head_architecture not in ("baseline", "default"):
            _model_version = f"plantvillage_v2_{head_architecture}"
        else:
            _model_version = "plantvillage_v2"

    return _model, _id_to_class, _model_version or "plantvillage_v2"


@torch.no_grad()
def predict(image_path: Path) -> Dict[str, object]:
    """Run inference on a local image file and return a safe result dict."""
    model, id_to_class, version = load_model()
    image = Image.open(image_path).convert("RGB")
    tensor = _eval_transform(image).unsqueeze(0)
    outputs = model(tensor)
    probabilities = torch.softmax(outputs, dim=1).squeeze(0)
    confidence, predicted_id = torch.max(probabilities, dim=0)
    confidence_val = float(confidence.item())
    predicted_id_val = int(predicted_id.item())
    class_name = id_to_class[predicted_id_val]

    return {
        "predicted_class": class_name,
        "confidence": round(confidence_val, 4),
        "class_id": predicted_id_val,
        "model_version": version,
        "uncertain": confidence_val < settings.confidence_threshold,
        "warning": (
            "Low confidence prediction. Please consult an extension worker for confirmation."
            if confidence_val < settings.confidence_threshold
            else None
        ),
    }
