"""Tests for scripts/07_ingest_pesticide_report.py."""

from __future__ import annotations

import csv
import hashlib
import importlib.util
import json
import shutil
from pathlib import Path
from typing import Any, Dict, List

import pytest
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas


PROJECT_ROOT = Path(__file__).resolve().parent.parent


def _load_ingest_module() -> Any:
    spec = importlib.util.spec_from_file_location(
        "ingest_pesticide_report", PROJECT_ROOT / "scripts" / "07_ingest_pesticide_report.py"
    )
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)  # type: ignore[union-attr]
    return module


ingest = _load_ingest_module()


def _make_pdf(tmp_path: Path, pages: List[str], filename: str = "test_report.pdf") -> Path:
    """Create a simple multi-page text PDF for tests."""
    pdf_path = tmp_path / filename
    c = canvas.Canvas(str(pdf_path), pagesize=letter)
    width, height = letter
    for idx, text in enumerate(pages, start=1):
        c.setFont("Helvetica-Bold", 14)
        c.drawString(50, height - 50, f"CHAPTER {idx}")
        c.setFont("Helvetica", 10)
        y = height - 80
        for line in text.splitlines():
            c.drawString(50, y, line)
            y -= 14
        c.showPage()
    c.save()
    return pdf_path


@pytest.fixture
def tmp_project(tmp_path: Path, monkeypatch: Any) -> Path:
    """Provide an isolated project directory with output dirs."""
    processed = tmp_path / "data" / "processed"
    reports = tmp_path / "reports"
    processed.mkdir(parents=True)
    reports.mkdir(parents=True)
    monkeypatch.setattr(ingest, "PROCESSED_DIR", processed)
    monkeypatch.setattr(ingest, "REPORTS_DIR", reports)
    monkeypatch.setattr(ingest, "CHUNKS_JSONL", processed / "pesticide_report_chunks.jsonl")
    monkeypatch.setattr(ingest, "FACTS_CSV", processed / "pesticide_report_facts.csv")
    monkeypatch.setattr(ingest, "REVIEW_CSV", processed / "pesticide_report_review_queue.csv")
    monkeypatch.setattr(ingest, "META_JSON", processed / "pesticide_report_ingestion_meta.json")
    monkeypatch.setattr(ingest, "ANALYSIS_MD", reports / "pesticide_report_analysis.md")
    monkeypatch.setattr(ingest, "QUALITY_MD", reports / "pesticide_report_extraction_quality.md")
    return tmp_path


def test_inspect_pdf_missing(tmp_project: Path) -> None:
    result = ingest.inspect_pdf(tmp_project / "nonexistent.pdf")
    assert result["readable"] is False
    assert result["reason"] == "file_not_found"


def test_inspect_pdf_readable(tmp_project: Path) -> None:
    pdf = _make_pdf(tmp_project, ["This is page one. It has advisory text for cotton aphid in Lahore.", "Page two."])
    result = ingest.inspect_pdf(pdf)
    assert result["readable"] is True
    assert result["page_count"] == 2
    assert result["total_characters"] > 0


def test_extract_pages_preserves_page_numbers(tmp_project: Path) -> None:
    pdf = _make_pdf(tmp_project, ["First page text.", "Second page text about wheat rust."])
    pages = ingest.extract_pages(pdf)
    assert [p["page"] for p in pages] == [1, 2]
    assert all(isinstance(p["text"], str) for p in pages)
    assert "second" in pages[1]["text"].lower()


def test_build_chunks_page_bounded(tmp_project: Path) -> None:
    pages = [
        {"page": 1, "text": "A" * 3000, "characters": 3000, "empty_text_layer": False},
        {"page": 2, "text": "B" * 3000, "characters": 3000, "empty_text_layer": False},
    ]
    chunks = ingest.build_chunks(pages, target_chars=1200, overlap_chars=150)
    pages_in_chunks = {c["page"] for c in chunks}
    assert pages_in_chunks == {1, 2}
    assert all(c["page"] in {1, 2} for c in chunks)
    assert all(c["chunk_id"].startswith("chunk_") for c in chunks)


