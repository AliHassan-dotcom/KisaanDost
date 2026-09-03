"""Tests for the unified manifest cleanup module.

Covers:
- Module loads and exposes key functions
- Citrus crop override logic
- Duplicate detection and cluster ID assignment
- De-duplicated manifest generation
- Duplicate audit table construction
- Clean label mapping generation
- Report writing
- Ambiguous label detection
"""

from __future__ import annotations

import csv
import importlib.util
from pathlib import Path
from typing import List

import pytest

ROOT = Path(__file__).resolve().parent.parent


@pytest.fixture(scope="module")
def cleanup_mod():
    script = ROOT / "scripts" / "02_cleanup_unified_manifest.py"
    spec = importlib.util.spec_from_file_location("cleanup_module", script)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


# ── Module loading ──────────────────────────────────────────────────


class TestModuleLoads:
    def test_module_imports(self, cleanup_mod):
        assert cleanup_mod is not None

    def test_has_run(self, cleanup_mod):
        assert callable(cleanup_mod.run)

    def test_has_apply_citrus_override(self, cleanup_mod):
        assert callable(cleanup_mod.apply_citrus_override)

    def test_has_assign_duplicate_cluster_ids(self, cleanup_mod):
        assert callable(cleanup_mod.assign_duplicate_cluster_ids)

    def test_has_deduplicate_manifest(self, cleanup_mod):
        assert callable(cleanup_mod.deduplicate_manifest)

    def test_has_build_duplicate_audit(self, cleanup_mod):
        assert callable(cleanup_mod.build_duplicate_audit)

    def test_has_build_label_mapping(self, cleanup_mod):
        assert callable(cleanup_mod.build_label_mapping)


# ── Citrus override ─────────────────────────────────────────────────


class TestCitrusOverride:
    def test_healthy_folder(self, cleanup_mod):
        rows = [
            {
                "source_dataset": "Citrus Leaves",
                "source_class_name": "healthy",
                "crop": "Healthy",
                "disease": "",
                "canonical_label": "Healthy__healthy",
                "is_healthy": "True",
            },
        ]
        result = cleanup_mod.apply_citrus_override(rows)
        assert result[0]["crop"] == "citrus"
        assert result[0]["disease"] == "healthy"
        assert result[0]["canonical_label"] == "citrus_healthy"
        assert result[0]["is_healthy"] == "True"

    def test_disease_folder(self, cleanup_mod):
        rows = [
            {
                "source_dataset": "Citrus Leaves",
                "source_class_name": "Black spot",
                "crop": "Black",
                "disease": "Spot",
                "canonical_label": "Black__Spot",
                "is_healthy": "False",
            },
        ]
        result = cleanup_mod.apply_citrus_override(rows)
        assert result[0]["crop"] == "citrus"
        assert result[0]["disease"] == "black spot"
        assert result[0]["canonical_label"] == "citrus_black_spot"
        assert result[0]["is_healthy"] == "False"

    def test_non_citrus_unchanged(self, cleanup_mod):
        rows = [
            {
                "source_dataset": "PlantVillage",
                "source_class_name": "Tomato_Bacterial_spot",
                "crop": "Tomato",
                "disease": "Bacterial Spot",
                "canonical_label": "Tomato__Bacterial Spot",
                "is_healthy": "False",
            },
        ]
        result = cleanup_mod.apply_citrus_override(rows)
        assert result[0]["crop"] == "Tomato"
        assert result[0]["canonical_label"] == "Tomato__Bacterial Spot"

    def test_melanose_folder(self, cleanup_mod):
        rows = [
            {
                "source_dataset": "Citrus Leaves",
                "source_class_name": "Melanose",
                "crop": "Melanose",
                "disease": "",
                "canonical_label": "Melanose",
                "is_healthy": "False",
            },
        ]
        result = cleanup_mod.apply_citrus_override(rows)
        assert result[0]["crop"] == "citrus"
        assert result[0]["canonical_label"] == "citrus_melanose"


# ── Duplicate detection ─────────────────────────────────────────────


class TestDuplicateDetection:
    def test_no_duplicates(self, cleanup_mod):
        rows = [
            {"hash_md5": "abc", "image_path": "/a.jpg"},
            {"hash_md5": "def", "image_path": "/b.jpg"},
        ]
        dup_hashes, clusters = cleanup_mod.assign_duplicate_cluster_ids(rows)
        assert clusters == 0
        assert dup_hashes == []
        assert all(r["duplicate_cluster_id"] == "" for r in rows)

    def test_detects_duplicates(self, cleanup_mod):
        rows = [
            {"hash_md5": "abc", "image_path": "/a.jpg"},
            {"hash_md5": "abc", "image_path": "/b.jpg"},
            {"hash_md5": "def", "image_path": "/c.jpg"},
        ]
        dup_hashes, clusters = cleanup_mod.assign_duplicate_cluster_ids(rows)
        assert clusters == 1
        assert "abc" in dup_hashes
        cluster_ids = {r["duplicate_cluster_id"] for r in rows}
        assert "" in cluster_ids
        assert "1" in cluster_ids

    def test_empty_hash_skipped(self, cleanup_mod):
        rows = [
            {"hash_md5": "", "image_path": "/a.jpg"},
            {"hash_md5": "", "image_path": "/b.jpg"},
        ]
        dup_hashes, clusters = cleanup_mod.assign_duplicate_cluster_ids(rows)
        assert clusters == 0
        assert all(r["duplicate_cluster_id"] == "" for r in rows)


