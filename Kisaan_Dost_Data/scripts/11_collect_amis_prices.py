"""AMIS Punjab Market Price Collector (Phase 7B).

Fetches official wholesale prices for expanded allowlisted commodities from http://www.amis.pk/
- Allowlisted commodities: Wheat, Rice Basmati Super, Rice IRRI, Maize, Potato Fresh, Potato Store,
  Onion, Tomato, Cotton (Phutti), Sugarcane, Gram, Moong.
- Enforces maximum 1 HTTP request per commodity per run.
- Integrates verified market-to-district mappings.
- Preserves raw source text, exact displayed unit, date, and provenance hashes.
- Never converts blanks/dashes to zero (preserves as null).
- Implements atomic writes and failure manifest logging.
"""

from __future__ import annotations

import csv
import hashlib
from datetime import datetime, timezone
import logging
from pathlib import Path
import re
import sys
import tempfile
from typing import Any, Dict, List, Optional, Tuple
from urllib.parse import urljoin
import urllib.request
import urllib.error

PARSER_VERSION = "amis_v1_phase7b"
SOURCE_NAME = "Official AMIS Punjab"
AMIS_BASE_URL = "http://www.amis.pk/ViewPrices.aspx?searchType=0&commodityId="

COMMODITY_ALLOWLIST: Dict[int, str] = {
    1: "Wheat",
    3: "Rice Basmati Super (New)",
    4: "Rice (IRRI)",
    9: "Gram Black Bareek",
    11: "Moong",
    17: "Maize",
    21: "Potato Fresh",
    22: "Potato Store",
    23: "Onion",
    26: "Tomato",
    49: "Seed Cotton(Phutti)",
    125: "Sugarcane",
}

DEFAULT_USER_AGENT = "KisaanDost-MarketConnector/1.1 (Agricultural Platform POC Phase 7B)"

ROOT = Path(__file__).resolve().parent.parent
PROCESSED_DIR = ROOT / "processed"
REPORTS_DIR = ROOT / "reports"

PRICES_CSV = PROCESSED_DIR / "amis_market_prices_v1.csv"
REVIEW_QUEUE_CSV = PROCESSED_DIR / "amis_market_price_review_queue_v1.csv"
COMMODITY_CATALOG_CSV = PROCESSED_DIR / "amis_commodity_catalog_v1.csv"
MARKET_CATALOG_CSV = PROCESSED_DIR / "amis_market_catalog_v1.csv"
MARKET_DISTRICT_MAPPING_CSV = PROCESSED_DIR / "amis_market_district_mapping_v1.csv"
MANIFEST_CSV = PROCESSED_DIR / "amis_market_collection_manifest_v1.csv"

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger(__name__)


PRICE_FIELDNAMES = [
    "record_id",
    "price_date",
    "source_displayed_date",
    "province",
    "district",
    "market_name",
    "market_id_or_source_label",
    "commodity_name",
    "commodity_id",
    "variety",
    "min_price_raw",
    "max_price_raw",
    "fqp_price_raw",
    "quantity_raw",
    "unit_raw",
    "min_price_pkr",
    "max_price_pkr",
    "fqp_price_pkr",
    "quantity",
    "unit",
    "source_name",
    "source_url",
    "retrieved_at",
    "parser_version",
    "data_status",
    "validation_status",
    "source_row_text",
    "source_row_hash",
    "source_table_header_text",
]

REVIEW_FIELDNAMES = [
    "review_id",
    "record_id",
    "commodity_id",
    "commodity_name",
    "market_name",
    "price_date",
    "issue_type",
    "issue_description",
    "source_row_text",
    "created_at",
]

MANIFEST_FIELDNAMES = [
    "run_id",
    "started_at",
    "completed_at",
    "commodity_id",
    "commodity_name",
    "source_url",
    "http_status",
    "content_hash",
    "parsed_row_count",
    "accepted_row_count",
    "review_row_count",
    "failure_reason",
    "parser_version",
]


