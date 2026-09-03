"""Download and index the PlantVillage dataset from Kaggle.

Steps:
1. Download via kagglehub (cached after first run).
2. Locate the image root automatically (skip nested duplicates).
3. Scan all image files and validate readability with PIL.
4. Parse class folder names into crop/disease/healthy fields.
5. Build a manifest CSV with deterministic ordering.
6. Separate clean and corrupt records.

Outputs:
- ``data/raw/plantvillage_manifest.csv`` — clean manifest (is_corrupt=False only)
- ``reports/plantvillage_dataset_report.md`` — full scan report

Stdlib + Pillow + kagglehub only.
"""

from __future__ import annotations

import csv
import os
import re
from collections import Counter
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

from PIL import Image

DATASET_HANDLE = "emmarex/plantdisease"
SOURCE_DATASET = "PlantVillage"
IMAGE_EXTENSIONS = {".jpg", ".jpeg", ".png", ".bmp", ".tiff", ".tif", ".gif"}


def download_dataset() -> Path:
    import kagglehub
    return Path(kagglehub.dataset_download(DATASET_HANDLE))


def find_image_root(download_dir: Path) -> Path:
    """Walk from the download root to find the actual class-folder root.

    The Kaggle zip often double-nests: ``PlantVillage/PlantVillage/<classes>``.
    We use the outermost level that has class subdirectories and skip the
    nested duplicate.
    """
    candidate = download_dir
    # Walk into single-child directories until we hit one with multiple subdirs
    while True:
        children = [d for d in candidate.iterdir() if d.is_dir()]
        if len(children) == 1:
            candidate = children[0]
        else:
            break

    # If there's a nested duplicate (same-named subdir with same class folders),
    # prefer the outer level.
    for child in candidate.iterdir():
        if child.is_dir() and child.name == candidate.name:
            # Check if inner has same subdirs
            outer_dirs = {d.name for d in candidate.iterdir() if d.is_dir() and d.name != child.name}
            inner_dirs = {d.name for d in child.iterdir() if d.is_dir()}
            if outer_dirs and outer_dirs == inner_dirs:
                return candidate  # use outer, inner is duplicate

    return candidate


def parse_class_name(folder_name: str) -> Tuple[str, str, bool]:
    """Parse a PlantVillage class folder name into (crop, disease, is_healthy).

    The dataset uses inconsistent separators between crop and disease:
    - ``Pepper__bell___Bacterial_spot`` (triple underscore, ``__`` within crop)
    - ``Potato___Early_blight`` (triple underscore)
    - ``Tomato_Bacterial_spot`` (single underscore)
    - ``Tomato__Target_Spot`` (double underscore)

    Crop names use lowercase after ``__`` (e.g. ``Pepper__bell``); disease
    segments start with uppercase. The regex captures this pattern.
    """
    m = re.match(r"^([A-Z][a-z]*(?:__[a-z]+)?)_+(.+)$", folder_name)
    if m:
        crop_raw = m.group(1)
        disease_raw = m.group(2)
    else:
        crop_raw = folder_name
        disease_raw = ""

    crop = re.sub(r"\s+", " ", crop_raw.replace("__", " ").replace("_", " ")).strip()
    disease = re.sub(r"\s+", " ", disease_raw.replace("_", " ")).strip()

    is_healthy = disease.lower() == "healthy"

    return crop, disease, is_healthy


def scan_images(image_root: Path) -> List[Dict[str, Any]]:
    """Scan all images under *image_root*, one class per subdirectory."""
    records: List[Dict[str, Any]] = []
    class_dirs = sorted(
        [d for d in image_root.iterdir() if d.is_dir()],
        key=lambda d: d.name,
    )

    for class_dir in class_dirs:
        folder_name = class_dir.name
        crop, disease, is_healthy = parse_class_name(folder_name)
        label = folder_name  # preserve original folder name as label

        files = sorted(
            [
                f
                for f in class_dir.iterdir()
                if f.is_file() and f.suffix.lower() in IMAGE_EXTENSIONS
            ],
            key=lambda f: f.name,
        )

        for img_path in files:
            record = {
                "image_path": str(img_path),
                "label": label,
                "class_name": folder_name,
                "source_dataset": SOURCE_DATASET,
                "crop": crop,
                "disease": disease,
                "is_healthy": str(is_healthy),
                "split": "",  # assigned later
                "width": "",
                "height": "",
                "channels": "",
                "is_corrupt": "False",
            }

            try:
                with Image.open(img_path) as img:
                    img.verify()
                # Re-open after verify (verify closes the image)
                with Image.open(img_path) as img:
                    w, h = img.size
                    mode = img.mode
                    channels = len(mode) if mode in ("RGB", "RGBA", "CMYK") else 1
                    if mode == "RGBA":
                        channels = 3  # treat alpha as non-essential
                    record["width"] = str(w)
                    record["height"] = str(h)
                    record["channels"] = str(channels)
                    if channels == 1:
                        record["is_corrupt"] = "grayscale"
            except Exception as exc:
                record["is_corrupt"] = str(exc)[:200]

            records.append(record)

    return records


