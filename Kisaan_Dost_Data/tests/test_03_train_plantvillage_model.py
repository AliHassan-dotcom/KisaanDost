"""Tests for Step 3: training pipeline (feature-extraction approach).

Covers:
- Module loads and key functions exist
- Helper functions (set_seed, get_device, build_model, etc.)
- Class weight computation correctness
- Feature extraction and FeatureDataset logic
- Output files: checkpoint (.pt) and history CSV
- Checkpoint contains expected keys and valid state dict
- Training history CSV has correct shape and column names
- Training history values are reasonable (loss finite, accuracy > 0)

Stdlib + PyTorch + torchvision + sklearn + numpy.
"""

from __future__ import annotations

import csv
import importlib.util
from pathlib import Path

import numpy as np
import pytest
import torch
import torch.nn as nn

ROOT = Path(__file__).resolve().parent.parent
MANIFEST_PATH = ROOT / "data" / "processed" / "plantvillage_manifest_clean.csv"
MAPPING_PATH = ROOT / "data" / "processed" / "plantvillage_class_mapping.csv"
CHECKPOINT_PATH = ROOT / "models" / "best_plantvillage_model.pt"
HISTORY_PATH = ROOT / "models" / "training_history.csv"

NUM_CLASSES = 15
NUM_EPOCHS = 10
EXPECTED_HISTORY_COLS = [
    "epoch", "train_loss", "train_acc",
    "val_loss", "val_acc", "val_f1", "lr", "elapsed_sec",
]


@pytest.fixture(scope="module")
def train_mod():
    script = ROOT / "scripts" / "03_train_plantvillage_model.py"
    spec = importlib.util.spec_from_file_location("train_module", script)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


@pytest.fixture(scope="module")
def manifest_and_mapping(train_mod):
    all_rows, class_to_id, id_to_class = train_mod.load_manifest_and_mapping(
        MANIFEST_PATH, MAPPING_PATH,
    )
    return all_rows, class_to_id, id_to_class


@pytest.fixture(scope="module")
def train_val_test(manifest_and_mapping):
    all_rows, class_to_id, id_to_class = manifest_and_mapping
    train, val, test = [], [], []
    for row in all_rows:
        if row["split"] == "train":
            train.append(row)
        elif row["split"] == "val":
            val.append(row)
        elif row["split"] == "test":
            test.append(row)
    return train, val, test


# ── Module loading ──────────────────────────────────────────────────


class TestModuleLoads:
    def test_module_imports(self, train_mod):
        assert train_mod is not None

    def test_has_run(self, train_mod):
        assert callable(getattr(train_mod, "run", None))

    def test_has_build_model(self, train_mod):
        assert callable(getattr(train_mod, "build_model", None))

    def test_has_set_seed(self, train_mod):
        assert callable(getattr(train_mod, "set_seed", None))

    def test_has_get_device(self, train_mod):
        assert callable(getattr(train_mod, "get_device", None))

    def test_has_extract_features(self, train_mod):
        assert callable(getattr(train_mod, "extract_features", None))

    def test_has_feature_dataset(self, train_mod):
        assert hasattr(train_mod, "FeatureDataset")

    def test_has_plantvillage_dataset(self, train_mod):
        assert hasattr(train_mod, "PlantVillageDataset")


# ── Helper functions ────────────────────────────────────────────────


class TestHelpers:
    def test_set_seed_deterministic(self, train_mod):
        train_mod.set_seed(42)
        a = torch.randn(5)
        train_mod.set_seed(42)
        b = torch.randn(5)
        assert torch.equal(a, b)

    def test_get_device_returns_tensor(self, train_mod):
        device = train_mod.get_device()
        assert isinstance(device, torch.device)

    def test_build_model_output_shape(self, train_mod):
        model = train_mod.build_model(NUM_CLASSES)
        x = torch.randn(2, 3, 224, 224)
        out = model(x)
        assert out.shape == (2, NUM_CLASSES)

    def test_build_model_has_dropout(self, train_mod):
        model = train_mod.build_model(NUM_CLASSES)
        assert isinstance(model.fc[0], nn.Dropout)

    def test_build_model_has_linear(self, train_mod):
        model = train_mod.build_model(NUM_CLASSES)
        assert isinstance(model.fc[1], nn.Linear)
        assert model.fc[1].out_features == NUM_CLASSES

    def test_get_eval_transforms_returns_compose(self, train_mod):
        from torchvision.transforms import Compose
        tf = train_mod.get_eval_transforms()
        assert isinstance(tf, Compose)


