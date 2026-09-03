"""Validate pesticide report extraction outputs.

Can be imported as a module (validate(...)) or run as a script. Missing source
artifacts are reported as INFO, not failure, so CI stays green when the PDF has
not been provided.
"""

from __future__ import annotations

import csv
import json
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Set, Tuple


FACT_FIELDS = [
    "fact_id",
    "category",
    "crop",
    "pest_or_disease",
    "district",
    "date_or_period",
    "advisory_text",
    "pesticide_name",
    "active_ingredient",
    "formulation",
    "explicit_dose_text",
    "safety_text",
    "quality_control_status",
    "source_report_title",
    "source_report_year",
    "source_filename",
    "source_page",
    "source_section",
    "source_excerpt",
    "extraction_status",
    "confidence",
    "reviewed",
]

ALLOWED_CATEGORIES = {
    "pest_warning",
    "crop_disease_warning",
    "pesticide_quality_control",
    "pesticide_safety",
    "inspection",
    "laboratory_result",
    "general_agricultural_advisory",
}

REQUIRED_FILES = [
    "pesticide_report_facts.csv",
    "pesticide_report_chunks.jsonl",
    "pesticide_report_review_queue.csv",
    "pesticide_report_ingestion_meta.json",
]


def _read_csv(path: Path) -> Tuple[List[str], List[Dict[str, str]]]:
    with path.open("r", encoding="utf-8", newline="") as fh:
        reader = csv.DictReader(fh)
        rows = list(reader)
        return reader.fieldnames or [], rows


def _read_jsonl(path: Path) -> List[Dict[str, Any]]:
    items: List[Dict[str, Any]] = []
    with path.open("r", encoding="utf-8") as fh:
        for line in fh:
            line = line.strip()
            if not line:
                continue
            items.append(json.loads(line))
    return items


