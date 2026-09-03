"""Clean manifest + class mapping + stratified train/val/test split.

Input:
- ``data/raw/plantvillage_manifest.csv`` (20,638 rows, Step 1 output)

Outputs:
- ``data/processed/plantvillage_manifest_clean.csv`` — with split assignments
- ``data/processed/plantvillage_class_mapping.csv`` — class ID mapping table
- ``reports/plantvillage_clean_manifest_report.md`` — validation report

Split strategy:
- Stratified by class_name (preserves class balance in each split)
- Deterministic via ``random.Random(seed).shuffle()`` per class group
- 70% train / 15% val / 15% test

Stdlib only.
"""

from __future__ import annotations

import csv
import random
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

SPLIT_SEED = 42
TRAIN_RATIO = 0.70
VAL_RATIO = 0.15
# TEST_RATIO is the remainder: 0.15

OUTPUT_COLUMNS = [
    "image_path",
    "label",
    "class_name",
    "crop",
    "disease",
    "is_healthy",
    "source_dataset",
    "split",
    "split_seed",
]

CLASS_MAPPING_COLUMNS = [
    "class_id",
    "class_name",
    "crop",
    "disease",
    "is_healthy",
    "num_images",
    "num_train",
    "num_val",
    "num_test",
]


def load_raw_manifest(path: Path) -> List[Dict[str, str]]:
    """Load the raw manifest from Step 1."""
    with path.open("r", encoding="utf-8", newline="") as fh:
        return list(csv.DictReader(fh))


def stratified_split(
    rows: List[Dict[str, str]],
    seed: int = SPLIT_SEED,
    train_ratio: float = TRAIN_RATIO,
    val_ratio: float = VAL_RATIO,
) -> List[Dict[str, str]]:
    """Assign stratified train/val/test splits to each row.

    Groups by class_name, sorts deterministically within each group by
    image_path, shuffles with the given seed, then assigns splits by
    cumulative ratio.

    Returns the rows with ``split`` and ``split_seed`` fields set.
    """
    rng = random.Random(seed)

    # Group by class
    groups: Dict[str, List[Dict[str, str]]] = defaultdict(list)
    for row in rows:
        groups[row["class_name"]].append(row)

    output_rows: List[Dict[str, str]] = []

    for class_name in sorted(groups.keys()):
        class_rows = groups[class_name]
        # Sort by image_path for deterministic base order
        class_rows.sort(key=lambda r: r["image_path"])
        # Shuffle with seeded RNG
        rng.shuffle(class_rows)

        n = len(class_rows)
        n_train = round(n * train_ratio)
        n_val = round(n * val_ratio)
        # test gets the remainder to ensure exact total

        for i, row in enumerate(class_rows):
            if i < n_train:
                split = "train"
            elif i < n_train + n_val:
                split = "val"
            else:
                split = "test"

            out_row = {
                "image_path": row["image_path"],
                "label": row["label"],
                "class_name": row["class_name"],
                "crop": row["crop"],
                "disease": row["disease"],
                "is_healthy": row["is_healthy"],
                "source_dataset": row["source_dataset"],
                "split": split,
                "split_seed": str(seed),
            }
            output_rows.append(out_row)

    # Sort final output by class_name then image_path for deterministic order
    output_rows.sort(key=lambda r: (r["class_name"], r["image_path"]))
    return output_rows


def build_class_mapping(
    rows: List[Dict[str, str]],
) -> List[Dict[str, str]]:
    """Build the class mapping table with split counts."""
    # Group by class_name
    groups: Dict[str, List[Dict[str, str]]] = defaultdict(list)
    for row in rows:
        groups[row["class_name"]].append(row)

    mapping: List[Dict[str, str]] = []
    for class_id, class_name in enumerate(sorted(groups.keys())):
        class_rows = groups[class_name]
        first = class_rows[0]
        split_counts = Counter(r["split"] for r in class_rows)

        mapping.append({
            "class_id": str(class_id),
            "class_name": class_name,
            "crop": first["crop"],
            "disease": first["disease"],
            "is_healthy": first["is_healthy"],
            "num_images": str(len(class_rows)),
            "num_train": str(split_counts.get("train", 0)),
            "num_val": str(split_counts.get("val", 0)),
            "num_test": str(split_counts.get("test", 0)),
        })

    return mapping


def write_clean_manifest(
    rows: List[Dict[str, str]],
    output_path: Path,
) -> None:
    """Write the clean manifest CSV."""
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with output_path.open("w", encoding="utf-8", newline="") as fh:
        writer = csv.DictWriter(
            fh, fieldnames=OUTPUT_COLUMNS, lineterminator="\n", extrasaction="ignore"
        )
        writer.writeheader()
        writer.writerows(rows)