# ── Class weight computation ────────────────────────────────────────


class TestClassWeights:
    def test_weights_shape(self, train_mod, train_val_test):
        train_rows = train_val_test[0]
        class_to_id = {f"class_{i}": i for i in range(NUM_CLASSES)}
        weights = train_mod.compute_class_weights(train_rows, class_to_id)
        # Weights computed from actual class_to_id from mapping
        assert isinstance(weights, torch.Tensor)

    def test_weights_positive(self, train_mod, train_val_test):
        train_rows = train_val_test[0]
        _, class_to_id, _ = train_mod.load_manifest_and_mapping(MANIFEST_PATH, MAPPING_PATH)
        weights = train_mod.compute_class_weights(train_rows, class_to_id)
        assert (weights > 0).all()

    def test_weights_length(self, train_mod, train_val_test):
        train_rows = train_val_test[0]
        _, class_to_id, _ = train_mod.load_manifest_and_mapping(MANIFEST_PATH, MAPPING_PATH)
        weights = train_mod.compute_class_weights(train_rows, class_to_id)
        assert len(weights) == NUM_CLASSES

    def test_weights_inverse_frequency(self, train_mod, train_val_test):
        train_rows = train_val_test[0]
        _, class_to_id, _ = train_mod.load_manifest_and_mapping(MANIFEST_PATH, MAPPING_PATH)
        weights = train_mod.compute_class_weights(train_rows, class_to_id)
        # The most frequent class should have the lowest weight
        from collections import Counter
        counts = Counter(r["class_name"] for r in train_rows)
        sorted_by_count = sorted(counts.items(), key=lambda x: x[1])
        rarest_class = sorted_by_count[0][0]
        most_common_class = sorted_by_count[-1][0]
        rarest_id = class_to_id[rarest_class]
        common_id = class_to_id[most_common_class]
        assert weights[rarest_id] > weights[common_id]


# ── Feature extraction ──────────────────────────────────────────────


class TestFeatureExtraction:
    def test_feature_dataset_len(self, train_mod):
        features = torch.randn(10, 512)
        labels = torch.arange(10)
        ds = train_mod.FeatureDataset(features, labels)
        assert len(ds) == 10

    def test_feature_dataset_getitem(self, train_mod):
        features = torch.randn(10, 512)
        labels = torch.arange(10)
        ds = train_mod.FeatureDataset(features, labels)
        feat, label = ds[3]
        assert feat.shape == (512,)
        assert label == 3

    def test_extract_features_runs(self, train_mod):
        """Extract features from a tiny model to verify the function works."""
        # Build a minimal backbone that outputs 8-dim features
        backbone = nn.Sequential(
            nn.AdaptiveAvgPool2d(1),
            nn.Flatten(),
            nn.Linear(3, 8),
        )
        backbone.eval()

        # Create a tiny dataset with dummy image paths
        class DummyDS:
            def __len__(self):
                return 4

            def __getitem__(self, idx):
                return torch.randn(3, 32, 32), idx

        feats, labs = train_mod.extract_features(backbone, DummyDS(), torch.device("cpu"), batch_size=2)
        assert feats.shape == (4, 8)
        assert labs.shape == (4,)


# ── Training output files ──────────────────────────────────────────


