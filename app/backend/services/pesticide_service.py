"""Pesticide advisory service backed by the official annual report.

Loads extracted facts, chunks, and metadata lazily. Falls back to a safe
unavailable response when no ingestion artifacts exist.
"""

from __future__ import annotations

import csv
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional

from app.config import settings


class PesticideService:
    """Lazy-loading service for official pesticide report data."""

    def __init__(self) -> None:
        self._facts: Optional[List[Dict[str, Any]]] = None
        self._chunks: Optional[List[Dict[str, Any]]] = None
        self._meta: Optional[Dict[str, Any]] = None

    # -----------------------------------------------------------------------
    # Loading
    # -----------------------------------------------------------------------
    def _load_facts(self) -> List[Dict[str, Any]]:
        if self._facts is None:
            self._facts = self._load_csv(settings.pesticide_facts_csv_full_path())
        return self._facts

    def _load_chunks(self) -> List[Dict[str, Any]]:
        if self._chunks is None:
            self._chunks = self._load_jsonl(settings.pesticide_chunks_jsonl_full_path())
        return self._chunks

    def _load_meta(self) -> Dict[str, Any]:
        if self._meta is None:
            path = settings.pesticide_meta_json_full_path()
            if path.exists():
                try:
                    with path.open("r", encoding="utf-8") as fh:
                        self._meta = json.load(fh)
                except Exception:  # noqa: BLE001
                    self._meta = {"readable": False, "status": "error"}
            else:
                self._meta = {"readable": False, "status": "missing"}
        return self._meta

    @staticmethod
    def _load_csv(path: Path) -> List[Dict[str, Any]]:
        if not path.exists():
            return []
        with path.open("r", encoding="utf-8", newline="") as fh:
            reader = csv.DictReader(fh)
            rows = list(reader)
        for row in rows:
            row["confidence"] = float(row.get("confidence", "0") or "0")
            page = row.get("source_page", "")
            try:
                row["source_page"] = int(page)
            except ValueError:
                row["source_page"] = 0
            row["reviewed"] = row.get("reviewed", "").lower() == "true"
        return rows

    @staticmethod
    def _load_jsonl(path: Path) -> List[Dict[str, Any]]:
        if not path.exists():
            return []
        items: List[Dict[str, Any]] = []
        with path.open("r", encoding="utf-8") as fh:
            for line in fh:
                line = line.strip()
                if line:
                    items.append(json.loads(line))
        return items

    # -----------------------------------------------------------------------
    # Status
    # -----------------------------------------------------------------------
    @property
    def source_status(self) -> str:
        meta = self._load_meta()
        if (
            meta.get("readable", False)
            and self._load_facts()
            and meta.get("status") in ("ok", "partial")
        ):
            return "official_report"
        return "unavailable"

    # -----------------------------------------------------------------------
    # Alerts
    # -----------------------------------------------------------------------
    def recent_alerts(
        self,
        district: Optional[str] = None,
        crop: Optional[str] = None,
        category: Optional[str] = None,
        limit: int = 50,
    ) -> List[Dict[str, Any]]:
        facts = self._load_facts()
        out: List[Dict[str, Any]] = []
        for fact in facts:
            if fact["confidence"] < 0.60 and not fact["reviewed"]:
                continue
            if district and not self._matches(district, fact.get("district", "")):
                continue
            if crop and not self._matches(crop, fact.get("crop", "")):
                continue
            if category and not self._matches(category, fact.get("category", "")):
                continue
            out.append(fact)
            if len(out) >= limit:
                break

        # Fallback to general Punjab advisories if district-specific alerts are empty
        if not out and district:
            for fact in facts:
                if fact["confidence"] < 0.60 and not fact["reviewed"]:
                    continue
                if crop and not self._matches(crop, fact.get("crop", "")):
                    continue
                if category and not self._matches(category, fact.get("category", "")):
                    continue
                out.append(fact)
                if len(out) >= limit:
                    break

        return out

    # -----------------------------------------------------------------------
    # Search / advisory
    # -----------------------------------------------------------------------
    def search(
        self,
        crop: Optional[str] = None,
        pest: Optional[str] = None,
        district: Optional[str] = None,
        query: Optional[str] = None,
        limit: int = 5,
    ) -> List[Dict[str, Any]]:
        facts = self._load_facts()
        scored: List[Tuple[float, Dict[str, Any]]] = []
        for fact in facts:
            if fact["confidence"] < 0.60 and not fact["reviewed"]:
                continue
            score = self._score_fact(fact, crop, pest, district, query)
            if score > 0:
                scored.append((score, fact))
        scored.sort(key=lambda x: x[0], reverse=True)
        return [fact for _, fact in scored[:limit]]

    def advisory(
        self,
        crop: Optional[str] = None,
        pest: Optional[str] = None,
        district: Optional[str] = None,
    ) -> Dict[str, Any]:
        source_status = self.source_status
        now = datetime.now(timezone.utc).isoformat()
        if source_status != "official_report":
            return self._unavailable_response(crop, pest, district, now)

        matches = self.search(crop=crop, pest=pest, district=district, limit=settings.pesticide_max_citations)
        if not matches:
            return self._unavailable_response(crop, pest, district, now)

        citations = [self._to_citation(fact) for fact in matches]
        dose_facts = [f for f in matches if f.get("explicit_dose_text")]
        if dose_facts:
            dose_guidance = (
                "Quoted from the official report: "
                + "; ".join(f["explicit_dose_text"] for f in dose_facts[:2])
                + ". Verify product label, local registration, and Agriculture Department guidance before application."
            )
        else:
            dose_guidance = "No dosage is specified in the report for this query — consult an extension worker."

        safety = "; ".join(f.get("safety_text", "") for f in matches if f.get("safety_text"))[:500]
        if not safety:
            safety = "Always follow label instructions and consult a local extension worker before applying any pesticide."

        return {
            "crop": crop,
            "pest": pest,
            "district": district,
            "status": "advisory",
            "source_status": source_status,
            "matched": True,
            "reason": "official_report_match",
            "recommendations": [
                "The following information is drawn from the official pesticide annual report.",
                "Verify product label, local registration, and Agriculture Department guidance before application.",
            ],
            "dose_guidance": dose_guidance,
            "safety_notice": safety,
            "citations": citations,
            "updated_at": now,
        }

    def sources(self) -> List[Dict[str, Any]]:
        meta = self._load_meta()
        return [
            {
                "title": meta.get("source_title", "Pest Warning and Quality Control of Pesticides Annual Report"),
                "year": meta.get("source_year", "2024-25"),
                "filename": meta.get("source_filename", "Annual Report 2024-25_copy.pdf"),
                "ingestion_timestamp": meta.get("ingestion_timestamp"),
                "page_count": meta.get("page_count", 0),
                "num_facts": meta.get("num_facts", 0),
                "num_review_queue": meta.get("num_review_queue", 0),
                "num_chunks": meta.get("num_chunks", 0),
                "status": meta.get("status", "missing"),
            }
        ]

    # -----------------------------------------------------------------------
    # Helpers
    # -----------------------------------------------------------------------
    @staticmethod
    def _matches(query: str, text: str) -> bool:
        if not query or not text:
            return False
        return query.lower() in text.lower()

    @staticmethod
    def _tokenize(text: Optional[str]) -> set[str]:
        if not text:
            return set()
        return set(re.sub(r"[^a-z0-9]", " ", text.lower()).split())

    def _score_fact(
        self,
        fact: Dict[str, Any],
        crop: Optional[str],
        pest: Optional[str],
        district: Optional[str],
        query: Optional[str],
    ) -> float:
        score = 0.0
        if crop and self._matches(crop, fact.get("crop", "")):
            score += 3.0
        if pest and (
            self._matches(pest, fact.get("pest_or_disease", ""))
            or self._matches(pest, fact.get("advisory_text", ""))
        ):
            score += 3.0
        if district and self._matches(district, fact.get("district", "")):
            score += 2.0
        if query:
            query_tokens = self._tokenize(query)
            text = " ".join(
                str(fact.get(k, "")) for k in ["advisory_text", "source_excerpt", "pesticide_name"]
            )
            fact_tokens = self._tokenize(text)
            if query_tokens:
                overlap = len(query_tokens & fact_tokens) / len(query_tokens)
                score += overlap * 2.0
        # Slight boost for higher confidence and reviewed facts
        score += fact.get("confidence", 0) * 0.5
        if fact.get("reviewed"):
            score += 0.25
        return score

    @staticmethod
    def _to_citation(fact: Dict[str, Any]) -> Dict[str, Any]:
        return {
            "fact_id": fact.get("fact_id", ""),
            "category": fact.get("category", ""),
            "source_page": fact.get("source_page", 0),
            "source_section": fact.get("source_section", ""),
            "source_excerpt": fact.get("source_excerpt", ""),
        }

    def _unavailable_response(
        self,
        crop: Optional[str],
        pest: Optional[str],
        district: Optional[str],
        now: str,
    ) -> Dict[str, Any]:
        return {
            "crop": crop,
            "pest": pest,
            "district": district,
            "status": "unavailable",
            "source_status": self.source_status,
            "matched": False,
            "reason": "no_official_report_match",
            "recommendations": [
                "Consult the latest Pest Warning and Quality Control of Pesticides Annual Report.",
                "Contact a local extension worker before applying any pesticide.",
            ],
            "dose_guidance": None,
            "safety_notice": "Always follow label instructions and consult a local extension worker before applying any pesticide.",
            "citations": [],
            "updated_at": now,
        }


# ---------------------------------------------------------------------------
# Module-level singleton and thin back-compat shims
# ---------------------------------------------------------------------------
_service: Optional[PesticideService] = None


def get_pesticide_service() -> PesticideService:
    global _service
    if _service is None:
        _service = PesticideService()
    return _service


def advisory(crop: str, pest: str) -> Dict[str, object]:
    """Back-compat shim for callers expecting the old signature."""
    return get_pesticide_service().advisory(crop=crop, pest=pest)


def recent_alerts(district: str) -> List[Dict[str, object]]:
    """Back-compat shim for callers expecting the old signature."""
    return get_pesticide_service().recent_alerts(district=district)


# re is used in _tokenize
import re  # noqa: E402