def write_class_mapping(
    mapping: List[Dict[str, str]],
    output_path: Path,
) -> None:
    """Write the class mapping CSV."""
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with output_path.open("w", encoding="utf-8", newline="") as fh:
        writer = csv.DictWriter(
            fh, fieldnames=CLASS_MAPPING_COLUMNS, lineterminator="\n"
        )
        writer.writeheader()
        writer.writerows(mapping)


def validate(
    raw_rows: List[Dict[str, str]],
    clean_rows: List[Dict[str, str]],
    mapping: List[Dict[str, str]],
) -> Dict[str, Any]:
    """Run all validation checks and return a summary dict."""
    # Row count
    raw_count = len(raw_rows)
    clean_count = len(clean_rows)

    # Duplicate check
    paths = [r["image_path"] for r in clean_rows]
    duplicate_paths = len(paths) - len(set(paths))

    # Missing values
    missing: Dict[str, int] = {}
    for col in OUTPUT_COLUMNS:
        empty = sum(1 for r in clean_rows if not r.get(col, "").strip())
        if empty > 0:
            missing[col] = empty

    # Split distribution
    split_counts = Counter(r["split"] for r in clean_rows)

    # Per-class split distribution
    class_split: Dict[str, Dict[str, int]] = defaultdict(lambda: defaultdict(int))
    class_totals: Dict[str, int] = Counter()
    for row in clean_rows:
        cls = row["class_name"]
        class_split[cls][row["split"]] += 1
        class_totals[cls] += 1

    # Class balance: compare raw vs clean proportions
    raw_class_counts = Counter(r["class_name"] for r in raw_rows)
    clean_class_counts = Counter(r["class_name"] for r in clean_rows)

    # Mapping summary
    num_classes = len(mapping)
    num_crops = len(set(m["crop"] for m in mapping))
    num_healthy = sum(1 for m in mapping if m["is_healthy"] == "True")

    # Source dataset check
    source_ok = all(r["source_dataset"] == "PlantVillage" for r in clean_rows)

    # Split seed check
    seed_ok = all(r["split_seed"] == str(SPLIT_SEED) for r in clean_rows)

    return {
        "raw_count": raw_count,
        "clean_count": clean_count,
        "row_count_match": raw_count == clean_count,
        "duplicate_paths": duplicate_paths,
        "missing_values": dict(missing),
        "split_counts": dict(split_counts.most_common()),
        "class_split_distribution": {
            k: dict(v) for k, v in sorted(class_split.items())
        },
        "class_totals": dict(sorted(class_totals.items())),
        "raw_class_counts": dict(sorted(raw_class_counts.items())),
        "clean_class_counts": dict(sorted(clean_class_counts.items())),
        "num_classes": num_classes,
        "num_crops": num_crops,
        "num_healthy": num_healthy,
        "source_dataset_ok": source_ok,
        "split_seed_ok": seed_ok,
        "mapping_rows": len(mapping),
    }


