"""Tests for AMIS Punjab Market Price Collector, Mapping, and Parser (Phase 7B)."""

from __future__ import annotations

import csv
import importlib.util
from pathlib import Path
import pytest

ROOT = Path(__file__).resolve().parent.parent
script_path = ROOT / "scripts" / "11_collect_amis_prices.py"
spec = importlib.util.spec_from_file_location("collect_amis_module", script_path)
_mod = importlib.util.module_from_spec(spec)
spec.loader.exec_module(_mod)

COMMODITY_ALLOWLIST = _mod.COMMODITY_ALLOWLIST
PARSER_VERSION = _mod.PARSER_VERSION
parse_amis_date = _mod.parse_amis_date
parse_amis_html = _mod.parse_amis_html
parse_numeric_value = _mod.parse_numeric_value
run_collection = _mod.run_collection
load_market_district_map = _mod.load_market_district_map

SAMPLE_AMIS_HTML_WITH_VALUES = """
<!DOCTYPE html>
<html>
<head><title>AMIS ViewPrices</title></head>
<body>
<span id="ctl00_cphPage_lblMsg">Wheat</span>
<span id="ctl00_cphPage_lblquintal">[ All Prices are in Rs/100Kg specified otherwise ]</span>
<td id="ctl00_cphPage_Grd">
<table border='0' cellpadding='0' cellspacing='0' width='%100'>
<tr style="background-color:#FFFFE0;font-family:verdana;">
<td style="border-right: 1px solid black;font-family:verdana;">&nbsp;Dated:02-09-2026</td>
<td style="border-right: 1px solid black;font-family:verdana;">&nbsp;Graph</td>
<td style="border-right: 1px solid black;font-family:verdana;">&nbsp;Min</td>
<td style="border-right: 1px solid black;font-family:verdana;;">&nbsp;Max</td>
<td style="border-right: 1px solid black;font-family:verdana;">&nbsp;FQP</td>
<td style="font-family:verdana;">&nbsp;Quantity</td>
</tr>
<tr style="font-family:verdana;">
<td style="border-right: 1px solid black;">&nbsp;<b>1&nbsp<a href='http://www.amis.pk/ViewPrices.aspx?searchType=1&commodityId=1'>Lahore</a></b></td>
<td style="border-right: 1px solid black;">&nbsp; <a href="http://www.amis.pk/reports/CommodityChart.aspx?cmd=1&city=1">Graph</a></td>
<td style="border-right: 1px solid black;">&nbsp;3200</td>
<td style="border-right: 1px solid black;">&nbsp;3400</td>
<td style="border-right: 1px solid black;">&nbsp;3300</td>
<td>&nbsp;150</td>
</tr>
<tr style="font-family:verdana;">
<td style="border-right: 1px solid black;">&nbsp;<b>2&nbsp<a href='http://www.amis.pk/ViewPrices.aspx?searchType=1&commodityId=1'>Faisalabad</a></b></td>
<td style="border-right: 1px solid black;">&nbsp; <a href="http://www.amis.pk/reports/CommodityChart.aspx?cmd=1&city=2">Graph</a></td>
<td style="border-right: 1px solid black;">&nbsp;3150</td>
<td style="border-right: 1px solid black;">&nbsp;3350</td>
<td style="border-right: 1px solid black;">&nbsp;3250</td>
<td>&nbsp;-</td>
</tr>
</table>
</td>
</body>
</html>
"""

SAMPLE_AMIS_HTML_ORDER_MISMATCH = """
<!DOCTYPE html>
<html>
<body>
<span id="ctl00_cphPage_lblMsg">Potato Fresh</span>
<span id="ctl00_cphPage_lblquintal">[ All Prices are in Rs/100Kg specified otherwise ]</span>
<td id="ctl00_cphPage_Grd">
<table border='0' cellpadding='0' cellspacing='0' width='%100'>
<tr style="background-color:#FFFFE0;">
<td>&nbsp;Dated:02-09-2026</td><td>&nbsp;Graph</td><td>&nbsp;Min</td><td>&nbsp;Max</td><td>&nbsp;FQP</td><td>&nbsp;Quantity</td>
</tr>
<tr>
<td>&nbsp;<b>1&nbsp<a href='#'>Multan</a></b></td>
<td>&nbsp;Graph</td>
<td>&nbsp;4500</td>
<td>&nbsp;4000</td>
<td>&nbsp;4200</td>
<td>&nbsp;50</td>
</tr>
</table>
</td>
</body>
</html>
"""