def build_manifest(
    records: List[Dict[str, Any]],
    output_dir: Path,
) -> Dict[str, Any]:
    """Write the clean manifest and return summary stats."""
    output_dir.mkdir(parents=True, exist_ok=True)
    manifest_path = output_dir / "plantvillage_manifest.csv"

    clean = [r for r in records if r["is_corrupt"] == "False"]
    corrupt = [r for r in records if r["is_corrupt"] != "False"]

    fieldnames = [
        "image_path",
        "label",
        "class_name",
        "source_dataset",
        "crop",
        "disease",
        "is_healthy",
        "split",
        "width",
        "height",
        "channels",
        "is_corrupt",
    ]

    with manifest_path.open("w", encoding="utf-8", newline="") as fh:
        writer = csv.DictWriter(fh, fieldnames=fieldnames, lineterminator="\n")
        writer.writeheader()
        writer.writerows(clean)

    return {
        "manifest_path": str(manifest_path),
        "total_scanned": len(records),
        "total_clean": len(clean),
        "total_corrupt": len(corrupt),
        "corrupt_records": corrupt,
    }


def compute_report_stats(
    records: List[Dict[str, Any]],
    clean: List[Dict[str, Any]],
) -> Dict[str, Any]:
    """Compute statistics for the report."""
    classes = sorted(set(r["class_name"] for r in records))
    class_counts = Counter(r["class_name"] for r in clean)
    crop_counts = Counter(r["crop"] for r in clean)

    widths = [int(r["width"]) for r in clean if r["width"]]
    heights = [int(r["height"]) for r in clean if r["height"]]
    size_counter = Counter(
        f"{r['width']}x{r['height']}" for r in clean if r["width"]
    )
    grayscale = [r for r in clean if r["is_corrupt"] == "grayscale"]
    channel_counter = Counter(r["channels"] for r in clean if r["channels"])

    corrupt_reasons = Counter(
        r["is_corrupt"] for r in records if r["is_corrupt"] not in ("False", "grayscale")
    )

    top10 = class_counts.most_common(10)

    return {
        "classes": classes,
        "num_classes": len(classes),
        "class_counts": dict(class_counts.most_common()),
        "crop_counts": dict(crop_counts.most_common()),
        "total_scanned": len(records),
        "total_clean": len(clean),
        "total_corrupt": len(records) - len(clean),
        "size_distribution": dict(size_counter.most_common(10)),
        "width_range": (min(widths), max(widths)) if widths else (0, 0),
        "height_range": (min(heights), max(heights)) if heights else (0, 0),
        "top10_classes": top10,
        "grayscale_count": len(grayscale),
        "channel_distribution": dict(channel_counter),
        "corrupt_reasons": dict(corrupt_reasons),
    }