def validate(
    processed_dir: Path, reports_dir: Path
) -> Dict[str, Any]:
    """Validate all generated artifacts.

    Returns a dict with ``success`` (bool), ``errors`` (list), ``info`` (list),
    and summary counters. Missing source data is reported as INFO, not an error.
    """
    errors: List[str] = []
    info: List[str] = []

    missing_files = [
        name
        for name in REQUIRED_FILES
        if not (processed_dir / name).exists()
    ]
    if missing_files:
        info.append(
            f"Missing source artifacts (run 07_ingest_pesticide_report.py first): {missing_files}"
        )
        return {
            "success": True,
            "errors": errors,
            "info": info,
            "facts": 0,
            "chunks": 0,
            "review_queue": 0,
            "dose_integrity_violations": 0,
        }

    meta_path = processed_dir / "pesticide_report_ingestion_meta.json"
    with meta_path.open("r", encoding="utf-8") as fh:
        meta = json.load(fh)

    if not meta.get("readable", False):
        info.append(
            "Source PDF was not readable; validation treats empty artifacts as acceptable."
        )
        return {
            "success": True,
            "errors": errors,
            "info": info,
            "facts": 0,
            "chunks": 0,
            "review_queue": 0,
            "dose_integrity_violations": 0,
        }

    page_count = meta.get("page_count", 0)

    # --- facts.csv ---
    facts_path = processed_dir / "pesticide_report_facts.csv"
    headers, fact_rows = _read_csv(facts_path)

    if headers != FACT_FIELDS:
        errors.append(
            f"facts.csv headers mismatch: expected {FACT_FIELDS}, got {headers}"
        )

    fact_ids: Set[str] = set()
    for idx, row in enumerate(fact_rows, start=2):
        fact_id = row.get("fact_id", "").strip()
        if not fact_id:
            errors.append(f"facts.csv row {idx}: empty fact_id")
        elif fact_id in fact_ids:
            errors.append(f"facts.csv row {idx}: duplicate fact_id {fact_id}")
        else:
            fact_ids.add(fact_id)

        if not row.get("source_excerpt", "").strip():
            errors.append(f"facts.csv {fact_id}: missing source_excerpt")
        if not row.get("source_filename", "").strip():
            errors.append(f"facts.csv {fact_id}: missing source_filename")

        page_raw = row.get("source_page", "").strip()
        try:
            page = int(page_raw)
        except ValueError:
            errors.append(f"facts.csv {fact_id}: source_page is not an integer ({page_raw})")
            page = 0
        if page <= 0:
            errors.append(f"facts.csv {fact_id}: source_page must be positive ({page})")
        elif page_count and page > page_count:
            errors.append(
                f"facts.csv {fact_id}: source_page {page} exceeds metadata page_count {page_count}"
            )

        category = row.get("category", "").strip()
        if category not in ALLOWED_CATEGORIES:
            errors.append(f"facts.csv {fact_id}: invalid category '{category}'")

        confidence_raw = row.get("confidence", "").strip()
        try:
            confidence = float(confidence_raw)
            if not 0.0 <= confidence <= 1.0:
                errors.append(
                    f"facts.csv {fact_id}: confidence {confidence} out of range [0,1]"
                )
        except ValueError:
            errors.append(
                f"facts.csv {fact_id}: confidence is not numeric ({confidence_raw})"
            )

        dose = row.get("explicit_dose_text", "").strip()
        excerpt = row.get("source_excerpt", "")
        if dose and dose.lower() not in excerpt.lower():
            errors.append(
                f"facts.csv {fact_id}: explicit_dose_text is not a verbatim substring of source_excerpt"
            )

    # --- chunks.jsonl ---
    chunks_path = processed_dir / "pesticide_report_chunks.jsonl"
    try:
        chunks = _read_jsonl(chunks_path)
    except json.JSONDecodeError as exc:
        errors.append(f"chunks.jsonl: invalid JSONL - {exc}")
        chunks = []

    chunk_ids: Set[str] = set()
    for idx, chunk in enumerate(chunks, start=1):
        chunk_id = chunk.get("chunk_id")
        if not chunk_id:
            errors.append(f"chunks.jsonl line {idx}: missing chunk_id")
        elif chunk_id in chunk_ids:
            errors.append(f"chunks.jsonl line {idx}: duplicate chunk_id {chunk_id}")
        else:
            chunk_ids.add(chunk_id)
        if not isinstance(chunk.get("page"), int) or chunk.get("page", 0) <= 0:
            errors.append(f"chunks.jsonl {chunk_id}: missing or invalid page reference")

    # --- review_queue.csv ---
    review_path = processed_dir / "pesticide_report_review_queue.csv"
    _, review_rows = _read_csv(review_path)
    review_ids = {row.get("fact_id", "").strip() for row in review_rows if row.get("fact_id", "").strip()}
    missing_in_facts = review_ids - fact_ids
    if missing_in_facts:
        errors.append(
            f"review_queue.csv contains fact_ids not present in facts.csv: {sorted(missing_in_facts)}"
        )

    dose_integrity_violations = sum(
        1
        for row in fact_rows
        if row.get("explicit_dose_text", "").strip()
        and row.get("explicit_dose_text", "").strip().lower()
        not in row.get("source_excerpt", "").lower()
    )

    summary = {
        "success": len(errors) == 0,
        "errors": errors,
        "info": info,
        "facts": len(fact_rows),
        "chunks": len(chunks),
        "review_queue": len(review_rows),
        "dose_integrity_violations": dose_integrity_violations,
    }
    return summary


def _write_quality_report(reports_dir: Path, result: Dict[str, Any]) -> None:
    reports_dir.mkdir(parents=True, exist_ok=True)
    path = reports_dir / "pesticide_report_extraction_quality.md"
    lines = [
        "# Pesticide Report Extraction Quality (Validator)",
        "",
        f"**Validated at:** {datetime.now(timezone.utc).isoformat()} UTC",
        "",
        f"- Overall success: {'PASS' if result['success'] else 'FAIL'}",
        f"- Facts: {result['facts']}",
        f"- Chunks: {result['chunks']}",
        f"- Review queue: {result['review_queue']}",
        f"- Dose integrity violations: {result['dose_integrity_violations']}",
        "",
    ]
    if result["info"]:
        lines.extend(["## Info", ""])
        for item in result["info"]:
            lines.append(f"- {item}")
        lines.append("")
    if result["errors"]:
        lines.extend(["## Errors", ""])
        for err in result["errors"]:
            lines.append(f"- {err}")
    else:
        lines.extend(["## Errors", "", "No validation errors found.", ""])
    with path.open("w", encoding="utf-8") as fh:
        fh.write("\n".join(lines))


def main() -> int:
    project_root = Path(__file__).resolve().parent.parent
    processed_dir = project_root / "data" / "processed"
    reports_dir = project_root / "reports"
    result = validate(processed_dir, reports_dir)
    _write_quality_report(reports_dir, result)
    print(json.dumps(result, indent=2))
    return 0 if result["success"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
