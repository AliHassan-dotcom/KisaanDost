"""Clean up the unified crop-disease manifest.

Steps:
1. Load the unified manifest, source inventory, and label mapping.
2. Apply a Citrus Leaves crop override so crop = "citrus" and disease comes from
   the source folder name.
3. Recompute canonical labels for Citrus entries.
4. Detect duplicate MD5 hashes and assign duplicate_cluster_id.
5. Build a de-duplicated clean manifest (one row per hash cluster).
6. Preserve a full duplicate audit table.
7. Update the label mapping table with corrected crop/disease/canonical labels.
8. Write a Markdown cleanup report.

The raw unified manifest is never modified.
"""

from __future__ import annotations

import csv
import os
import re
from collections import OrderedDict
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

ROOT = Path(__file__).resolve().parent.parent

INPUT_MANIFEST = ROOT / "data" / "raw" / "unified_crop_disease_manifest.csv"
INPUT_INVENTORY = ROOT / "data" / "raw" / "dataset_source_inventory.csv"
INPUT_MAPPING = ROOT / "data" / "raw" / "label_mapping_table.csv"

OUTPUT_DIR = ROOT / "data" / "processed"
REPORT_DIR = ROOT / "reports"

OUTPUT_MANIFEST = OUTPUT_DIR / "unified_crop_disease_manifest_clean.csv"
OUTPUT_DUPLICATE_AUDIT = OUTPUT_DIR / "duplicate_audit_table.csv"
OUTPUT_MAPPING_CLEAN = OUTPUT_DIR / "label_mapping_table_clean.csv"
OUTPUT_REPORT = REPORT_DIR / "unified_manifest_cleanup_report.md"

MANIFEST_COLUMNS = [
    "image_path",
    "source_dataset",
    "source_class_name",
    "crop",
    "disease",
    "canonical_label",
    "is_healthy",
    "width",
    "height",
    "channels",
    "is_corrupt",
    "hash_md5",
    "duplicate_cluster_id",
]

DEDUPLICATED_MANIFEST_COLUMNS = MANIFEST_COLUMNS + ["is_duplicate_kept"]

AUDIT_COLUMNS = [
    "duplicate_cluster_id",
    "hash_md5",
    "image_path",
    "source_dataset",
    "source_class_name",
    "canonical_label",
    "kept_for_training",
]

MAPPING_COLUMNS = [
    "source_dataset",
    "source_class_name",
    "crop",
    "disease",
    "canonical_label",
    "is_healthy",
]

INVENTORY_COLUMNS = [
    "source_dataset",
    "download_path",
    "detected_root",
    "total_images",
    "valid_images",
    "corrupt_images",
    "num_classes",
    "notes",
]

CITRUS_SOURCE_NAME = "Citrus Leaves"
CITRUS_CROP = "citrus"


def load_csv(path: Path) -> List[Dict[str, str]]:
    """Load a CSV file into a list of dictionaries."""
    with path.open("r", encoding="utf-8", newline="") as fh:
        return list(csv.DictReader(fh))


def _normalize_disease_token(value: str) -> str:
    """Normalize a disease folder name into a lowercase snake_case token."""
    cleaned = re.sub(r"\s+", " ", value.replace("_", " ").replace("-", " ")).strip()
    return "_".join(cleaned.lower().split())


def apply_citrus_override(rows: List[Dict[str, str]]) -> List[Dict[str, str]]:
    """Override Citrus Leaves crop and recompute canonical labels.

    For Citrus Leaves the source folder names are disease names (e.g.
    ``Black spot``, ``canker``, ``greening``, ``Melanose``, ``healthy``).
    We force crop to ``citrus``, keep the disease, and build a consistent
    lowercase canonical label such as ``citrus_black_spot`` or
    ``citrus_healthy``.
    """
    for row in rows:
        if row["source_dataset"] != CITRUS_SOURCE_NAME:
            continue
        disease_raw = row["source_class_name"].strip()
        disease = _normalize_disease_token(disease_raw)
        row["crop"] = CITRUS_CROP
        row["disease"] = disease.replace("_", " ")
        if disease == "healthy":
            row["is_healthy"] = "True"
            row["canonical_label"] = "citrus_healthy"
        else:
            row["is_healthy"] = "False"
            row["canonical_label"] = f"citrus_{disease}"
    return rows