def write_report(
    stats: Dict[str, Any],
    report_path: Path,
) -> None:
    """Write the clean manifest validation report."""
    report_path.parent.mkdir(parents=True, exist_ok=True)

    lines = [
        "# PlantVillage Clean Manifest Report",
        "",
        "## Summary",
        "",
        "| Metric | Value |",
        "|--------|-------|",
        f"| Raw manifest rows | {stats['raw_count']} |",
        f"| Clean manifest rows | {stats['clean_count']} |",
        f"| Row count match | {stats['row_count_match']} |",
        f"| Duplicate paths | {stats['duplicate_paths']} |",
        f"| Classes | {stats['num_classes']} |",
        f"| Crops | {stats['num_crops']} |",
        f"| Healthy classes | {stats['num_healthy']} |",
        f"| Source dataset consistent | {stats['source_dataset_ok']} |",
        f"| Split seed consistent | {stats['split_seed_ok']} |",
        f"| Split seed | {SPLIT_SEED} |",
        "",
        "## Split Distribution",
        "",
        "| Split | Count | Percentage |",
        "|-------|-------|------------|",
    ]

    for split_name in ("train", "val", "test"):
        count = stats["split_counts"].get(split_name, 0)
        pct = f"{count / stats['clean_count'] * 100:.1f}%" if stats["clean_count"] else "0%"
        lines.append(f"| {split_name} | {count} | {pct} |")

    lines += [
        "",
        "## Per-Class Split Distribution",
        "",
        "| Class | Total | Train | Val | Test |",
        "|-------|-------|-------|-----|------|",
    ]

    for cls in sorted(stats["class_split_distribution"].keys()):
        splits = stats["class_split_distribution"][cls]
        total = stats["class_totals"][cls]
        tr = splits.get("train", 0)
        va = splits.get("val", 0)
        te = splits.get("test", 0)
        lines.append(f"| {cls} | {total} | {tr} | {va} | {te} |")

    lines += [
        "",
        "## Class Balance: Raw vs Clean",
        "",
        "| Class | Raw Count | Clean Count | Match |",
        "|-------|-----------|-------------|-------|",
    ]

    for cls in sorted(stats["raw_class_counts"].keys()):
        raw_c = stats["raw_class_counts"][cls]
        clean_c = stats["clean_class_counts"].get(cls, 0)
        match = raw_c == clean_c
        lines.append(f"| {cls} | {raw_c} | {clean_c} | {match} |")

    lines += [
        "",
        "## Class Mapping Table",
        "",
        "| ID | Class Name | Crop | Disease | Healthy | Images |",
        "|----|-----------|------|---------|---------|--------|",
    ]

    for m in stats.get("mapping_table", []):
        lines.append(
            f"| {m['class_id']} | {m['class_name']} | {m['crop']} "
            f"| {m['disease']} | {m['is_healthy']} | {m['num_images']} |"
        )

    if stats.get("missing_values"):
        lines += [
            "",
            "## Missing Values",
            "",
            "| Column | Empty Count |",
            "|--------|-------------|",
        ]
        for col, count in sorted(stats["missing_values"].items()):
            lines.append(f"| {col} | {count} |")
    else:
        lines += [
            "",
            "## Missing Values",
            "",
            "None — all required columns populated.",
        ]

    lines += [
        "",
        "## Notes",
        "",
        f"- Stratified split: {TRAIN_RATIO:.0%} train / {VAL_RATIO:.0%} val / remainder test.",
        f"- Random seed: {SPLIT_SEED} (deterministic, reproducible).",
        "- No rows dropped, no duplicates introduced, no image paths modified.",
        "- `source_dataset` preserved as `PlantVillage` on every row.",
        "- Raw manifest (`data/raw/plantvillage_manifest.csv`) not modified.",
    ]

    with report_path.open("w", encoding="utf-8") as fh:
        fh.write("\n".join(lines) + "\n")


def run(
    raw_manifest_path: Optional[Path] = None,
    output_dir: Optional[Path] = None,
    report_dir: Optional[Path] = None,
) -> Dict[str, Any]:
    """Full pipeline: load raw manifest, split, build mapping, validate, write."""
    root = Path(__file__).resolve().parent.parent
    raw_manifest_path = raw_manifest_path or (root / "data" / "raw" / "plantvillage_manifest.csv")
    output_dir = output_dir or (root / "data" / "processed")
    report_dir = report_dir or (root / "reports")

    print("Loading raw manifest...")
    raw_rows = load_raw_manifest(raw_manifest_path)
    print(f"  Loaded {len(raw_rows)} rows")

    print("Building stratified split...")
    clean_rows = stratified_split(raw_rows)
    print(f"  Split {len(clean_rows)} rows into train/val/test")

    print("Building class mapping...")
    mapping = build_class_mapping(clean_rows)
    print(f"  {len(mapping)} classes mapped")

    print("Validating...")
    stats = validate(raw_rows, clean_rows, mapping)
    print(f"  Row count match: {stats['row_count_match']}")
    print(f"  Duplicate paths: {stats['duplicate_paths']}")
    print(f"  Source dataset OK: {stats['source_dataset_ok']}")

    print("Writing outputs...")
    clean_path = output_dir / "plantvillage_manifest_clean.csv"
    mapping_path = output_dir / "plantvillage_class_mapping.csv"
    report_path = report_dir / "plantvillage_clean_manifest_report.md"

    write_clean_manifest(clean_rows, clean_path)
    write_class_mapping(mapping, mapping_path)

    # Include mapping table in report stats
    stats["mapping_table"] = mapping

    write_report(stats, report_path)

    print(f"  Clean manifest: {clean_path}")
    print(f"  Class mapping:  {mapping_path}")
    print(f"  Report:         {report_path}")

    split_counts = stats["split_counts"]
    print(f"\nSplit distribution:")
    for s in ("train", "val", "test"):
        print(f"  {s}: {split_counts.get(s, 0)}")

    return {
        "clean_manifest_path": str(clean_path),
        "class_mapping_path": str(mapping_path),
        "report_path": str(report_path),
        "stats": stats,
    }


if __name__ == "__main__":
    result = run()
    s = result["stats"]
    print(f"\nValidation: row_match={s['row_count_match']}, "
          f"duplicates={s['duplicate_paths']}, "
          f"missing={len(s['missing_values'])} columns")
