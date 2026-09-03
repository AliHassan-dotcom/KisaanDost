"""Build a unified crop-disease image manifest across multiple datasets.

Scans six Kaggle-hosted sources, validates images, computes MD5 hashes, and
normalizes class labels into a single canonical taxonomy.
"""

from __future__ import annotations

import csv
import hashlib
import os
import re
from collections import Counter, OrderedDict
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

from PIL import Image

IMAGE_EXTENSIONS = {".jpg", ".jpeg", ".png", ".bmp", ".tiff", ".tif", ".gif"}

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

MAPPING_COLUMNS = [
    "source_dataset",
    "source_class_name",
    "crop",
    "disease",
    "canonical_label",
    "is_healthy",
]

HEALTHY_TOKENS = {
    "healthy", "no disease", "no disease detected", "no disease present",
    "no symptoms", "unaffected", "normal",
}

SOURCE_REGISTRY: List[Dict[str, Any]] = [
    {
        "source_dataset": "PlantVillage",
        "kaggle_slug": "emmarex/plantdisease",
        "expected_crops": ["Pepper bell", "Potato", "Tomato"],
        "notes": "Leaf-level disease dataset; 15 classes across 3 crops.",
    },
    {
        "source_dataset": "Wheat Disease",
        "kaggle_slug": "nirmalsaroha/wheat-disease-dataset",
        "expected_crops": ["Wheat"],
        "notes": "Wheat leaf disease dataset.",
    },
    {
        "source_dataset": "Wheat and Rice Leaf Disease",
        "kaggle_slug": "nageshsingh/wheat-and-rice-leaf-disease-images",
        "expected_crops": ["Wheat", "Rice"],
        "notes": "Combined wheat and rice leaf disease images.",
    },
    {
        "source_dataset": "Cotton Leaf Disease",
        "kaggle_slug": "abdulbasithk/cotton-leaf-disease-detection",
        "expected_crops": ["Cotton"],
        "notes": "Cotton leaf disease detection dataset.",
    },
    {
        "source_dataset": "Sugarcane Leaf Diseases",
        "kaggle_slug": "sanjeevkumar21/sugarcane-leaf-diseases",
        "expected_crops": ["Sugarcane"],
        "notes": "Sugarcane leaf disease images.",
    },
    {
        "source_dataset": "Citrus Leaves",
        "kaggle_slug": "sourabh2001/citrus-leaves-dataset",
        "expected_crops": ["Citrus"],
        "notes": "Citrus leaf images.",
    },
]


def download_dataset(slug: str) -> Path:
    """Download a Kaggle dataset via kagglehub and return the local path."""
    import kagglehub
    return Path(kagglehub.dataset_download(slug))


def find_image_root(download_dir: Path) -> Path:
    """Walk into single-child folders and skip nested duplicate roots."""
    candidate = download_dir
    while True:
        children = [d for d in candidate.iterdir() if d.is_dir()]
        if len(children) == 1:
            candidate = children[0]
        else:
            break

    for child in candidate.iterdir():
        if child.is_dir() and child.name == candidate.name:
            outer_dirs = {
                d.name for d in candidate.iterdir()
                if d.is_dir() and d.name != child.name
            }
            inner_dirs = {d.name for d in child.iterdir() if d.is_dir()}
            if outer_dirs and outer_dirs == inner_dirs:
                return candidate
    return candidate


def _classify_folder(image_root: Path, source_class_name: str) -> Tuple[str, str, bool]:
    """Return (crop, disease, is_healthy) for a source class folder."""
    if source_class_name == image_root.name:
        crop = _normalize_name(source_class_name)
        disease = ""
        is_healthy = source_class_name.strip().lower() in HEALTHY_TOKENS
        return crop, disease, is_healthy

    parts = re.split(r"[_.\-\s]+", source_class_name.strip("_ .-"))
    if len(parts) < 2:
        crop = _normalize_name(source_class_name)
        disease = ""
        is_healthy = source_class_name.strip().lower() in HEALTHY_TOKENS
        return crop, disease, is_healthy

    crop = _normalize_name(parts[0])
    disease = " ".join(_normalize_name(token) for token in parts[1:] if token).strip()
    is_healthy = disease.lower() in HEALTHY_TOKENS
    if is_healthy:
        disease = "healthy"
    return crop, disease, is_healthy