# ── De-duplication ──────────────────────────────────────────────────


class TestDeduplicateManifest:
    def test_keeps_one_per_cluster(self, cleanup_mod):
        rows = [
            {"hash_md5": "abc", "image_path": "/b.jpg"},
            {"hash_md5": "abc", "image_path": "/a.jpg"},
            {"hash_md5": "def", "image_path": "/c.jpg"},
        ]
        clean, kept, removed = cleanup_mod.deduplicate_manifest(rows)
        assert len(clean) == 2
        assert removed == 1
        assert kept["abc"] == "/a.jpg"  # lexicographic first
        assert kept["def"] == "/c.jpg"

    def test_empty_hash_retained(self, cleanup_mod):
        rows = [
            {"hash_md5": "", "image_path": "/a.jpg"},
            {"hash_md5": "", "image_path": "/b.jpg"},
        ]
        clean, kept, removed = cleanup_mod.deduplicate_manifest(rows)
        assert len(clean) == 2
        assert removed == 0

    def test_is_duplicate_kept_flag(self, cleanup_mod):
        rows = [
            {"hash_md5": "abc", "image_path": "/a.jpg"},
            {"hash_md5": "abc", "image_path": "/b.jpg"},
        ]
        clean, kept, removed = cleanup_mod.deduplicate_manifest(rows)
        assert clean[0]["is_duplicate_kept"] == "True"


# ── Duplicate audit table ───────────────────────────────────────────


class TestDuplicateAudit:
    def test_audit_contains_all_cluster_rows(self, cleanup_mod):
        rows = [
            {"hash_md5": "abc", "image_path": "/a.jpg", "source_dataset": "S1", "source_class_name": "C1", "canonical_label": "L1", "duplicate_cluster_id": "1"},
            {"hash_md5": "abc", "image_path": "/b.jpg", "source_dataset": "S1", "source_class_name": "C1", "canonical_label": "L1", "duplicate_cluster_id": "1"},
            {"hash_md5": "def", "image_path": "/c.jpg", "source_dataset": "S2", "source_class_name": "C2", "canonical_label": "L2", "duplicate_cluster_id": ""},
        ]
        kept = {"abc": "/a.jpg"}
        audit = cleanup_mod.build_duplicate_audit(rows, kept)
        assert len(audit) == 2
        assert any(r["kept_for_training"] == "True" for r in audit)
        assert any(r["kept_for_training"] == "False" for r in audit)


# ── Label mapping ───────────────────────────────────────────────────


class TestBuildLabelMapping:
    def test_one_row_per_source_class(self, cleanup_mod):
        rows = [
            {"source_dataset": "S1", "source_class_name": "C1", "crop": "Crop1", "disease": "D1", "canonical_label": "L1", "is_healthy": "False"},
            {"source_dataset": "S1", "source_class_name": "C1", "crop": "Crop1", "disease": "D1", "canonical_label": "L1", "is_healthy": "False"},
            {"source_dataset": "S1", "source_class_name": "C2", "crop": "Crop1", "disease": "D2", "canonical_label": "L2", "is_healthy": "False"},
        ]
        mapping = cleanup_mod.build_label_mapping(rows)
        assert len(mapping) == 2
        assert mapping[0]["source_class_name"] == "C1"
        assert mapping[1]["source_class_name"] == "C2"


# ── Ambiguous labels ────────────────────────────────────────────────


class TestAmbiguousLabels:
    def test_missing_crop(self, cleanup_mod):
        rows = [
            {"image_path": "/a.jpg", "source_dataset": "S1", "source_class_name": "C1", "crop": "", "canonical_label": "L1"},
        ]
        ambiguous = cleanup_mod.find_ambiguous_labels(rows)
        assert len(ambiguous) == 1
        assert ambiguous[0]["reason"] == "missing_crop"

    def test_no_ambiguous(self, cleanup_mod):
        rows = [
            {"image_path": "/a.jpg", "source_dataset": "S1", "source_class_name": "C1", "crop": "Crop1", "canonical_label": "L1"},
        ]
        ambiguous = cleanup_mod.find_ambiguous_labels(rows)
        assert ambiguous == []


# ── Report writing ──────────────────────────────────────────────────


