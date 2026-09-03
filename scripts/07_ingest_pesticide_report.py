"""Ingest the Punjab pesticide annual report into source-traceable facts.

Reads the PDF at the configured path and writes:
  - data/processed/pesticide_report_chunks.jsonl
  - data/processed/pesticide_report_facts.csv
  - data/processed/pesticide_report_review_queue.csv
  - data/processed/pesticide_report_ingestion_meta.json
  - reports/pesticide_report_analysis.md
  - reports/pesticide_report_extraction_quality.md

The source PDF is never modified.
"""

from __future__ import annotations

import csv
import hashlib
import json
import re
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import pdfplumber


# ---------------------------------------------------------------------------
# Paths
# ---------------------------------------------------------------------------
PROJECT_ROOT = Path(__file__).resolve().parent.parent
DEFAULT_PDF_PATH = Path("Kisaan_Dost_Data/Annual Report 2024-25_copy.pdf")
FALLBACK_PDF_PATH = Path("../Kisaan_Dost_Data/Annual Report 2024-25_copy.pdf")
PROCESSED_DIR = PROJECT_ROOT / "data" / "processed"
REPORTS_DIR = PROJECT_ROOT / "reports"

CHUNKS_JSONL = PROCESSED_DIR / "pesticide_report_chunks.jsonl"
FACTS_CSV = PROCESSED_DIR / "pesticide_report_facts.csv"
REVIEW_CSV = PROCESSED_DIR / "pesticide_report_review_queue.csv"
META_JSON = PROCESSED_DIR / "pesticide_report_ingestion_meta.json"
ANALYSIS_MD = REPORTS_DIR / "pesticide_report_analysis.md"
QUALITY_MD = REPORTS_DIR / "pesticide_report_extraction_quality.md"

SOURCE_TITLE = "Pest Warning and Quality Control of Pesticides Annual Report"
SOURCE_YEAR = "2024-25"
SOURCE_FILENAME = "Annual Report 2024-25_copy.pdf"


# ---------------------------------------------------------------------------
# Schema
# ---------------------------------------------------------------------------
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


# ---------------------------------------------------------------------------
# Knowledge lists (keyword matching)
# ---------------------------------------------------------------------------
CROP_KEYWORDS = {
    "cotton": ["cotton", "kapas"],
    "wheat": ["wheat", "gandum"],
    "rice": ["rice", "paddy"],
    "sugarcane": ["sugarcane", "ganna"],
    "maize": ["maize", "corn", "makai"],
    "citrus": ["citrus", "kinnow", "orange", "lemon"],
    "mango": ["mango"],
    "vegetables": ["vegetable", "tomato", "potato", "brinjal", "okra", "chilli"],
    "pulses": ["pulse", "gram", "lentil"],
    "oilseeds": ["oilseed", "mustard", "canola", "sunflower"],
}

PEST_KEYWORDS = {
    "whitefly": ["whitefly", "white fly"],
    "aphid": ["aphid", "aphids"],
    "jassid": ["jassid", "leafhopper"],
    "thrips": ["thrips"],
    "bollworm": ["bollworm", "pink bollworm", "spotted bollworm"],
    "armyworm": ["armyworm", "army worm"],
    "borer": ["stem borer", "shoot borer", "fruit borer"],
    "mites": ["mite", "mites"],
    "dusky bug": ["dusky bug"],
    "mealybug": ["mealybug", "mealy bug"],
    "rust": ["rust", "leaf rust", "yellow rust", "brown rust"],
    "blast": ["blast"],
    "blight": ["blight", "leaf blight"],
    "bacterial spot": ["bacterial spot"],
    "mildew": ["mildew", "powdery mildew", "downy mildew"],
}

DISTRICTS = [
    "attock", "bahawalnagar", "bahawalpur", "bhakkar", "chiniot", "deragazi",
    "faisalabad", "gujranwala", "gujrat", "hafizabad", "jhang", "jhelum",
    "kasur", "khanewal", "khushab", "lahore", "layyah", "lodhran",
    "mandibahauddin", "mianwali", "multan", "muzaffargarh", "nankana",
    "narowal", "okara", "pakpattan", "rahimyarkhan", "rajanpur",
    "rawalpindi", "sahiwal", "sargodha", "sheikhupura", "sialkot",
    "tobsatehsingh", "vehari", "dg khan", "dera ghazi khan",
]