def assign_duplicate_cluster_ids(
    rows: List[Dict[str, str]],
) -> Tuple[List[Dict[str, str]], int]:
    """Add duplicate_cluster_id to rows whose hash appears more than once.

    Empty hashes and unique hashes receive an empty cluster id.
    """
    hash_counts: Dict[str, int] = {}
    for row in rows:
        h = row["hash_md5"]
        if h:
            hash_counts[h] = hash_counts.get(h, 0) + 1

    hash_to_cluster: Dict[str, int] = {}
    next_cluster_id = 1
    for h, count in hash_counts.items():
        if count > 1:
            hash_to_cluster[h] = next_cluster_id
            next_cluster_id += 1

    for row in rows:
        h = row["hash_md5"]
        row["duplicate_cluster_id"] = str(hash_to_cluster.get(h, ""))

    duplicate_hashes = [h for h, cid in hash_to_cluster.items()]
    return duplicate_hashes, next_cluster_id - 1


def build_duplicate_audit(
    rows: List[Dict[str, str]],
    kept_paths: Dict[str, str],
) -> List[Dict[str, str]]:
    """Build an audit table containing every row that belongs to a cluster."""
    audit: List[Dict[str, str]] = []
    for row in rows:
        cluster_id = row["duplicate_cluster_id"]
        if not cluster_id:
            continue
        h = row["hash_md5"]
        audit.append(
            {
                "duplicate_cluster_id": cluster_id,
                "hash_md5": h,
                "image_path": row["image_path"],
                "source_dataset": row["source_dataset"],
                "source_class_name": row["source_class_name"],
                "canonical_label": row["canonical_label"],
                "kept_for_training": str(row["image_path"] == kept_paths.get(h, "")),
            }
        )
    return audit


def deduplicate_manifest(
    rows: List[Dict[str, str]],
) -> Tuple[List[Dict[str, str]], Dict[str, str], int]:
    """Keep one representative per duplicate hash cluster.

    Deterministic tie-breaking: sort by image_path and keep the first row.
    Returns the de-duplicated rows, a map hash->kept path, and the number of
    rows removed.
    """
    seen_hashes: Dict[str, str] = {}
    kept_paths: Dict[str, str] = {}
    deduped: List[Dict[str, str]] = []

    for row in sorted(rows, key=lambda r: r["image_path"]):
        h = row["hash_md5"]
        if not h:
            row["is_duplicate_kept"] = "True"
            deduped.append(row)
            continue
        if h not in seen_hashes:
            seen_hashes[h] = row["image_path"]
            kept_paths[h] = row["image_path"]
            row["is_duplicate_kept"] = "True"
            deduped.append(row)
        else:
            row["is_duplicate_kept"] = "False"
            deduped.append(row)

    # The clean manifest keeps only representatives + all unique rows
    clean_rows = [r for r in deduped if r["is_duplicate_kept"] == "True"]
    removed = len(rows) - len(clean_rows)
    return clean_rows, kept_paths, removed


def build_label_mapping(
    rows: List[Dict[str, str]],
) -> List[Dict[str, str]]:
    """Build a deterministic label-mapping table per source class name."""
    mapping: Dict[Tuple[str, str], Dict[str, str]] = OrderedDict()
    for row in rows:
        key = (row["source_dataset"], row["source_class_name"])
        if key in mapping:
            continue
        mapping[key] = {
            "source_dataset": row["source_dataset"],
            "source_class_name": row["source_class_name"],
            "crop": row["crop"],
            "disease": row["disease"],
            "canonical_label": row["canonical_label"],
            "is_healthy": row["is_healthy"],
        }
    return list(mapping.values())


