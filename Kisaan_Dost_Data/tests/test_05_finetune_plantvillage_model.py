"""Tests for the validation-gated PlantVillage v2 head-fine-tuning module."""

from __future__ import annotations

import csv
import importlib.util
from pathlib import Path

import pytest
import torch
import torch.nn as nn
from torchvision import transforms

ROOT = Path(__file__).resolve().parent.parent
EXPECTED_HISTORY_FIELDS = [
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


@pytest.fixture(scope="module")
def finetune_mod():
    script = ROOT / "scripts" / "05_finetune_plantvillage_model.py"
    spec = importlib.util.spec_from_file_location("finetune_module", script)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class TestModuleContract:
    def test_module_imports(self, finetune_mod):
        assert finetune_mod is not None

    def test_has_run(self, finetune_mod):
        assert callable(finetune_mod.run)

    def test_has_validation_gate(self, finetune_mod):
        assert callable(finetune_mod.should_save_candidate)

    def test_has_finetune_configuration(self, finetune_mod):
        assert callable(finetune_mod.configure_model_for_finetuning)

    def test_has_history_writer(self, finetune_mod):
        assert callable(finetune_mod.write_history)


class TestFineTuningSetup:
    def test_train_transform_is_compose(self, finetune_mod):
        assert isinstance(finetune_mod.get_train_transforms(), transforms.Compose)

    def test_train_transform_has_realistic_augmentation(self, finetune_mod):
        transform_types = {
            type(transform)
            for transform in finetune_mod.get_train_transforms().transforms
        }
        assert transforms.RandomResizedCrop in transform_types
        assert transforms.RandomHorizontalFlip in transform_types
        assert transforms.RandomRotation in transform_types
        assert transforms.RandomAffine in transform_types
        assert transforms.ColorJitter in transform_types

    def test_only_fc_is_trainable(self, finetune_mod):
        train_mod = finetune_mod.load_training_module()
        model = train_mod.build_model(finetune_mod.NUM_CLASSES)
        assert finetune_mod.configure_model_for_finetuning(model) == ["fc"]
        for name, parameter in model.named_parameters():
            assert parameter.requires_grad == name.startswith("fc.")


class TestValidationGate:
    def test_requires_strict_improvement(self, finetune_mod):
        assert finetune_mod.should_save_candidate(0.8333, 0.8332)

    def test_rejects_equal_score(self, finetune_mod):
        assert not finetune_mod.should_save_candidate(0.8332, 0.8332)

    def test_rejects_lower_score(self, finetune_mod):
        assert not finetune_mod.should_save_candidate(0.8331, 0.8332)


class TestEvaluationMetrics:
    def test_evaluate_returns_macro_metrics(self, finetune_mod):
        features = torch.tensor([[3.0, 0.0], [0.0, 3.0]])
        labels = torch.tensor([0, 1])
        loader = torch.utils.data.DataLoader(
            torch.utils.data.TensorDataset(features, labels), batch_size=2,
        )
        model = nn.Identity()
        metrics = finetune_mod.evaluate(
            model,
            loader,
            nn.CrossEntropyLoss(),
            torch.device("cpu"),
        )
        assert metrics["accuracy"] == 1.0
        assert metrics["f1_macro"] == 1.0
        assert metrics["precision_macro"] == 1.0
        assert metrics["recall_macro"] == 1.0


class TestOutputs:
    def test_history_schema(self, finetune_mod, tmp_path):
        record = {
            "epoch": 1,
            "train_loss": 1.0,
            "train_acc": 0.5,
            "val_loss": 0.9,
            "val_acc": 0.6,
            "val_precision_macro": 0.6,
            "val_recall_macro": 0.6,
            "val_f1_macro": 0.6,
            "lr": 0.0001,
            "elapsed_sec": 3.0,
        }
        output_path = tmp_path / "history.csv"
        finetune_mod.write_history([record], output_path)
        with output_path.open("r", encoding="utf-8", newline="") as handle:
            reader = csv.DictReader(handle)
            assert reader.fieldnames == EXPECTED_HISTORY_FIELDS
            assert list(reader)[0]["val_f1_macro"] == "0.6"

    def test_checkpoint_payload_has_provenance(self, finetune_mod, tmp_path):
        model = nn.Linear(2, 2)
        record = {
            "epoch": 3,
            "val_f1_macro": 0.9,
            "val_acc": 0.9,
            "val_precision_macro": 0.9,
            "val_recall_macro": 0.9,
        }
        payload = finetune_mod.build_checkpoint_payload(
            model,
            record,
            tmp_path / "baseline.pt",
            0.8,
            {"train": 7, "val": 2, "test": 1},
            ["fc"],
            12.3,
            "mlp_256",
        )
        for key in (
            "model_state_dict",
            "baseline_checkpoint_path",
            "baseline_val_f1",
            "selection_metric",
            "trainable_modules",
            "split_counts",
            "seed",
            "head_architecture",
        ):
            assert key in payload
        assert payload["selection_metric"] == "validation_macro_f1"
        assert payload["baseline_val_f1"] == 0.8
        assert payload["head_architecture"] == "mlp_256"