def write_report(
    stats: Dict[str, Any],
    image_root: Path,
    report_path: Path,
) -> None:
    """Write the dataset report in Markdown."""
    report_path.parent.mkdir(parents=True, exist_ok=True)

    lines = [
        "# PlantVillage Dataset Report",
        "",
        f"**Source:** Kaggle `{DATASET_HANDLE}`",
        f"**Local root:** `{image_root}`",
        f"**Source dataset tag:** `{SOURCE_DATASET}`",
        "",
        "## Summary",
        "",
        f"| Metric | Value |",
        f"|--------|-------|",
        f"| Total images scanned | {stats['total_scanned']} |",
        f"| Valid (clean) images | {stats['total_clean']} |",
        f"| Corrupt / unreadable | {stats['total_corrupt']} |",
        f"| Classes | {stats['num_classes']} |",
        f"| Crops | {len(stats['crop_counts'])} |",
        f"| Grayscale (flagged) | {stats['grayscale_count']} |",
        "",
        "## Class Distribution",
        "",
        "| Class | Count |",
        "|-------|-------|",
    ]

    for cls, count in sorted(stats["class_counts"].items()):
        lines.append(f"| {cls} | {count} |")

    lines += [
        "",
        "## Crop Distribution",
        "",
        "| Crop | Count |",
        "|------|-------|",
    ]
    for crop, count in sorted(stats["crop_counts"].items()):
        lines.append(f"| {crop} | {count} |")

    lines += [
        "",
        "## Top 10 Largest Classes",
        "",
        "| Rank | Class | Count |",
        "|------|-------|-------|",
    ]
    for i, (cls, count) in enumerate(stats["top10_classes"], 1):
        lines.append(f"| {i} | {cls} | {count} |")

    lines += [
        "",
        "## Image Size Distribution",
        "",
        f"- Width range: {stats['width_range'][0]} - {stats['width_range'][1]}",
        f"- Height range: {stats['height_range'][0]} - {stats['height_range'][1]}",
        "",
        "| Size (WxH) | Count |",
        "|-------------|-------|",
    ]
    for size, count in sorted(stats["size_distribution"].items()):
        lines.append(f"| {size} | {count} |")

    lines += [
        "",
        "## Channel Distribution",
        "",
        "| Channels | Count |",
        "|----------|-------|",
    ]
    for ch, count in sorted(stats["channel_distribution"].items()):
        lines.append(f"| {ch} | {count} |")

    if stats["corrupt_reasons"]:
        lines += [
            "",
            "## Corrupt Image Reasons",
            "",
            "| Reason | Count |",
            "|--------|-------|",
        ]
        for reason, count in sorted(stats["corrupt_reasons"].items()):
            lines.append(f"| {reason[:80]} | {count} |")

    lines += [
        "",
        "## Folder Structure",
        "",
        f"Image root: `{image_root}`",
        "",
    ]
    for cls in stats["classes"]:
        count = stats["class_counts"].get(cls, 0)
        lines.append(f"- `{cls}/` ({count} images)")

    lines += [
        "",
        "## Notes",
        "",
        "- Class names preserved verbatim from source folder names.",
        "- `crop` and `disease` fields parsed from folder name using `___` / `__` separators.",
        "- `is_healthy = True` when disease field equals 'healthy' (case-insensitive).",
        "- Grayscale images flagged but NOT excluded from clean manifest (channels=1).",
        "- Train/val/test split column left empty for downstream assignment.",
        "- Nested duplicate `PlantVillage/PlantVillage/` folder detected and skipped.",
    ]

    with report_path.open("w", encoding="utf-8") as fh:
        fh.write("\n".join(lines) + "\n")


def run(output_dir: Optional[Path] = None, report_dir: Optional[Path] = None) -> Dict[str, Any]:
    """Full pipeline: download, scan, build manifest, write report."""
    root = Path(__file__).resolve().parent.parent
    output_dir = output_dir or (root / "data" / "raw")
    report_dir = report_dir or (root / "reports")

    print("Downloading dataset...")
    download_dir = download_dataset()
    print(f"  Downloaded to: {download_dir}")

    image_root = find_image_root(download_dir)
    print(f"  Image root: {image_root}")

    print("Scanning images...")
    records = scan_images(image_root)
    print(f"  Scanned {len(records)} images")

    print("Building manifest...")
    result = build_manifest(records, output_dir)
    clean = [r for r in records if r["is_corrupt"] == "False"]
    print(f"  Clean: {result['total_clean']}, Corrupt: {result['total_corrupt']}")

    print("Computing stats...")
    stats = compute_report_stats(records, clean)

    report_path = report_dir / "plantvillage_dataset_report.md"
    print("Writing report...")
    write_report(stats, image_root, report_path)
    print(f"  Report: {report_path}")

    return {
        **result,
        "stats": stats,
        "image_root": str(image_root),
        "report_path": str(report_path),
    }


if __name__ == "__main__":
    result = run()
    print(f"\nDone. Manifest: {result['manifest_path']}")
    print(f"  Total: {result['total_scanned']}, Clean: {result['total_clean']}, "
          f"Corrupt: {result['total_corrupt']}")
