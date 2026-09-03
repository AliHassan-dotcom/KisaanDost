"""Tests for scripts/08_validate_pesticide_report.py."""

from __future__ import annotations

import csv
import importlib.util
import json
from pathlib import Path
from typing import Any

import pytest


PROJECT_ROOT = Path(__file__).resolve().parent.parent


def _load_validator_module() -> Any:
    spec = importlib.util.spec_from_file_location(
        "validate_pesticide_report", PROJECT_ROOT / "scripts" / "08_validate_pesticide_report.py"
    )
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)  # type: ignore[union-attr]
    return module


validate = _load_validator_module()


def _write_csv(path: Path, headers: list[str], rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as fh:
        writer = csv.DictWriter(fh, fieldnames=headers, lineterminator="\n")
        writer.writeheader()
        for row in rows:
            writer.writerow(row)


def _write_jsonl(path: Path, items: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as fh:
        for item in items:
            fh.write(json.dumps(item) + "\n")


def _make_meta(processed_dir: Path, readable: bool = True, page_count: int = 5) -> None:
    processed_dir.mkdir(parents=True, exist_ok=True)
    meta = {
        "readable": readable,
        "page_count": page_count,
        "num_facts": 1,
        "num_chunks": 1,
        "warnings": [],
    }
    with (processed_dir / "pesticide_report_ingestion_meta.json").open("w", encoding="utf-8") as fh:
        json.dump(meta, fh)


def test_missing_source_info_not_failure(tmp_path: Path) -> None:
    result = validate.validate(tmp_path / "processed", tmp_path / "reports")
    assert result["success"] is True
    assert any("Missing source artifacts" in info for info in result["info"])


def test_schema_validation_passes(tmp_path: Path) -> None:
    processed = tmp_path / "processed"
    reports = tmp_path / "reports"
    _make_meta(processed, readable=True, page_count=5)
    _write_csv(
        processed / "pesticide_report_facts.csv",
        validate.FACT_FIELDS,
        [
            {
                "fact_id": "fact_00001",
                "category": "pest_warning",
                "crop": "cotton",
                "pest_or_disease": "whitefly",
                "district": "Lahore",
                "date_or_period": "2024-25",
                "advisory_text": "Use Confidor 200 SL at 250 ml per acre.",
                "pesticide_name": "Confidor",
                "active_ingredient": "imidacloprid",
                "formulation": "SL",
                "explicit_dose_text": "250 ml per acre",
                "safety_text": "Use protective clothing.",
                "quality_control_status": "",
                "source_report_title": "Annual Report",
                "source_report_year": "2024-25",
                "source_filename": "report.pdf",
                "source_page": "1",
                "source_section": "Chapter 1",
                "source_excerpt": "Use Confidor 200 SL at 250 ml per acre.",
                "extraction_status": "extracted",
                "confidence": "0.85",
                "reviewed": "false",
            }
        ],
    )
    _write_csv(processed / "pesticide_report_review_queue.csv", validate.FACT_FIELDS, [])
    _write_jsonl(
        processed / "pesticide_report_chunks.jsonl",
        [{"chunk_id": "chunk_00001", "page": 1, "section": "Chapter 1", "text": "Use Confidor."}],
    )
    result = validate.validate(processed, reports)
    assert result["success"] is True
    assert result["errors"] == []


def test_dose_integrity_failure(tmp_path: Path) -> None:
    processed = tmp_path / "processed"
    reports = tmp_path / "reports"
    _make_meta(processed, readable=True, page_count=5)
    row = {
        "fact_id": "fact_00001",
        "category": "pest_warning",
        "crop": "cotton",
        "pest_or_disease": "whitefly",
        "district": "Lahore",
        "date_or_period": "",
        "advisory_text": "",
        "pesticide_name": "",
        "active_ingredient": "",
        "formulation": "",
        "explicit_dose_text": "999 ml per acre",
        "safety_text": "",
        "quality_control_status": "",
        "source_report_title": "",
        "source_report_year": "",
        "source_filename": "report.pdf",
        "source_page": "1",
        "source_section": "",
        "source_excerpt": "Use Confidor 200 SL at 250 ml per acre.",
        "extraction_status": "extracted",
        "confidence": "0.85",
        "reviewed": "false",
    }
    _write_csv(processed / "pesticide_report_facts.csv", validate.FACT_FIELDS, [row])
    _write_csv(processed / "pesticide_report_review_queue.csv", validate.FACT_FIELDS, [])
    _write_jsonl(processed / "pesticide_report_chunks.jsonl", [])
    result = validate.validate(processed, reports)
    assert result["success"] is False
    assert any("explicit_dose_text is not a verbatim substring" in err for err in result["errors"])
    assert result["dose_integrity_violations"] == 1


def test_invalid_category_and_confidence(tmp_path: Path) -> None:
    processed = tmp_path / "processed"
    reports = tmp_path / "reports"
    _make_meta(processed, readable=True, page_count=5)
    row = {
        "fact_id": "fact_00001",
        "category": "invalid_category",
        "crop": "",
        "pest_or_disease": "",
        "district": "",
        "date_or_period": "",
        "advisory_text": "",
        "pesticide_name": "",
        "active_ingredient": "",
        "formulation": "",
        "explicit_dose_text": "",
        "safety_text": "",
        "quality_control_status": "",
        "source_report_title": "",
        "source_report_year": "",
        "source_filename": "report.pdf",
        "source_page": "1",
        "source_section": "",
        "source_excerpt": "Some excerpt.",
        "extraction_status": "extracted",
        "confidence": "1.5",
        "reviewed": "false",
    }
    _write_csv(processed / "pesticide_report_facts.csv", validate.FACT_FIELDS, [row])
    _write_csv(processed / "pesticide_report_review_queue.csv", validate.FACT_FIELDS, [])
    _write_jsonl(processed / "pesticide_report_chunks.jsonl", [])
    result = validate.validate(processed, reports)
    assert result["success"] is False
    assert any("invalid category" in err for err in result["errors"])
    assert any("confidence" in err for err in result["errors"])


def test_review_queue_subset_of_facts(tmp_path: Path) -> None:
    processed = tmp_path / "processed"
    reports = tmp_path / "reports"
    _make_meta(processed, readable=True, page_count=5)
    base_row = {
        "fact_id": "fact_00001",
        "category": "pest_warning",
        "crop": "cotton",
        "pest_or_disease": "whitefly",
        "district": "Lahore",
        "date_or_period": "",
        "advisory_text": "",
        "pesticide_name": "",
        "active_ingredient": "",
        "formulation": "",
        "explicit_dose_text": "",
        "safety_text": "",
        "quality_control_status": "",
        "source_report_title": "",
        "source_report_year": "",
        "source_filename": "report.pdf",
        "source_page": "1",
        "source_section": "",
        "source_excerpt": "Excerpt.",
        "extraction_status": "extracted",
        "confidence": "0.85",
        "reviewed": "false",
    }
    _write_csv(processed / "pesticide_report_facts.csv", validate.FACT_FIELDS, [base_row])
    _write_csv(
        processed / "pesticide_report_review_queue.csv",
        validate.FACT_FIELDS,
        [{**base_row, "fact_id": "fact_99999"}],
    )
    _write_jsonl(processed / "pesticide_report_chunks.jsonl", [])
    result = validate.validate(processed, reports)
    assert result["success"] is False
    assert any("fact_ids not present in facts.csv" in err for err in result["errors"])