def _normalize_name(value: str) -> str:
    """Normalize a name token into readable spaced words."""
    cleaned = re.sub(r"\s+", " ", value.replace("_", " ").replace("-", " ")).strip()
    if not cleaned:
        return cleaned
    return " ".join(word.capitalize() for word in cleaned.split())


def canonical_label(crop: str, disease: str, is_healthy: bool) -> str:
    """Build the canonical label for a source class."""
    if is_healthy:
        return f"{crop}__healthy"
    if not disease:
        return crop
    return f"{crop}__{disease}"


def compute_md5(path: Path) -> str:
    """Compute the MD5 hash of a file's contents."""
    md5 = hashlib.md5()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(8192), b""):
            md5.update(chunk)
    return md5.hexdigest()


def scan_source(
    source_name: str,
    image_root: Path,
) -> Tuple[List[Dict[str, Any]], Dict[str, Any]]:
    """Recursively scan one source root into manifest rows and folder stats."""
    records: List[Dict[str, Any]] = []
    folder_tree: Dict[str, List[Path]] = OrderedDict()
    class_dirs = sorted(
        [d for d in image_root.iterdir() if d.is_dir()],
        key=lambda d: d.name,
    )

    if not class_dirs:
        folder_tree[str(image_root.name)] = []
        for image_path in sorted(image_root.iterdir(), key=lambda p: p.name):
            if image_path.is_file() and image_path.suffix.lower() in IMAGE_EXTENSIONS:
                folder_tree[str(image_root.name)].append(image_path)
    else:
        for class_dir in class_dirs:
            folder_tree[class_dir.name] = sorted(
                [f for f in class_dir.iterdir()
                 if f.is_file() and f.suffix.lower() in IMAGE_EXTENSIONS],
                key=lambda p: p.name,
            )

    for folder_name, image_paths in folder_tree.items():
        crop, disease, is_healthy = _classify_folder(image_root, folder_name)
        canonical = canonical_label(crop, disease, is_healthy)
        for image_path in image_paths:
            record = {
                "image_path": str(image_path),
                "source_dataset": source_name,
                "source_class_name": folder_name,
                "crop": crop,
                "disease": disease,
                "canonical_label": canonical,
                "is_healthy": str(is_healthy),
                "width": "",
                "height": "",
                "channels": "",
                "is_corrupt": "False",
                "hash_md5": "",
            }
            try:
                with Image.open(image_path) as img:
                    img.verify()
                with Image.open(image_path) as img:
                    width, height = img.size
                    mode = img.mode
                    channels = len(mode) if mode in ("RGB", "RGBA", "CMYK") else 1
                    record["width"] = str(width)
                    record["height"] = str(height)
                    record["channels"] = str(channels)
                record["hash_md5"] = compute_md5(image_path)
            except Exception as exc:
                record["is_corrupt"] = str(exc)[:200]

            records.append(record)

    return records, folder_tree