class TestWriteReport:
    def test_report_has_required_sections(self, cleanup_mod, tmp_path):
        cleanup_mod.write_report(
            tmp_path / "report.md",
            total_before=100,
            total_after=95,
            duplicate_clusters=3,
            duplicate_rows=8,
            rows_removed=5,
            canonical_before=20,
            canonical_after=18,
            citrus_override_count=1036,
            ambiguous=[],
        )
        text = (tmp_path / "report.md").read_text(encoding="utf-8")
        assert "## Summary" in text
        assert "Total rows before cleanup" in text
        assert "Total rows after cleanup" in text
        assert "Duplicate clusters found" in text
        assert "Citrus crop override applied" in text
        assert "## Ambiguous or Unmatched Labels" in text

    def test_report_ambiguous_entries(self, cleanup_mod, tmp_path):
        cleanup_mod.write_report(
            tmp_path / "report.md",
            total_before=100,
            total_after=95,
            duplicate_clusters=0,
            duplicate_rows=0,
            rows_removed=0,
            canonical_before=20,
            canonical_after=20,
            citrus_override_count=0,
            ambiguous=[{"image_path": "/x.jpg", "source_dataset": "S", "source_class_name": "C", "reason": "missing_crop"}],
        )
        text = (tmp_path / "report.md").read_text(encoding="utf-8")
        assert "/x.jpg" in text
        assert "missing_crop" in text


# ── Integration test ────────────────────────────────────────────────


class TestRunIntegration:
    def test_run_with_synthetic_data(self, cleanup_mod, tmp_path):
        """Run the pipeline on synthetic CSVs and verify outputs."""
        manifest = tmp_path / "manifest.csv"
        inventory = tmp_path / "inventory.csv"
        mapping = tmp_path / "mapping.csv"

        with manifest.open("w", encoding="utf-8", newline="") as fh:
            writer = csv.DictWriter(fh, fieldnames=cleanup_mod.MANIFEST_COLUMNS[:-1], lineterminator="\n")
            writer.writeheader()
            writer.writerows([
                {
                    "image_path": "/a.jpg",
                    "source_dataset": "Citrus Leaves",
                    "source_class_name": "Black spot",
                    "crop": "Black",
                    "disease": "Spot",
                    "canonical_label": "Black__Spot",
                    "is_healthy": "False",
                    "width": "100",
                    "height": "100",
                    "channels": "3",
                    "is_corrupt": "False",
                    "hash_md5": "abc",
                },
                {
                    "image_path": "/b.jpg",
                    "source_dataset": "Citrus Leaves",
                    "source_class_name": "Black spot",
                    "crop": "Black",
                    "disease": "Spot",
                    "canonical_label": "Black__Spot",
                    "is_healthy": "False",
                    "width": "100",
                    "height": "100",
                    "channels": "3",
                    "is_corrupt": "False",
                    "hash_md5": "abc",
                },
                {
                    "image_path": "/c.jpg",
                    "source_dataset": "PlantVillage",
                    "source_class_name": "Tomato_healthy",
                    "crop": "Tomato",
                    "disease": "healthy",
                    "canonical_label": "Tomato__healthy",
                    "is_healthy": "True",
                    "width": "100",
                    "height": "100",
                    "channels": "3",
                    "is_corrupt": "False",
                    "hash_md5": "def",
                },
            ])

        with inventory.open("w", encoding="utf-8", newline="") as fh:
            writer = csv.DictWriter(fh, fieldnames=cleanup_mod.INVENTORY_COLUMNS, lineterminator="\n")
            writer.writeheader()
            writer.writerow({
                "source_dataset": "Citrus Leaves",
                "download_path": "",
                "detected_root": "",
                "total_images": "2",
                "valid_images": "2",
                "corrupt_images": "0",
                "num_classes": "1",
                "notes": "test",
            })

        with mapping.open("w", encoding="utf-8", newline="") as fh:
            writer = csv.DictWriter(fh, fieldnames=cleanup_mod.MAPPING_COLUMNS, lineterminator="\n")
            writer.writeheader()
            writer.writerow({
                "source_dataset": "Citrus Leaves",
                "source_class_name": "Black spot",
                "crop": "Black",
                "disease": "Spot",
                "canonical_label": "Black__Spot",
                "is_healthy": "False",
            })

        out_manifest = tmp_path / "clean_manifest.csv"
        out_audit = tmp_path / "audit.csv"
        out_mapping = tmp_path / "clean_mapping.csv"
        out_report = tmp_path / "report.md"

        result = cleanup_mod.run(
            manifest_path=manifest,
            inventory_path=inventory,
            mapping_path=mapping,
            output_manifest_path=out_manifest,
            output_audit_path=out_audit,
            output_mapping_path=out_mapping,
            output_report_path=out_report,
        )

        assert result["total_before"] == 3
        assert result["total_after"] == 2
        assert result["duplicate_clusters"] == 1
        assert result["duplicate_rows"] == 2
        assert result["rows_removed"] == 1
        assert result["citrus_override_count"] == 2
        assert out_manifest.exists()
        assert out_audit.exists()
        assert out_mapping.exists()
        assert out_report.exists()