def test_parse_amis_date():
    iso, raw = parse_amis_date("02-09-2026")
    assert iso == "2026-09-02"
    assert raw == "02-09-2026"

    iso2, _ = parse_amis_date("09/02/2026")
    assert iso2 == "2026-09-02"

    iso_inv, _ = parse_amis_date("invalid-date")
    assert iso_inv is None


def test_parse_numeric_value_null_preservation():
    assert parse_numeric_value("3200") == 3200.0
    assert parse_numeric_value("3,450.50") == 3450.50
    assert parse_numeric_value("-") is None
    assert parse_numeric_value("--") is None
    assert parse_numeric_value("N/A") is None
    assert parse_numeric_value("") is None
    assert parse_numeric_value("   ") is None


def test_market_district_mapping_resolution():
    mapping = load_market_district_map()
    assert len(mapping) >= 30
    assert mapping.get("lahore") == "Lahore District"
    assert mapping.get("faisalabad") == "Faisalabad District"
    assert mapping.get("multan") == "Multan District"
    assert mapping.get("unknown_mandi") is None


def test_parse_amis_html_with_values():
    mapping = {"lahore": "Lahore District", "faisalabad": "Faisalabad District"}
    records, reviews, err = parse_amis_html(
        html=SAMPLE_AMIS_HTML_WITH_VALUES,
        commodity_id=1,
        commodity_name="Wheat",
        source_url="http://www.amis.pk/ViewPrices.aspx?searchType=0&commodityId=1",
        retrieved_at="2026-09-01T12:00:00Z",
        market_district_map=mapping,
    )
    assert err is None
    assert len(records) == 2
    assert len(reviews) == 0

    r1 = records[0]
    assert r1["market_name"] == "Lahore"
    assert r1["district"] == "Lahore District"  # Resolved via mapping
    assert r1["commodity_name"] == "Wheat"
    assert r1["commodity_id"] == 1
    assert r1["price_date"] == "2026-09-02"
    assert r1["source_displayed_date"] == "02-09-2026"
    assert r1["min_price_pkr"] == 3200.0
    assert r1["max_price_pkr"] == 3400.0
    assert r1["fqp_price_pkr"] == 3300.0
    assert r1["quantity"] == 150.0
    assert r1["unit"] == "Rs/100Kg"
    assert r1["validation_status"] == "validated"
    assert r1["data_status"] == "official_amis"

    r2 = records[1]
    assert r2["market_name"] == "Faisalabad"
    assert r2["district"] == "Faisalabad District"
    assert r2["quantity"] is None  # Preserves '-' as None, never 0.0
    assert r2["validation_status"] == "validated"


def test_parse_amis_html_ordering_mismatch_creates_review():
    records, reviews, err = parse_amis_html(
        html=SAMPLE_AMIS_HTML_ORDER_MISMATCH,
        commodity_id=21,
        commodity_name="Potato Fresh",
        source_url="http://www.amis.pk/ViewPrices.aspx?searchType=0&commodityId=21",
        retrieved_at="2026-09-01T12:00:00Z",
    )
    assert err is None
    assert len(records) == 1
    assert len(reviews) == 1

    r = records[0]
    assert r["market_name"] == "Multan"
    assert r["validation_status"] == "needs_review"
    assert r["min_price_pkr"] == 4500.0
    assert r["max_price_pkr"] == 4000.0

    rev = reviews[0]
    assert rev["issue_type"] == "price_ordering_mismatch"
    assert "exceeds Max price" in rev["issue_description"]
    assert rev["market_name"] == "Multan"


def test_run_collection_with_fixtures():
    fixtures = {
        1: SAMPLE_AMIS_HTML_WITH_VALUES,
        21: SAMPLE_AMIS_HTML_ORDER_MISMATCH,
        22: SAMPLE_AMIS_HTML_WITH_VALUES,
    }

    prices_path = ROOT / "processed" / "amis_market_prices_v1.csv"
    orig_content = prices_path.read_text(encoding="utf-8") if prices_path.exists() else None

    try:
        result = run_collection(allowlist={1: "Wheat", 21: "Potato Fresh", 22: "Potato Store"}, sample_fixtures=fixtures)
        assert result["total_requests"] == 3
        assert result["total_records"] == 5
        assert result["total_reviews"] == 1
        assert len(result["manifest"]) == 3
        for entry in result["manifest"]:
            assert entry["http_status"] == 200
            assert entry["parser_version"] == PARSER_VERSION
    finally:
        if orig_content is not None:
            prices_path.write_text(orig_content, encoding="utf-8")