def load_market_district_map(mapping_csv: Path = MARKET_DISTRICT_MAPPING_CSV) -> Dict[str, str]:
    """Load verified market-to-district mappings."""
    mapping: Dict[str, str] = {}
    if not mapping_csv.exists():
        return mapping

    with open(mapping_csv, "r", encoding="utf-8", newline="") as fh:
        reader = csv.DictReader(fh)
        for r in reader:
            m_name = r.get("amis_market_name", "").strip().lower()
            dist = r.get("normalized_district", "").strip()
            if m_name and dist:
                mapping[m_name] = dist
    return mapping


def _clean_html_text(text: str) -> str:
    cleaned = re.sub(r"<[^>]+>", " ", text)
    cleaned = cleaned.replace("&nbsp;", " ").replace("&nbsp", " ").replace("&#39;", "'").replace("&amp;", "&")
    return " ".join(cleaned.split()).strip()


def parse_amis_date(date_str: str) -> Tuple[Optional[str], str]:
    """Parse date from format DD-MM-YYYY or MM/DD/YYYY to YYYY-MM-DD."""
    clean = date_str.strip()
    m1 = re.search(r"(\d{1,2})-(\d{1,2})-(\d{4})", clean)
    if m1:
        d, m, y = m1.groups()
        return f"{int(y):04d}-{int(m):02d}-{int(d):02d}", clean
    m2 = re.search(r"(\d{1,2})/(\d{1,2})/(\d{4})", clean)
    if m2:
        m, d, y = m2.groups()
        return f"{int(y):04d}-{int(m):02d}-{int(d):02d}", clean
    return None, clean


def parse_numeric_value(raw: str) -> Optional[float]:
    """Parse numeric string without converting blanks/dashes to 0."""
    c = raw.strip().replace(",", "")
    if not c or c in {"-", "N/A", "NA", "--", "."}:
        return None
    try:
        val = float(c)
        return val
    except ValueError:
        return None