PESTICIDE_KEYWORDS = [
    "insecticide", "fungicide", "herbicide", "acaricide", "nematicide",
    "pyrethroid", "neonicotinoid", "organophosphate", "carbamate",
    "chlorantraniliprole", "emamectin", "spinosad", "abamectin",
    "imidacloprid", "thiamethoxam", "acetamiprid", "bifenthrin",
    "lambda-cyhalothrin", "cypermethrin", "deltamethrin", "profenophos",
    "triazophos", "chlorpyrifos", "cartap", "fipronil", "flubendiamide",
    "lufenuron", "novaluron", "indoxacarb", "methoxyfenozide", "spinetoram",
    "azoxystrobin", "carbendazim", "mancozeb", "metalaxyl", "propiconazole",
    "tebuconazole", "thiophanate-methyl", "tricyclazole", "validamycin",
    "glyphosate", "atrazine", "s-metolachlor", "pendimethalin", "bentazon",
    "2,4-d", "dicamba", "paraquat",
]

SAFETY_KEYWORDS = [
    "safety", "precaution", "hazard", "toxic", "poison", "ppe",
    "protective clothing", "re-entry", "waiting period", "phi",
    "pre-harvest interval", "environmental hazard", "bee", "pollinator",
    "avoid drift", "do not mix", "antidote", "first aid",
]

QC_KEYWORDS = [
    "quality control", "qc", "registration", "registered", "banned",
    "prohibited", "restricted", "fake", "spurious", "adulterated",
    "substandard", "misbranded", "sample", "laboratory", "analysis",
    "active ingredient", "a.i.", "formulation", "seizure", "confiscated",
]


# ---------------------------------------------------------------------------
# PDF inspection and extraction
# ---------------------------------------------------------------------------
def inspect_pdf(pdf_path: Path) -> Dict[str, Any]:
    """Probe whether the PDF can be read and contains extractable text."""
    result: Dict[str, Any] = {
        "pdf_path": str(pdf_path),
        "readable": False,
        "exists": False,
        "page_count": 0,
        "encrypted": False,
        "text_layer_present": False,
        "total_characters": 0,
        "reason": "",
    }
    if not pdf_path.exists():
        result["reason"] = "file_not_found"
        return result
    result["exists"] = True
    try:
        with pdfplumber.open(pdf_path) as pdf:
            result["page_count"] = len(pdf.pages)
            is_encrypted = getattr(pdf, "is_encrypted", None)
            if is_encrypted is None and hasattr(pdf, "doc"):
                is_encrypted = not getattr(pdf.doc, "is_extractable", True)
            if is_encrypted:
                result["encrypted"] = True
                result["reason"] = "pdf_is_encrypted"
                return result
            total_chars = 0
            for page in pdf.pages:
                text = page.extract_text() or ""
                total_chars += len(text.strip())
            result["total_characters"] = total_chars
            result["text_layer_present"] = total_chars > 0
            result["readable"] = True
    except Exception as exc:  # noqa: BLE001
        result["reason"] = f"open_failed: {exc}"
    return result


def extract_pages(pdf_path: Path) -> List[Dict[str, Any]]:
    """Extract text from each page, flagging pages with very little text."""
    pages: List[Dict[str, Any]] = []
    with pdfplumber.open(pdf_path) as pdf:
        for idx, page in enumerate(pdf.pages, start=1):
            text = page.extract_text() or ""
            text = _clean_text(text)
            pages.append(
                {
                    "page": idx,
                    "text": text,
                    "characters": len(text),
                    "empty_text_layer": len(text) < 20,
                }
            )
    return pages


def extract_tables(
    pdf_path: Path,
) -> Tuple[List[Dict[str, Any]], List[str]]:
    """Extract tables that meet quality thresholds."""
    tables: List[Dict[str, Any]] = []
    warnings: List[str] = []
    with pdfplumber.open(pdf_path) as pdf:
        for idx, page in enumerate(pdf.pages, start=1):
            page_tables = page.extract_tables()
            for t_idx, table in enumerate(page_tables or [], start=1):
                if not table or len(table) < 2:
                    warnings.append(f"page {idx} table {t_idx}: fewer than 2 rows")
                    continue
                rows = [[_clean_text(str(cell)) if cell is not None else "" for cell in row] for row in table]
                num_cols = max(len(row) for row in rows)
                if num_cols < 2:
                    warnings.append(f"page {idx} table {t_idx}: fewer than 2 columns")
                    continue
                header = rows[0]
                if not any(header):
                    warnings.append(f"page {idx} table {t_idx}: empty header")
                    continue
                total_cells = sum(len(row) for row in rows)
                empty_cells = sum(1 for row in rows for cell in row if not cell.strip())
                if total_cells and (empty_cells / total_cells) >= 0.30:
                    warnings.append(f"page {idx} table {t_idx}: too many empty cells")
                    continue
                tables.append(
                    {
                        "page": idx,
                        "table_index": t_idx,
                        "header": header,
                        "rows": rows[1:],
                        "num_rows": len(rows),
                        "num_cols": num_cols,
                    }
                )
    return tables, warnings