def find_duplicate_hashes(records: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Return duplicate-hash clusters without deleting any rows."""
    hash_groups: Dict[str, List[Dict[str, Any]]] = {}
    for record in records:
        digest = record["hash_md5"]
        if not digest:
            continue
        hash_groups.setdefault(digest, []).append(record)
    return [
        {
            "hash_md5": digest,
            "count": len(group),
            "paths": [entry["image_path"] for entry in group],
        }
        for digest, group in hash_groups.items()
        if len(group) > 1
    ]


def build_label_mapping(records: List[Dict[str, Any]]) -> List[Dict[str, str]]:
    """Build a deterministic label-mapping table per source class name."""
    mapping: Dict[Tuple[str, str], Dict[str, str]] = OrderedDict()
    for record in records:
        key = (record["source_dataset"], record["source_class_name"])
        if key in mapping:
            continue
        mapping[key] = {
            "source_dataset": record["source_dataset"],
            "source_class_name": record["source_class_name"],
            "crop": record["crop"],
            "disease": record["disease"],
            "canonical_label": record["canonical_label"],
            "is_healthy": record["is_healthy"],
        }
    return list(mapping.values())


def build_source_inventory(
    source_name: str,
    download_path: Optional[Path],
    image_root: Optional[Path],
    records: List[Dict[str, Any]],
    notes: str,
    status: str,
) -> Dict[str, str]:
    """Summarize counts for one source."""
    valid = sum(1 for record in records if record["is_corrupt"] == "False")
    corrupt = len(records) - valid
    classes = {record["source_class_name"] for record in records}
    final_notes = notes if status == "ok" else f"{status}: {notes}"
    return {
        "source_dataset": source_name,
        "download_path": str(download_path) if download_path else "",
        "detected_root": str(image_root) if image_root else "",
        "total_images": len(records),
        "valid_images": valid,
        "corrupt_images": corrupt,
        "num_classes": len(classes),
        "notes": final_notes,
    }


def write_manifest(
    records: List[Dict[str, Any]],
    manifest_path: Path,
) -> None:
    """Write the unified manifest CSV."""
    manifest_path.parent.mkdir(parents=True, exist_ok=True)
    with manifest_path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=MANIFEST_COLUMNS, lineterminator="\n")
        writer.writeheader()
        writer.writerows(records)


def write_inventory(inventory: List[Dict[str, str]], path: Path) -> None:
    """Write the source inventory CSV."""
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=INVENTORY_COLUMNS, lineterminator="\n")
        writer.writeheader()
        writer.writerows(inventory)


def write_label_mapping(mapping_rows: List[Dict[str, str]], path: Path) -> None:
    """Write the canonical label mapping CSV."""
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=MAPPING_COLUMNS, lineterminator="\n")
        writer.writeheader()
        writer.writerows(mapping_rows)


def build_report_context(
    records: List[Dict[str, Any]],
    inventory: List[Dict[str, str]],
    mapping_rows: List[Dict[str, str]],
    duplicates: List[Dict[str, Any]],
    folder_trees: Dict[str, Dict[str, List[Path]]],
) -> Dict[str, Any]:
    """Assemble summary statistics for the Markdown report."""
    total_found = len(records)
    valid_count = sum(1 for record in records if record["is_corrupt"] == "False")
    corrupt_count = total_found - valid_count
    crops = sorted({record["crop"] for record in records if record["crop"]})
    canonical_labels = sorted(
        {record["canonical_label"] for record in records if record["canonical_label"]}
    )
    per_dataset_classes = {
        row["source_dataset"]: sorted(
            {record["source_class_name"] for record in records if record["source_dataset"] == row["source_dataset"]}
        )
        for row in inventory
    }
    unmatched_sources = [
        record["source_class_name"]
        for record in records
        if not record["crop"] and not record["disease"]
    ]
    return {
        "total_datasets_scanned": len(inventory),
        "total_images_found": total_found,
        "total_valid_images": valid_count,
        "total_corrupt_images": corrupt_count,
        "total_duplicate_hashes": len(duplicates),
        "crops_covered": crops,
        "canonical_labels": canonical_labels,
        "label_mapping_coverage": len(mapping_rows),
        "per_dataset_classes": per_dataset_classes,
        "folder_trees": folder_trees,
        "unmatched_source_classes": sorted(set(unmatched_sources)),
        "duplicates": duplicates,
    }


def write_report(context: Dict[str, Any], report_path: Path) -> None:
    """Write the unified ingestion report."""
    report_path.parent.mkdir(parents=True, exist_ok=True)
    lines = [
        "# Unified Crop-Disease Ingestion Report",
        "",
        "## Summary",
        "",
        "| Metric | Value |",
        "|--------|-------|",
        f"| Total datasets scanned | {context['total_datasets_scanned']} |",
        f"| Total images found | {context['total_images_found']} |",
        f"| Total valid images | {context['total_valid_images']} |",
        f"| Total corrupt images | {context['total_corrupt_images']} |",
        f"| Total duplicate hashes | {context['total_duplicate_hashes']} |",
        f"| Crops covered | {len(context['crops_covered'])} |",
        f"| Canonical labels | {len(context['canonical_labels'])} |",
        f"| Label mapping coverage | {context['label_mapping_coverage']} |",
        "",
        "## Per-Dataset Class Counts",
        "",
        "| Source Dataset | Classes | Count |",
        "|----------------|---------|-------|",
    ]
    for source, classes in sorted(context["per_dataset_classes"].items()):
        lines.append(f"| {source} | {len(classes)} | {sum(len(context['folder_trees'].get(source, {}).get(name, [])) for name in classes)} |")

    lines += [
        "",
        "## Crops Covered",
        "",
    ]
    for crop in context["crops_covered"]:
        lines.append(f"- {crop}")

    lines += [
        "",
        "## Canonical Labels",
        "",
    ]
    for label in context["canonical_labels"]:
        lines.append(f"- {label}")

    lines += [
        "",
        "## Folder Structure Summary",
        "",
    ]
    for source, tree in sorted(context["folder_trees"].items()):
        lines.append(f"### {source}")
        for folder, files in tree.items():
            lines.append(f"- `{folder}/` ({len(files)} images)")
        lines.append("")

    lines += [
        "## Duplicate Hashes",
        "",
    ]
    if context["duplicates"]:
        for cluster in context["duplicates"]:
            lines.append(f"- `hash_md5={cluster['hash_md5']}` ({cluster['count']} files)")
    else:
        lines.append("- No duplicate hashes detected.")

    lines += [
        "",
        "## Unmatched Source Classes",
        "",
    ]
    if context["unmatched_source_classes"]:
        for name in context["unmatched_source_classes"]:
            lines.append(f"- `{name}`")
    else:
        lines.append("- None detected.")

    lines.append("")
    report_path.write_text("\n".join(lines), encoding="utf-8")


def run(
    output_dir: Optional[Path] = None,
    report_dir: Optional[Path] = None,
) -> Dict[str, Any]:
    """Download each source, scan it, and write the unified artifacts."""
    root = Path(__file__).resolve().parent.parent
    output_dir = output_dir or (root / "data" / "raw")
    report_dir = report_dir or (root / "reports")

    all_records: List[Dict[str, Any]] = []
    inventory: List[Dict[str, str]] = []
    folder_trees: Dict[str, Dict[str, List[Path]]] = {}

    for source in SOURCE_REGISTRY:
        source_name = source["source_dataset"]
        slug = source["kaggle_slug"]
        print(f"Downloading {source_name} ({slug})...")
        try:
            download_path = download_dataset(slug)
        except Exception as exc:
            print(f"  Skipping {source_name}: {exc}")
            inventory.append(
                build_source_inventory(source_name, None, None, [], source["notes"], "skipped")
            )
            folder_trees[source_name] = {}
            continue

        image_root = find_image_root(download_path)
        print(f"  Image root: {image_root}")
        records, tree = scan_source(source_name, image_root)
        folder_trees[source_name] = tree
        inventory.append(
            build_source_inventory(
                source_name, download_path, image_root, records, source["notes"], "ok",
            )
        )
        all_records.extend(records)
        print(f"  Scanned {len(records)} images")

    manifest_path = output_dir / "unified_crop_disease_manifest.csv"
    write_manifest(all_records, manifest_path)

    duplicates = find_duplicate_hashes(all_records)
    mapping_rows = build_label_mapping(all_records)
    inventory_path = output_dir / "dataset_source_inventory.csv"
    mapping_path = output_dir / "label_mapping_table.csv"
    write_inventory(inventory, inventory_path)
    write_label_mapping(mapping_rows, mapping_path)

    context = build_report_context(all_records, inventory, mapping_rows, duplicates, folder_trees)
    report_path = report_dir / "unified_dataset_ingestion_report.md"
    write_report(context, report_path)

    return {
        "manifest_path": str(manifest_path),
        "inventory_path": str(inventory_path),
        "mapping_path": str(mapping_path),
        "report_path": str(report_path),
        "records": all_records,
        "context": context,
    }


if __name__ == "__main__":
    result = run()
    print(f"Manifest: {result['manifest_path']}")
    print(f"Inventory: {result['inventory_path']}")
    print(f"Mapping: {result['mapping_path']}")
    print(f"Report: {result['report_path']}")