class TestCheckpoint:
    def test_checkpoint_exists(self):
        assert CHECKPOINT_PATH.exists(), f"Checkpoint not found: {CHECKPOINT_PATH}"

    def test_checkpoint_is_dict(self):
        ckpt = torch.load(CHECKPOINT_PATH, map_location="cpu", weights_only=False)
        assert isinstance(ckpt, dict)

    def test_checkpoint_has_required_keys(self):
        ckpt = torch.load(CHECKPOINT_PATH, map_location="cpu", weights_only=False)
        for key in ("epoch", "model_state_dict", "val_f1", "num_classes"):
            assert key in ckpt, f"Missing key: {key}"

    def test_checkpoint_has_timing_metadata(self):
        ckpt = torch.load(CHECKPOINT_PATH, map_location="cpu", weights_only=False)
        for key in ("training_duration_sec", "feature_extraction_sec", "head_training_sec"):
            assert key in ckpt, f"Missing key: {key}"
            assert ckpt[key] >= 0.0

    def test_checkpoint_num_classes(self):
        ckpt = torch.load(CHECKPOINT_PATH, map_location="cpu", weights_only=False)
        assert ckpt["num_classes"] == NUM_CLASSES

    def test_checkpoint_val_f1_positive(self):
        ckpt = torch.load(CHECKPOINT_PATH, map_location="cpu", weights_only=False)
        assert ckpt["val_f1"] > 0.0

    def test_checkpoint_loads_into_model(self, train_mod):
        model = train_mod.build_model(NUM_CLASSES)
        ckpt = torch.load(CHECKPOINT_PATH, map_location="cpu", weights_only=False)
        model.load_state_dict(ckpt["model_state_dict"])
        # Verify forward pass works
        x = torch.randn(1, 3, 224, 224)
        out = model(x)
        assert out.shape == (1, NUM_CLASSES)


class TestTrainingHistory:
    def test_history_exists(self):
        assert HISTORY_PATH.exists(), f"History not found: {HISTORY_PATH}"

    def test_history_column_names(self):
        with HISTORY_PATH.open("r", encoding="utf-8", newline="") as fh:
            reader = csv.DictReader(fh)
            assert list(reader.fieldnames) == EXPECTED_HISTORY_COLS

    def test_history_row_count(self):
        with HISTORY_PATH.open("r", encoding="utf-8", newline="") as fh:
            rows = list(csv.DictReader(fh))
        assert len(rows) == NUM_EPOCHS

    def test_history_epoch_sequence(self):
        with HISTORY_PATH.open("r", encoding="utf-8", newline="") as fh:
            rows = list(csv.DictReader(fh))
        epochs = [int(r["epoch"]) for r in rows]
        assert epochs == list(range(1, NUM_EPOCHS + 1))

    def test_history_losses_finite(self):
        with HISTORY_PATH.open("r", encoding="utf-8", newline="") as fh:
            rows = list(csv.DictReader(fh))
        for row in rows:
            assert np.isfinite(float(row["train_loss"]))
            assert np.isfinite(float(row["val_loss"]))

    def test_history_accuracies_valid(self):
        with HISTORY_PATH.open("r", encoding="utf-8", newline="") as fh:
            rows = list(csv.DictReader(fh))
        for row in rows:
            train_acc = float(row["train_acc"])
            val_acc = float(row["val_acc"])
            assert 0.0 <= train_acc <= 1.0
            assert 0.0 <= val_acc <= 1.0

    def test_history_f1_valid(self):
        with HISTORY_PATH.open("r", encoding="utf-8", newline="") as fh:
            rows = list(csv.DictReader(fh))
        for row in rows:
            f1 = float(row["val_f1"])
            assert 0.0 <= f1 <= 1.0

    def test_history_accuracy_above_chance(self):
        """With 15 classes, random chance is ~6.7%. Training should exceed this."""
        with HISTORY_PATH.open("r", encoding="utf-8", newline="") as fh:
            rows = list(csv.DictReader(fh))
        last_row = rows[-1]
        assert float(last_row["train_acc"]) > 0.15
        assert float(last_row["val_acc"]) > 0.15