def _clean_text(text: str) -> str:
    """Normalize whitespace while preserving paragraph breaks."""
    text = text.replace("\r", "\n")
    text = re.sub(r" +", " ", text)
    text = re.sub(r"\n{3,}", "\n\n", text)
    return text.strip()


# ---------------------------------------------------------------------------
# Section detection
# ---------------------------------------------------------------------------
def detect_section(page_text: str, page: int, carry: str) -> str:
    """Heuristic heading detector for annual-report sections."""
    lines = [line.strip() for line in page_text.splitlines() if line.strip()]
    for line in lines[:12]:
        # Numbered chapters/sections: "CHAPTER 1", "1. Introduction", "1.1 Background"
        if re.match(r"^(CHAPTER|SECTION)\s+\d+", line, re.IGNORECASE):
            return line
        if re.match(r"^\d+(\.\d+)*\.?\s+[A-Z][A-Za-z ]{3,}$", line):
            return line
        # ALL CAPS headings of reasonable length (not page numbers)
        if line.isupper() and 10 <= len(line) <= 120 and not re.match(r"^\d+$", line):
            return line.title()
    if carry:
        return carry
    return f"page_{page}"


# ---------------------------------------------------------------------------
# Chunking
# ---------------------------------------------------------------------------
def build_chunks(
    pages: List[Dict[str, Any]], target_chars: int = 1200, overlap_chars: int = 150
) -> List[Dict[str, Any]]:
    """Build page-bounded text chunks with paragraph awareness."""
    chunks: List[Dict[str, Any]] = []
    carry_section = ""
    for page in pages:
        page_num = page["page"]
        text = page["text"]
        if not text:
            continue
        section = detect_section(text, page_num, carry_section)
        carry_section = section
        paragraphs = [p.strip() for p in text.split("\n\n") if p.strip()]
        current_text = ""
        current_paras: List[str] = []
        for para in paragraphs:
            if len(current_text) + len(para) + 2 > target_chars and current_text:
                chunks.append(
                    _make_chunk(page_num, section, current_text, chunks)
                )
                overlap = _tail_text(current_text, overlap_chars)
                current_text = overlap + "\n\n" + para if overlap else para
                current_paras = [para]
            else:
                current_text = (current_text + "\n\n" + para).strip() if current_text else para
                current_paras.append(para)
        if current_text:
            chunks.append(_make_chunk(page_num, section, current_text, chunks))
    return chunks


def _make_chunk(page: int, section: str, text: str, chunks: List[Dict[str, Any]]) -> Dict[str, Any]:
    return {
        "chunk_id": f"chunk_{len(chunks) + 1:05d}",
        "page": page,
        "section": section,
        "text": text,
        "characters": len(text),
    }


def _tail_text(text: str, max_chars: int) -> str:
    """Return the trailing portion of text up to max_chars, starting at a paragraph break if possible."""
    if len(text) <= max_chars:
        return text
    tail = text[-max_chars:]
    first_para_break = tail.find("\n\n")
    if first_para_break != -1:
        return tail[first_para_break + 2 :]
    return tail


# ---------------------------------------------------------------------------
# Fact extraction
# ---------------------------------------------------------------------------
def extract_facts(
    chunks: List[Dict[str, Any]], tables: List[Dict[str, Any]]
) -> List[Dict[str, Any]]:
    """Extract source-backed facts from chunks and tables."""
    facts: List[Dict[str, Any]] = []
    table_facts = _facts_from_tables(tables)
    facts.extend(table_facts)
    for chunk in chunks:
        chunk_facts = _facts_from_chunk(chunk)
        facts.extend(chunk_facts)
    # Deduplicate by hash of excerpt + page to avoid near-duplicates
    seen: set[str] = set()
    unique_facts: List[Dict[str, Any]] = []
    for fact in facts:
        key = hashlib.md5(
            f"{fact['source_page']}::{fact['source_excerpt'][:200]}".encode("utf-8")
        ).hexdigest()
        if key not in seen:
            seen.add(key)
            unique_facts.append(fact)
    return unique_facts