def parse_amis_html(
    html: str,
    commodity_id: int,
    commodity_name: str,
    source_url: str,
    retrieved_at: str,
    market_district_map: Optional[Dict[str, str]] = None,
) -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]], Optional[str]]:
    """Parse table rows and headers from AMIS HTML."""
    records: List[Dict[str, Any]] = []
    reviews: List[Dict[str, Any]] = []
    market_district_map = market_district_map or {}

    # 1. Extract Unit
    unit_match = re.search(r"lblquintal[^>]*>(.*?)</span>", html, re.DOTALL | re.IGNORECASE)
    unit_raw = "Rs/100Kg"
    if unit_match:
        unit_text = _clean_html_text(unit_match.group(1))
        if "Rs/100Kg" in unit_text or "100Kg" in unit_text:
            unit_raw = "Rs/100Kg"
        elif unit_text:
            unit_raw = unit_text

    # 2. Locate inner table inside ctl00_cphPage_Grd or demoarea
    table_match = re.search(r"<td\s+id=[\"']ctl00_cphPage_Grd[\"'][^>]*>\s*(<table[^>]*>[\s\S]*?</table>)\s*</td>", html, re.IGNORECASE)
    if not table_match:
        table_match = re.search(r"(<table[^>]*width=['\"]%100['\"][^>]*>[\s\S]*?</table>)", html, re.IGNORECASE)

    if not table_match:
        return records, reviews, "Price table container not found in HTML."

    table_html = table_match.group(1)

    # 3. Extract TRs
    all_trs = re.findall(r"<tr[^>]*>([\s\S]*?)</tr>", table_html, re.IGNORECASE)
    if not all_trs:
        return records, reviews, "No table rows found in price table."

    header_tr = all_trs[0]
    header_cells = re.findall(r"<td[^>]*>([\s\S]*?)</td>", header_tr, re.IGNORECASE)
    header_text = " ".join([_clean_html_text(c) for c in header_cells]) if header_cells else "Dated: Graph Min Max FQP Quantity"

    date_match = re.search(r"Dated:\s*([0-9\-\/]+)", header_text)
    source_displayed_date = date_match.group(1) if date_match else ""
    iso_date, _ = parse_amis_date(source_displayed_date) if source_displayed_date else (None, "")
    if not iso_date:
        input_date_match = re.search(r"name=[\"']ctl00\$cphPage\$DateTextBox[\"'][^>]*value=[\"']([^\"']+)[\"']", html)
        if input_date_match:
            iso_date, source_displayed_date = parse_amis_date(input_date_match.group(1))

    if not iso_date:
        iso_date = datetime.now(timezone.utc).strftime("%Y-%m-%d")

    data_trs = all_trs[1:]
    if not data_trs:
        return records, reviews, "No commodity price rows found below header."

    for idx, row_html in enumerate(data_trs):
        cells = re.findall(r"<td[^>]*>([\s\S]*?)</td>", row_html, re.IGNORECASE)
        if len(cells) < 4:
            continue

        raw_market_cell = _clean_html_text(cells[0])
        # Clean market name (e.g. "1 Lahore" -> "Lahore")
        market_name = re.sub(r"^\d+\s*", "", raw_market_cell).strip()
        market_id_match = re.search(r"city=(\d+)", cells[0]) or (re.search(r"city=(\d+)", cells[1]) if len(cells) > 1 else None)
        market_id = market_id_match.group(1) if market_id_match else ""

        if not market_name:
            continue

        min_raw = _clean_html_text(cells[2]) if len(cells) > 2 else "-"
        max_raw = _clean_html_text(cells[3]) if len(cells) > 3 else "-"
        fqp_raw = _clean_html_text(cells[4]) if len(cells) > 4 else "-"
        qty_raw = _clean_html_text(cells[5]) if len(cells) > 5 else "-"

        min_pkr = parse_numeric_value(min_raw)
        max_pkr = parse_numeric_value(max_raw)
        fqp_pkr = parse_numeric_value(fqp_raw)
        qty = parse_numeric_value(qty_raw)

        row_text = f"Market:{market_name}|Min:{min_raw}|Max:{max_raw}|FQP:{fqp_raw}|Qty:{qty_raw}"
        row_hash = hashlib.sha256(row_text.encode("utf-8")).hexdigest()[:16]
        record_id = f"amis_{commodity_id}_{iso_date}_{re.sub(r'[^a-z0-9]', '', market_name.lower())}"

        # Resolve verified district from crosswalk mapping
        resolved_district = market_district_map.get(market_name.lower())

        validation_status = "validated"
        issue_desc: Optional[str] = None

        # Validate numeric ordering Min <= FQP <= Max
        if min_pkr is not None and max_pkr is not None and min_pkr > max_pkr:
            validation_status = "needs_review"
            issue_desc = f"Min price ({min_pkr}) exceeds Max price ({max_pkr})"
        elif min_pkr is not None and fqp_pkr is not None and fqp_pkr < min_pkr:
            validation_status = "needs_review"
            issue_desc = f"FQP price ({fqp_pkr}) is below Min price ({min_pkr})"
        elif max_pkr is not None and fqp_pkr is not None and fqp_pkr > max_pkr:
            validation_status = "needs_review"
            issue_desc = f"FQP price ({fqp_pkr}) exceeds Max price ({max_pkr})"

        if validation_status == "needs_review" and issue_desc:
            reviews.append({
                "review_id": f"rev_{record_id}",
                "record_id": record_id,
                "commodity_id": commodity_id,
                "commodity_name": commodity_name,
                "market_name": market_name,
                "price_date": iso_date,
                "issue_type": "price_ordering_mismatch",
                "issue_description": issue_desc,
                "source_row_text": row_text,
                "created_at": retrieved_at,
            })

        record = {
            "record_id": record_id,
            "price_date": iso_date,
            "source_displayed_date": source_displayed_date,
            "province": "Punjab",
            "district": resolved_district,
            "market_name": market_name,
            "market_id_or_source_label": market_id or market_name,
            "commodity_name": commodity_name,
            "commodity_id": commodity_id,
            "variety": "Standard",
            "min_price_raw": min_raw,
            "max_price_raw": max_raw,
            "fqp_price_raw": fqp_raw,
            "quantity_raw": qty_raw,
            "unit_raw": unit_raw,
            "min_price_pkr": min_pkr,
            "max_price_pkr": max_pkr,
            "fqp_price_pkr": fqp_pkr,
            "quantity": qty,
            "unit": unit_raw,
            "source_name": SOURCE_NAME,
            "source_url": source_url,
            "retrieved_at": retrieved_at,
            "parser_version": PARSER_VERSION,
            "data_status": "official_amis",
            "validation_status": validation_status,
            "source_row_text": row_text,
            "source_row_hash": row_hash,
            "source_table_header_text": header_text,
        }
        records.append(record)

    return records, reviews, None