def test_detect_section_carries_forward(tmp_project: Path) -> None:
    assert ingest.detect_section("CHAPTER 3\nSome body text", 1, "") == "CHAPTER 3"
    assert ingest.detect_section("Some body text", 2, "CHAPTER 3") == "CHAPTER 3"
    assert ingest.detect_section("Some body text", 5, "") == "page_5"


def test_extract_dose_unambiguous_only() -> None:
    text = "Apply Confidor 200 SL at 250 ml per acre for cotton whitefly control."
    dose, score = ingest._extract_dose(text)
    assert dose == "250 ml per acre"
    assert score == 1.0
    assert dose.lower() in text.lower()

    # Bare number should not be treated as dose.
    assert ingest._extract_dose("Apply 2 sprays.")[0] == ""


def test_facts_schema_and_no_invented_dose(tmp_project: Path) -> None:
    pdf = _make_pdf(
        tmp_project,
        [
            "CHAPTER 1\nCotton farmers in Lahore should apply Confidor 200 SL at 250 ml per acre against whitefly.",
        ],
    )
    result = ingest.run(pdf)
    assert result["status"] == "ok"
    assert result["facts"] > 0

    facts_path = ingest.FACTS_CSV
    with facts_path.open("r", encoding="utf-8", newline="") as fh:
        reader = csv.DictReader(fh)
        rows = list(reader)
    assert reader.fieldnames == ingest.FACT_FIELDS
    fact = rows[0]
    assert fact["crop"]
    assert fact["pest_or_disease"]
    assert fact["district"]
    assert fact["source_excerpt"]
    assert int(fact["source_page"]) == 1
    # Explicit dose must be verbatim in excerpt.
    if fact["explicit_dose_text"]:
        assert fact["explicit_dose_text"].lower() in fact["source_excerpt"].lower()


def test_review_queue_contains_ambiguous_dose(tmp_project: Path) -> None:
    pdf = _make_pdf(
        tmp_project,
        [
            "CHAPTER 1\nFor control of cotton whitefly in Lahore, imidacloprid is recommended. Follow label instructions.",
        ],
    )
    ingest.run(pdf)
    with ingest.REVIEW_CSV.open("r", encoding="utf-8", newline="") as fh:
        rows = list(csv.DictReader(fh))
    assert len(rows) > 0
    assert any(
        row["extraction_status"] == "ambiguous_dose" or not row["explicit_dose_text"]
        for row in rows
    )


def test_raw_pdf_unchanged(tmp_project: Path) -> None:
    pdf = _make_pdf(tmp_project, ["Original text."])
    before = hashlib.sha256(pdf.read_bytes()).hexdigest()
    ingest.run(pdf)
    after = hashlib.sha256(pdf.read_bytes()).hexdigest()
    assert before == after


def test_run_writes_all_outputs(tmp_project: Path) -> None:
    pdf = _make_pdf(tmp_project, ["Page one.", "Page two."])
    ingest.run(pdf)
    assert ingest.CHUNKS_JSONL.exists()
    assert ingest.FACTS_CSV.exists()
    assert ingest.REVIEW_CSV.exists()
    assert ingest.META_JSON.exists()
    assert ingest.ANALYSIS_MD.exists()
    assert ingest.QUALITY_MD.exists()


def test_jsonl_chunk_ids_unique(tmp_project: Path) -> None:
    pdf = _make_pdf(tmp_project, ["Page one with enough text to possibly create a chunk. " * 20])
    ingest.run(pdf)
    with ingest.CHUNKS_JSONL.open("r", encoding="utf-8") as fh:
        ids = [json.loads(line)["chunk_id"] for line in fh if line.strip()]
    assert len(ids) == len(set(ids))


def test_real_pdf_extracts_facts() -> None:
    """Run against the configured real PDF if available."""
    pdf_path = PROJECT_ROOT / ingest.DEFAULT_PDF_PATH
    if not pdf_path.exists():
        pytest.skip("Real pesticide report PDF not found")
    # Copy to temp to avoid touching original.
    result = ingest.run(pdf_path)
    assert result["status"] == "ok"
    assert result["facts"] > 0
    assert result["chunks"] > 0