def _facts_from_tables(tables: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    facts: List[Dict[str, Any]] = []
    for table in tables:
        header = table["header"]
        rows = table["rows"]
        # Render table as text for excerpt
        rendered = " | ".join(header) + "\n"
        for row in rows[:5]:
            rendered += " | ".join(row) + "\n"
        text = rendered.strip()
        category = _categorize_text(text)
        fact = _blank_fact()
        fact["category"] = category
        fact["crop"] = _detect_crop(text)
        fact["pest_or_disease"] = _detect_pest(text)
        fact["district"] = _detect_district(text)
        fact["date_or_period"] = _detect_period(text)
        fact["advisory_text"] = text[:500]
        fact["pesticide_name"] = _detect_pesticide(text)
        fact["explicit_dose_text"] = _extract_dose(text)[0]
        fact["safety_text"] = _detect_safety(text)
        fact["quality_control_status"] = _detect_qc_status(text)
        fact["source_page"] = table["page"]
        fact["source_section"] = f"table_{table['table_index']}"
        fact["source_excerpt"] = text[:1200]
        fact["extraction_status"] = "extracted_from_table"
        fact["confidence"] = round(_score_confidence(fact, {"empty_text_layer": False}), 3)
        facts.append(fact)
    return facts


def _facts_from_chunk(chunk: Dict[str, Any]) -> List[Dict[str, Any]]:
    text = chunk["text"]
    facts: List[Dict[str, Any]] = []
    # Split chunk into sentence groups so one fact per advisory passage
    passages = _split_passages(text)
    for passage in passages:
        if len(passage) < 40:
            continue
        category = _categorize_text(passage)
        if category == "general_agricultural_advisory" and not _looks_advisory(passage):
            continue
        fact = _blank_fact()
        fact["category"] = category
        fact["crop"] = _detect_crop(passage)
        fact["pest_or_disease"] = _detect_pest(passage)
        fact["district"] = _detect_district(passage)
        fact["date_or_period"] = _detect_period(passage)
        fact["advisory_text"] = passage[:800]
        fact["pesticide_name"] = _detect_pesticide(passage)
        fact["active_ingredient"] = _detect_active_ingredient(passage)
        fact["formulation"] = _detect_formulation(passage)
        dose_text, _ = _extract_dose(passage)
        fact["explicit_dose_text"] = dose_text
        fact["safety_text"] = _detect_safety(passage)
        fact["quality_control_status"] = _detect_qc_status(passage)
        fact["source_page"] = chunk["page"]
        fact["source_section"] = chunk["section"]
        fact["source_excerpt"] = passage[:1200]
        fact["extraction_status"] = _determine_status(fact, passage)
        fact["confidence"] = round(_score_confidence(fact, chunk), 3)
        facts.append(fact)
    return facts


def _blank_fact() -> Dict[str, Any]:
    return {
        "fact_id": "",
        "category": "",
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
        "source_report_title": SOURCE_TITLE,
        "source_report_year": SOURCE_YEAR,
        "source_filename": SOURCE_FILENAME,
        "source_page": 0,
        "source_section": "",
        "source_excerpt": "",
        "extraction_status": "",
        "confidence": 0.0,
        "reviewed": False,
    }


def _split_passages(text: str, max_len: int = 700) -> List[str]:
    """Split text into sentence-bounded passages."""
    # Split on sentence terminators followed by space and capital letter
    raw = re.split(r"(?<=[.!?])\s+(?=[A-Z])", text)
    passages: List[str] = []
    current = ""
    for part in raw:
        part = part.strip()
        if not part:
            continue
        if len(current) + len(part) + 1 > max_len and current:
            passages.append(current)
            current = part
        else:
            current = (current + " " + part).strip() if current else part
    if current:
        passages.append(current)
    return passages


def _looks_advisory(text: str) -> bool:
    advisory_markers = [
        "should", "must", "recommended", "advisory", "control", "manage",
        "apply", "spray", "monitor", "scout", "per acre", "per ha",
    ]
    low = text.lower()
    return any(marker in low for marker in advisory_markers)


# ---------------------------------------------------------------------------
# Categorization and entity detection
# ---------------------------------------------------------------------------
def _categorize_text(text: str) -> str:
    low = text.lower()
    scores: Dict[str, int] = {cat: 0 for cat in ALLOWED_CATEGORIES}
    for kw in QC_KEYWORDS:
        if kw.lower() in low:
            scores["pesticide_quality_control"] += 1
    for kw in SAFETY_KEYWORDS:
        if kw.lower() in low:
            scores["pesticide_safety"] += 1
    for kw in ["inspection", "inspected", "inspector", "team", "field visit"]:
        if kw in low:
            scores["inspection"] += 1
    for kw in ["laboratory", "lab ", "tested", "analysis", "analyzed", "sample"]:
        if kw in low:
            scores["laboratory_result"] += 1
    for kw in ["warning", "outbreak", "infestation", "attack", "epidemic", "incidence"]:
        if kw in low:
            scores["pest_warning"] += 1
    for kw in ["disease", "fungal", "bacterial", "viral", "blight", "rust", "blast", "mildew"]:
        if kw in low:
            scores["crop_disease_warning"] += 1
    # General advisory if many pesticide words and advisory markers
    if scores["pesticide_quality_control"] == 0 and scores["pesticide_safety"] == 0:
        if _looks_advisory(text) and (scores["pest_warning"] or scores["crop_disease_warning"]):
            scores["general_agricultural_advisory"] += 1
    best = max(scores, key=scores.get)
    if scores[best] == 0:
        return "general_agricultural_advisory"
    return best


def _detect_crop(text: str) -> str:
    low = text.lower()
    found: List[str] = []
    for crop, keywords in CROP_KEYWORDS.items():
        if any(kw in low for kw in keywords):
            found.append(crop)
    return "; ".join(found)


def _detect_pest(text: str) -> str:
    low = text.lower()
    found: List[str] = []
    for pest, keywords in PEST_KEYWORDS.items():
        if any(kw in low for kw in keywords):
            found.append(pest)
    return "; ".join(found)


def _detect_district(text: str) -> str:
    low = text.lower()
    found: List[str] = []
    for district in DISTRICTS:
        if district in low:
            found.append(district.title())
    return "; ".join(found)


def _detect_period(text: str) -> str:
    # Look for years, months, kharif/rabi, season references
    patterns = [
        r"\b(20\d{2}-?\d{2,4})\b",
        r"\b(kharif|rabi|summer|winter|spring|monsoon)\s+20\d{2}\b",
        r"\b(january|february|march|april|may|june|july|august|september|october|november|december)\s+20\d{2}\b",
    ]
    found: List[str] = []
    for pattern in patterns:
        for match in re.finditer(pattern, text, re.IGNORECASE):
            found.append(match.group(0))
    return "; ".join(found)


def _detect_pesticide(text: str) -> str:
    low = text.lower()
    found: List[str] = []
    for kw in PESTICIDE_KEYWORDS:
        if kw.lower() in low:
            found.append(kw.title() if kw.islower() else kw)
    # Deduplicate while preserving order
    seen: set[str] = set()
    out: List[str] = []
    for item in found:
        key = item.lower()
        if key not in seen:
            seen.add(key)
            out.append(item)
    return "; ".join(out)


def _detect_active_ingredient(text: str) -> str:
    # Look for "active ingredient: X" or known active ingredient names
    match = re.search(
        r"(?:active ingredient|a\.i\.?)[\s:)(]+([A-Za-z0-9\- ]{3,60}?)(?:\n|\.|:|\)|\()",
        text,
        re.IGNORECASE,
    )
    if match:
        return match.group(1).strip()
    return ""


def _detect_formulation(text: str) -> str:
    # Match formulations like "250 EC", "50 WP", "20 SC", "70 DF"
    matches = re.findall(r"\b\d+\s*(EC|WP|SC|DF|WG|SP|SL|EW|ME|OD|GR)\b", text, re.IGNORECASE)
    if matches:
        return "; ".join(sorted(set(m.upper() for m in matches)))
    return ""


def _detect_safety(text: str) -> str:
    low = text.lower()
    phrases: List[str] = []
    for kw in SAFETY_KEYWORDS:
        if kw.lower() in low:
            phrases.append(kw)
    if not phrases:
        return ""
    # Pull a short sentence containing a safety keyword
    sentences = re.split(r"(?<=[.!?])\s+", text)
    for sentence in sentences:
        s_low = sentence.lower()
        if any(kw in s_low for kw in phrases[:3]):
            return sentence.strip()[:300]
    return phrases[0]


def _detect_qc_status(text: str) -> str:
    low = text.lower()
    statuses: List[str] = []
    if any(kw in low for kw in ["banned", "prohibited", "restricted"]):
        statuses.append("restricted/banned")
    if any(kw in low for kw in ["fake", "spurious", "adulterated", "substandard", "misbranded"]):
        statuses.append("non-compliant sample")
    if any(kw in low for kw in ["registered", "approved"]):
        statuses.append("registered")
    if any(kw in low for kw in ["seized", "confiscated", "action taken"]):
        statuses.append("enforcement action")
    return "; ".join(statuses)


# ---------------------------------------------------------------------------
# Explicit dose detection
# ---------------------------------------------------------------------------
_DOSE_RE = re.compile(
    r"\b(\d+(?:\.\d+)?)\s*(ml|millilitre|milliliter|litre|liter|l|g|gram|gm|kg|kilogram|ounce|oz|pound|lb)\s*(?:per|/|\\)\s*(acre|hectare|ha|kanal|marla|litre|liter|l|100\s*ltrs?|100\s*litres?)\b",
    re.IGNORECASE,
)

_DOSE_RANGE_RE = re.compile(
    r"\b(\d+(?:\.\d+)?)\s*-\s*(\d+(?:\.\d+)?)\s*(ml|millilitre|milliliter|litre|liter|l|g|gram|gm|kg|kilogram)\s*(?:per|/|\\)\s*(acre|hectare|ha|kanal)\b",
    re.IGNORECASE,
)


def _extract_dose(text: str) -> Tuple[str, float]:
    """Return verbatim dose text and a confidence score; empty if not unambiguous."""
    # Range first
    for match in _DOSE_RANGE_RE.finditer(text):
        dose = match.group(0)
        if dose.lower() in text.lower() and _dose_has_basis(dose):
            return dose, 1.0
    # Single value
    for match in _DOSE_RE.finditer(text):
        dose = match.group(0)
        if _dose_has_basis(dose):
            return dose, 1.0
    return "", 0.0


def _dose_has_basis(dose: str) -> bool:
    low = dose.lower()
    return any(basis in low for basis in ["acre", "hectare", "ha", "kanal", "marla", "ltr", "litre", "liter", "100 l"])


# ---------------------------------------------------------------------------
# Confidence and status
# ---------------------------------------------------------------------------
def _determine_status(fact: Dict[str, Any], passage: str) -> str:
    if fact["explicit_dose_text"]:
        return "extracted"
    if fact["pesticide_name"] and not fact["explicit_dose_text"]:
        # Pesticide mentioned but no unambiguous dose
        return "ambiguous_dose"
    return "extracted"


def _score_confidence(fact: Dict[str, Any], chunk: Dict[str, Any]) -> float:
    score = 0.5
    if fact["category"] in ALLOWED_CATEGORIES and fact["category"] != "general_agricultural_advisory":
        score += 0.15
    if fact["crop"] or fact["pest_or_disease"]:
        score += 0.10
    if fact["district"]:
        score += 0.05
    if fact["advisory_text"] and len(fact["advisory_text"]) >= 80:
        score += 0.05
    if fact["source_excerpt"] and len(fact["source_excerpt"]) >= 100:
        score += 0.05
    if fact["explicit_dose_text"]:
        score += 0.10
    if chunk.get("empty_text_layer"):
        score -= 0.20
    if fact["extraction_status"] == "ambiguous_dose":
        score -= 0.15
    return max(0.0, min(1.0, score))


# ---------------------------------------------------------------------------
# Writers
# ---------------------------------------------------------------------------
def assign_fact_ids(facts: List[Dict[str, Any]]) -> None:
    for idx, fact in enumerate(facts, start=1):
        fact["fact_id"] = f"fact_{idx:05d}"


def build_review_queue(facts: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    queue: List[Dict[str, Any]] = []
    for fact in facts:
        if (
            fact["confidence"] < 0.60
            or fact["extraction_status"] == "ambiguous_dose"
            or (fact["pesticide_name"] and not fact["explicit_dose_text"])
        ):
            queue.append(fact)
    return queue


def write_csv(path: Path, rows: List[Dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as fh:
        writer = csv.DictWriter(fh, fieldnames=FACT_FIELDS, lineterminator="\n")
        writer.writeheader()
        for row in rows:
            writer.writerow({k: _serialize(row.get(k, "")) for k in FACT_FIELDS})


def _serialize(value: Any) -> str:
    if value is None:
        return ""
    if isinstance(value, bool):
        return "true" if value else "false"
    return str(value)


def write_jsonl(path: Path, chunks: List[Dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as fh:
        for chunk in chunks:
            fh.write(json.dumps(chunk, ensure_ascii=False) + "\n")


def write_meta(
    path: Path,
    inspect: Dict[str, Any],
    facts: List[Dict[str, Any]],
    review_queue: List[Dict[str, Any]],
    chunks: List[Dict[str, Any]],
    warnings: List[str],
) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    meta = {
        "source_title": SOURCE_TITLE,
        "source_year": SOURCE_YEAR,
        "source_filename": SOURCE_FILENAME,
        "ingestion_timestamp": datetime.now(timezone.utc).isoformat(),
        "pdf_path": inspect.get("pdf_path"),
        "readable": inspect.get("readable", False),
        "page_count": inspect.get("page_count", 0),
        "total_characters": inspect.get("total_characters", 0),
        "text_layer_present": inspect.get("text_layer_present", False),
        "num_facts": len(facts),
        "num_review_queue": len(review_queue),
        "num_chunks": len(chunks),
        "num_tables": 0,
        "warnings": warnings,
        "status": "ok" if inspect.get("readable") and facts else "partial",
    }
    with path.open("w", encoding="utf-8") as fh:
        json.dump(meta, fh, indent=2, ensure_ascii=False)


def write_analysis_report(
    path: Path,
    inspect: Dict[str, Any],
    facts: List[Dict[str, Any]],
    chunks: List[Dict[str, Any]],
    warnings: List[str],
) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    lines: List[str] = [
        "# Pesticide Annual Report Analysis",
        "",
        f"**Source:** {SOURCE_TITLE} ({SOURCE_YEAR})",
        f"**File:** {SOURCE_FILENAME}",
        f"**Ingested:** {datetime.now(timezone.utc).isoformat()} UTC",
        "",
        "## PDF inspection",
        "",
        f"- Readable: {inspect.get('readable', False)}",
        f"- Pages: {inspect.get('page_count', 0)}",
        f"- Extractable characters: {inspect.get('total_characters', 0):,}",
        f"- Text layer present: {inspect.get('text_layer_present', False)}",
        "",
        "## Extraction summary",
        "",
        f"- Total facts: {len(facts)}",
        f"- Total chunks: {len(chunks)}",
        f"- Extraction warnings: {len(warnings)}",
        "",
        "## Facts by category",
        "",
    ]
    by_category: Dict[str, int] = {}
    for fact in facts:
        by_category[fact["category"]] = by_category.get(fact["category"], 0) + 1
    for cat in sorted(by_category):
        lines.append(f"- {cat}: {by_category[cat]}")
    lines.extend(["", "## Facts by crop", ""])
    by_crop: Dict[str, int] = {}
    for fact in facts:
        for crop in fact["crop"].split(";"):
            crop = crop.strip()
            if crop:
                by_crop[crop] = by_crop.get(crop, 0) + 1
    for crop in sorted(by_crop):
        lines.append(f"- {crop}: {by_crop[crop]}")
    lines.extend(["", "## Sample facts", ""])
    for fact in facts[:10]:
        lines.append(f"### {fact['fact_id']} (p. {fact['source_page']})")
        lines.append(f"- Category: {fact['category']}")
        lines.append(f"- Crop: {fact['crop'] or '—'}")
        lines.append(f"- Pest/disease: {fact['pest_or_disease'] or '—'}")
        lines.append(f"- District: {fact['district'] or '—'}")
        lines.append(f"- Confidence: {fact['confidence']}")
        lines.append(f"- Dose: {fact['explicit_dose_text'] or '—'}")
        lines.append(f"> {fact['source_excerpt'][:300]}")
        lines.append("")
    if warnings:
        lines.extend(["", "## Warnings", ""])
        for warning in warnings[:50]:
            lines.append(f"- {warning}")
    with path.open("w", encoding="utf-8") as fh:
        fh.write("\n".join(lines))


def write_quality_report(
    path: Path,
    facts: List[Dict[str, Any]],
    review_queue: List[Dict[str, Any]],
) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    dose_facts = [f for f in facts if f["explicit_dose_text"]]
    dose_integrity_ok = all(
        f["explicit_dose_text"].lower() in f["source_excerpt"].lower() for f in dose_facts
    )
    lines: List[str] = [
        "# Pesticide Report Extraction Quality",
        "",
        f"**Generated:** {datetime.now(timezone.utc).isoformat()} UTC",
        "",
        "## Checks",
        "",
        f"- Total facts: {len(facts)}",
        f"- Review queue: {len(review_queue)}",
        f"- Facts with explicit dose: {len(dose_facts)}",
        f"- Dose integrity (verbatim in excerpt): {'PASS' if dose_integrity_ok else 'FAIL'}",
        f"- Facts with source page: {sum(1 for f in facts if isinstance(f['source_page'], int) and f['source_page'] > 0)}",
        f"- Facts with source excerpt: {sum(1 for f in facts if f['source_excerpt'])}",
        "",
        "## Review queue reasons",
        "",
    ]
    low_conf = sum(1 for f in review_queue if f["confidence"] < 0.60)
    ambig = sum(1 for f in review_queue if f["extraction_status"] == "ambiguous_dose")
    no_dose = sum(
        1 for f in review_queue if f["pesticide_name"] and not f["explicit_dose_text"]
    )
    lines.extend(
        [
            f"- Low confidence (<0.60): {low_conf}",
            f"- Ambiguous dose status: {ambig}",
            f"- Pesticide without unambiguous dose: {no_dose}",
            "",
            "## Confidence distribution",
            "",
        ]
    )
    buckets = {"0.0-0.39": 0, "0.40-0.59": 0, "0.60-0.79": 0, "0.80-1.0": 0}
    for fact in facts:
        c = fact["confidence"]
        if c < 0.40:
            buckets["0.0-0.39"] += 1
        elif c < 0.60:
            buckets["0.40-0.59"] += 1
        elif c < 0.80:
            buckets["0.60-0.79"] += 1
        else:
            buckets["0.80-1.0"] += 1
    for label, count in buckets.items():
        lines.append(f"- {label}: {count}")
    with path.open("w", encoding="utf-8") as fh:
        fh.write("\n".join(lines))


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------
def run(pdf_path: Optional[Path] = None) -> Dict[str, Any]:
    if pdf_path is None:
        target = PROJECT_ROOT / DEFAULT_PDF_PATH
        if not target.exists():
            fallback = (PROJECT_ROOT / FALLBACK_PDF_PATH).resolve()
            if fallback.exists():
                target = fallback
        pdf_path = target
    inspect = inspect_pdf(pdf_path)

    PROCESSED_DIR.mkdir(parents=True, exist_ok=True)
    REPORTS_DIR.mkdir(parents=True, exist_ok=True)

    if not inspect["readable"]:
        # Write empty artifacts with clear status
        facts: List[Dict[str, Any]] = []
        chunks: List[Dict[str, Any]] = []
        tables: List[Dict[str, Any]] = []
        warnings = [inspect.get("reason", "pdf_not_readable")]
        review_queue: List[Dict[str, Any]] = []
        assign_fact_ids(facts)
        write_jsonl(CHUNKS_JSONL, chunks)
        write_csv(FACTS_CSV, facts)
        write_csv(REVIEW_CSV, review_queue)
        write_meta(META_JSON, inspect, facts, review_queue, chunks, warnings)
        write_analysis_report(ANALYSIS_MD, inspect, facts, chunks, warnings)
        write_quality_report(QUALITY_MD, facts, review_queue)
        return {
            "status": "skipped",
            "reason": inspect.get("reason"),
            "facts": 0,
            "chunks": 0,
        }

    pages = extract_pages(pdf_path)
    tables, warnings = extract_tables(pdf_path)
    chunks = build_chunks(pages, target_chars=1200, overlap_chars=150)
    facts = extract_facts(chunks, tables)
    assign_fact_ids(facts)
    review_queue = build_review_queue(facts)

    write_jsonl(CHUNKS_JSONL, chunks)
    write_csv(FACTS_CSV, facts)
    write_csv(REVIEW_CSV, review_queue)
    write_meta(META_JSON, inspect, facts, review_queue, chunks, warnings)
    write_analysis_report(ANALYSIS_MD, inspect, facts, chunks, warnings)
    write_quality_report(QUALITY_MD, facts, review_queue)

    return {
        "status": "ok",
        "facts": len(facts),
        "chunks": len(chunks),
        "review_queue": len(review_queue),
        "pages": inspect["page_count"],
        "warnings": len(warnings),
    }


def main() -> int:
    pdf_path: Optional[Path] = None
    if len(sys.argv) > 1:
        pdf_path = Path(sys.argv[1])
    result = run(pdf_path)
    print(json.dumps(result, indent=2))
    return 0 if result["status"] in ("ok", "skipped") else 1


if __name__ == "__main__":
    raise SystemExit(main())