def find_ambiguous_labels(rows: List[Dict[str, str]]) -> List[Dict[str, str]]:
    """Flag rows with missing or suspicious crop/disease/canonical values."""
    ambiguous: List[Dict[str, str]] = []
    for row in rows:
        if not row["crop"]:
            ambiguous.append(
                {
                    "image_path": row["image_path"],
                    "source_dataset": row["source_dataset"],
                    "source_class_name": row["source_class_name"],
                    "reason": "missing_crop",
                }
            )
        elif not row["canonical_label"]:
            ambiguous.append(
                {
                    "image_path": row["image_path"],
                    "source_dataset": row["source_dataset"],
                    "source_class_name": row["source_class_name"],
                    "reason": "missing_canonical_label",
                }
            )
    return ambiguous


def write_csv(rows: List[Dict[str, str]], path: Path, fieldnames: List[str]) -> None:
    """Write rows to a CSV file with explicit field order."""
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as fh:
        writer = csv.DictWriter(fh, fieldnames=fieldnames, lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)


def write_report(
    report_path: Path,
    total_before: int,
    total_after: int,
    duplicate_clusters: int,
    duplicate_rows: int,
    rows_removed: int,
    canonical_before: int,
    canonical_after: int,
    citrus_override_count: int,
    ambiguous: List[Dict[str, str]],
) -> None:
    """Write the Markdown cleanup report."""
    report_path.parent.mkdir(parents=True, exist_ok=True)
    lines = [
        "# Unified Manifest Cleanup Report",
        "",
        "## Summary",
        "",
        "| Metric | Value |",
        "|--------|-------|",
        f"| Total rows before cleanup | {total_before} |",
        f"| Total rows after cleanup | {total_after} |",
        f"| Duplicate clusters found | {duplicate_clusters} |",
        f"| Duplicate rows (audit table) | {duplicate_rows} |",
        f"| Rows removed from training manifest | {rows_removed} |",
        f"| Citrus crop override applied | {citrus_override_count} rows |",
        f"| Canonical labels before cleanup | {canonical_before} |",
        f"| Canonical labels after cleanup | {canonical_after} |",
        f"| Ambiguous labels remaining | {len(ambiguous)} |",
        "",
        "## Citrus Crop Override",
        "",
        f"Applied to `{CITRUS_SOURCE_NAME}`: crop forced to `{CITRUS_CROP}`, "
        "disease taken from source folder name, and canonical labels normalized to "
        "lowercase `citrus_<disease>` form.",
        "",
        "## Duplicate Cluster Summary",
        "",
        f"- Duplicate hash clusters: {duplicate_clusters}",
        f"- Rows involved in duplicate clusters: {duplicate_rows}",
        f"- Representative rows kept for training: {duplicate_clusters}",
        f"- Duplicate rows excluded from training manifest: {rows_removed}",
        "",
        "## Ambiguous or Unmatched Labels",
        "",
    ]
    if ambiguous:
        lines.append("| image_path | source_dataset | source_class_name | reason |")
        lines.append("|------------|----------------|-------------------|--------|")
        for entry in ambiguous:
            lines.append(
                f"| {entry['image_path']} | {entry['source_dataset']} | "
                f"{entry['source_class_name']} | {entry['reason']} |"
            )
    else:
        lines.append("- None detected.")

    lines += [
        "",
        "## Output Files",
        "",
        f"- Clean manifest: `{OUTPUT_MANIFEST.relative_to(ROOT)}`",
        f"- Duplicate audit table: `{OUTPUT_DUPLICATE_AUDIT.relative_to(ROOT)}`",
        f"- Clean label mapping: `{OUTPUT_MAPPING_CLEAN.relative_to(ROOT)}`",
        "",
        "## Notes",
        "",
        "- Raw unified manifest was not modified.",
        "- De-duplication keeps the first image_path (lexicographic) per hash cluster.",
        "- Rows with empty `hash_md5` are treated as unique and retained.",
    ]

    report_path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def run(
    manifest_path: Optional[Path] = None,
    inventory_path: Optional[Path] = None,
    mapping_path: Optional[Path] = None,
    output_manifest_path: Optional[Path] = None,
    output_audit_path: Optional[Path] = None,
    output_mapping_path: Optional[Path] = None,
    output_report_path: Optional[Path] = None,
) -> Dict[str, Any]:
    """Run the cleanup pipeline and write all artifacts."""
    manifest_path = manifest_path or INPUT_MANIFEST
    inventory_path = inventory_path or INPUT_INVENTORY
    mapping_path = mapping_path or INPUT_MAPPING
    output_manifest_path = output_manifest_path or OUTPUT_MANIFEST
    output_audit_path = output_audit_path or OUTPUT_DUPLICATE_AUDIT
    output_mapping_path = output_mapping_path or OUTPUT_MAPPING_CLEAN
    output_report_path = output_report_path or OUTPUT_REPORT

    print(f"Loading manifest from {manifest_path}...")
    rows = load_csv(manifest_path)
    total_before = len(rows)
    print(f"  Loaded {total_before} rows")

    # Citrus override (modifies rows in memory only)
    rows = apply_citrus_override(rows)
    citrus_override_count = sum(
        1 for r in rows if r["source_dataset"] == CITRUS_SOURCE_NAME
    )
    print(f"  Citrus override applied to {citrus_override_count} rows")

    # Duplicate detection
    duplicate_hashes, duplicate_clusters = assign_duplicate_cluster_ids(rows)
    duplicate_rows = sum(1 for r in rows if r["duplicate_cluster_id"])
    print(f"  Duplicate clusters: {duplicate_clusters} ({duplicate_rows} rows)")

    # De-duplicated clean manifest
    clean_rows, kept_paths, rows_removed = deduplicate_manifest(rows)
    print(f"  Clean manifest rows: {len(clean_rows)} (removed {rows_removed})")

    # Audit table
    audit_rows = build_duplicate_audit(rows, kept_paths)
    print(f"  Audit table rows: {len(audit_rows)}")

    # Clean label mapping (derived from clean rows)
    mapping_rows = build_label_mapping(clean_rows)
    canonical_after = len({r["canonical_label"] for r in clean_rows if r["canonical_label"]})
    print(f"  Clean label mapping rows: {len(mapping_rows)}")

    # Ambiguous labels
    ambiguous = find_ambiguous_labels(clean_rows)

    # Canonical label count before cleanup (from original mapping table)
    original_mapping = load_csv(mapping_path)
    canonical_before = len({r["canonical_label"] for r in original_mapping if r.get("canonical_label")})

    # Write outputs
    print("Writing outputs...")
    write_csv(clean_rows, output_manifest_path, DEDUPLICATED_MANIFEST_COLUMNS)
    write_csv(audit_rows, output_audit_path, AUDIT_COLUMNS)
    write_csv(mapping_rows, output_mapping_path, MAPPING_COLUMNS)
    write_report(
        output_report_path,
        total_before=total_before,
        total_after=len(clean_rows),
        duplicate_clusters=duplicate_clusters,
        duplicate_rows=duplicate_rows,
        rows_removed=rows_removed,
        canonical_before=canonical_before,
        canonical_after=canonical_after,
        citrus_override_count=citrus_override_count,
        ambiguous=ambiguous,
    )

    print(f"  Clean manifest: {output_manifest_path}")
    print(f"  Audit table: {output_audit_path}")
    print(f"  Clean mapping: {output_mapping_path}")
    print(f"  Report: {output_report_path}")

    return {
        "manifest_path": str(output_manifest_path),
        "audit_path": str(output_audit_path),
        "mapping_path": str(output_mapping_path),
        "report_path": str(output_report_path),
        "total_before": total_before,
        "total_after": len(clean_rows),
        "duplicate_clusters": duplicate_clusters,
        "duplicate_rows": duplicate_rows,
        "rows_removed": rows_removed,
        "canonical_before": canonical_before,
        "canonical_after": canonical_after,
        "citrus_override_count": citrus_override_count,
        "ambiguous_labels": ambiguous,
    }


if __name__ == "__main__":
    result = run()
    print("\nCleanup complete.")
    print(f"  Before: {result['total_before']} rows")
    print(f"  After:  {result['total_after']} rows")
    print(f"  Duplicate clusters: {result['duplicate_clusters']}")