def fetch_amis_commodity(commodity_id: int, user_agent: str = DEFAULT_USER_AGENT) -> Tuple[str, int, str]:
    """Fetch one commodity HTML page using standard HTTP GET."""
    url = f"{AMIS_BASE_URL}{commodity_id}"
    req = urllib.request.Request(
        url,
        headers={"User-Agent": user_agent, "Accept": "text/html,application/xhtml+xml"},
    )
    with urllib.request.urlopen(req, timeout=10.0) as resp:
        status_code = resp.getcode()
        content_bytes = resp.read()
        html = content_bytes.decode("utf-8", errors="replace")
        return html, status_code, url


def run_collection(
    allowlist: Optional[Dict[int, str]] = None,
    user_agent: str = DEFAULT_USER_AGENT,
    sample_fixtures: Optional[Dict[int, str]] = None,
) -> Dict[str, Any]:
    """Run one manual collection pass over allowlisted commodities."""
    allowlist = allowlist or COMMODITY_ALLOWLIST
    PROCESSED_DIR.mkdir(parents=True, exist_ok=True)
    REPORTS_DIR.mkdir(parents=True, exist_ok=True)

    market_district_map = load_market_district_map()

    run_id = f"amis_run_{datetime.now(timezone.utc).strftime('%Y%m%d_%H%M%S')}"
    started_at = datetime.now(timezone.utc).isoformat()
    logger.info(f"Starting AMIS collection run: {run_id} ({len(allowlist)} commodities)")

    all_records: List[Dict[str, Any]] = []
    all_reviews: List[Dict[str, Any]] = []
    manifest_entries: List[Dict[str, Any]] = []
    unique_markets: Dict[str, Dict[str, Any]] = {}
    unique_commodities: Dict[int, Dict[str, Any]] = {}

    total_requests = 0

    for cid, cname in allowlist.items():
        total_requests += 1
        source_url = f"{AMIS_BASE_URL}{cid}"
        retrieved_at = datetime.now(timezone.utc).isoformat()
        http_status = 200
        failure_reason = ""
        html = ""

        try:
            if sample_fixtures and cid in sample_fixtures:
                html = sample_fixtures[cid]
            else:
                html, http_status, source_url = fetch_amis_commodity(cid, user_agent)

            content_hash = hashlib.sha256(html.encode("utf-8")).hexdigest()[:16]
            records, reviews, parse_err = parse_amis_html(
                html, cid, cname, source_url, retrieved_at, market_district_map
            )

            if parse_err:
                failure_reason = parse_err
                accepted_count = 0
                review_count = len(reviews)
            else:
                accepted_count = len([r for r in records if r["validation_status"] == "validated"])
                review_count = len([r for r in records if r["validation_status"] == "needs_review"])
                all_records.extend(records)
                all_reviews.extend(reviews)

                for r in records:
                    m_name = r["market_name"]
                    m_id = r["market_id_or_source_label"]
                    mapped_dist = r.get("district")
                    if m_name not in unique_markets:
                        unique_markets[m_name] = {
                            "market_name": m_name,
                            "source_market_id": m_id,
                            "province": "Punjab",
                            "mapped_district": mapped_dist,
                            "notes": "Verified from AMIS public prices table",
                        }

                unique_commodities[cid] = {
                    "commodity_id": cid,
                    "commodity_name": cname,
                    "default_unit": "Rs/100Kg",
                    "status": "allowlisted_phase7b",
                }

        except Exception as exc:
            logger.error(f"Error fetching commodity {cid} ({cname}): {exc}")
            http_status = 500
            content_hash = ""
            failure_reason = str(exc)
            accepted_count = 0
            review_count = 0

        manifest_entries.append({
            "run_id": run_id,
            "started_at": started_at,
            "completed_at": datetime.now(timezone.utc).isoformat(),
            "commodity_id": cid,
            "commodity_name": cname,
            "source_url": source_url,
            "http_status": http_status,
            "content_hash": content_hash,
            "parsed_row_count": accepted_count + review_count,
            "accepted_row_count": accepted_count,
            "review_row_count": review_count,
            "failure_reason": failure_reason,
            "parser_version": PARSER_VERSION,
        })

    # Atomic write of price records if any were successfully extracted
    if all_records:
        _atomic_write_csv(PRICES_CSV, all_records, PRICE_FIELDNAMES)
        logger.info(f"Wrote {len(all_records)} price records to {PRICES_CSV}")

    # Write review queue
    _append_or_write_csv(REVIEW_QUEUE_CSV, all_reviews, REVIEW_FIELDNAMES)

    # Write commodity catalog for all allowlisted commodities
    for cid, cname in COMMODITY_ALLOWLIST.items():
        unique_commodities[cid] = {
            "commodity_id": cid,
            "commodity_name": cname,
            "default_unit": "Rs/100Kg",
            "status": "allowlisted_phase7b",
        }

    if unique_commodities:
        _atomic_write_csv(
            COMMODITY_CATALOG_CSV,
            list(unique_commodities.values()),
            ["commodity_id", "commodity_name", "default_unit", "status"],
        )

    # Write market catalog
    if unique_markets:
        _atomic_write_csv(
            MARKET_CATALOG_CSV,
            list(unique_markets.values()),
            ["market_name", "source_market_id", "province", "mapped_district", "notes"],
        )

    # Append run manifest
    _append_or_write_csv(MANIFEST_CSV, manifest_entries, MANIFEST_FIELDNAMES)

    return {
        "run_id": run_id,
        "total_requests": total_requests,
        "total_records": len(all_records),
        "total_reviews": len(all_reviews),
        "manifest": manifest_entries,
    }


def _atomic_write_csv(target_path: Path, data: List[Dict[str, Any]], fieldnames: List[str]) -> None:
    temp_file = target_path.with_suffix(".tmp")
    with open(temp_file, "w", encoding="utf-8", newline="") as fh:
        writer = csv.DictWriter(fh, fieldnames=fieldnames, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(data)
    temp_file.replace(target_path)


def _append_or_write_csv(target_path: Path, data: List[Dict[str, Any]], fieldnames: List[str]) -> None:
    exists = target_path.exists()
    mode = "a" if exists else "w"
    with open(target_path, mode, encoding="utf-8", newline="") as fh:
        writer = csv.DictWriter(fh, fieldnames=fieldnames, extrasaction="ignore")
        if not exists:
            writer.writeheader()
        if data:
            writer.writerows(data)


if __name__ == "__main__":
    result = run_collection()
    print(f"Collection Complete: {result['total_records']} records collected across {result['total_requests']} requests.")
