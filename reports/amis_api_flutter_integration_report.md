# AMIS Punjab Market Price Connector, Scheduled Updates & Flutter Integration Report

- **Project:** Kisaan Dost Agricultural Platform
- **Task:** Phase 7B: AMIS Punjab Scheduled Updates + Commodity Expansion
- **Timestamp (UTC):** `2026-09-01T22:15:00+00:00`
- **Status:** **COMPLETE / FULLY VALIDATED**

---

## 1. Executive Summary

Phase 7B extends the official **Agriculture Marketing Information Service (AMIS) Punjab** connector (`http://www.amis.pk/`) with:
1. **Expanded Commodity Catalog:** 12 verified Punjab-relevant crops (Wheat, Rice Basmati Super, Rice IRRI, Maize, Potato Fresh, Potato Store, Onion, Tomato, Seed Cotton/Phutti, Sugarcane, Gram Black, Moong).
2. **Automated Daily Collection Runner:** Scripted runner ([`run_daily_amis_collection.py`](file:///d:/KisaanDost/Kisaan_Dost_Data/scripts/run_daily_amis_collection.py) & [`.bat`](file:///d:/KisaanDost/Kisaan_Dost_Data/scripts/run_daily_amis_collection.bat)) executing 1–2 times daily with a hard limit of 1 HTTP request per commodity per run (max 12 HTTP requests total).
3. **Verified Market-to-District Mapping:** Authoritative crosswalk table ([`amis_market_district_mapping_v1.csv`](file:///d:/KisaanDost/Kisaan_Dost_Data/processed/amis_market_district_mapping_v1.csv)) mapping 39 Punjab Mandis to official districts.
4. **"Today's Top Movers" Feed:** Observational retrospective daily price change comparisons (`GET /api/v1/market/movers`), strictly without price forecasting or buy/sell recommendations.
5. **Flutter Mobile Screen:** Interactive commodity chips, horizontal Top Movers carousel, and source-attributed wholesale rate cards in English and Urdu.

---

## 2. Expanded Allowlisted Commodities

| Commodity ID | Commodity Name | Verified Unit | Default Market |
|---|---|---|---|
| `1` | Wheat | `Rs/100Kg` | Lahore Mandi |
| `3` | Rice Basmati Super (New) | `Rs/100Kg` | Lahore Mandi |
| `4` | Rice (IRRI) | `Rs/100Kg` | Lahore Mandi |
| `9` | Gram Black Bareek | `Rs/100Kg` | Lahore Mandi |
| `11` | Moong | `Rs/100Kg` | Lahore Mandi |
| `17` | Maize | `Rs/100Kg` | Lahore Mandi |
| `21` | Potato Fresh | `Rs/100Kg` | Lahore Mandi |
| `22` | Potato Store | `Rs/100Kg` | Lahore Mandi |
| `23` | Onion | `Rs/100Kg` | Lahore Mandi |
| `26` | Tomato | `Rs/100Kg` | Lahore Mandi |
| `49` | Seed Cotton(Phutti) | `Rs/100Kg` | Lahore Mandi |
| `125` | Sugarcane | `Rs/100Kg` | Lahore Mandi |

---

## 3. Market-to-District Mapping Strategy

- **Crosswalk Location:** [`Kisaan_Dost_Data/processed/amis_market_district_mapping_v1.csv`](file:///d:/KisaanDost/Kisaan_Dost_Data/processed/amis_market_district_mapping_v1.csv)
- **Verified Mandis:** 39 Mandis mapped directly to authoritative Punjab District Boundary master names (`<District Name> District`).
- **Unmapped Fallback:** Mandis without explicit verified mapping retain `district = null`.

---

## 4. FastAPI Backend Endpoints

| Endpoint | Method | Output Schema | Description |
|---|---|---|---|
| `/api/v1/market/commodities` | `GET` | `MarketCommoditiesResponse` | Returns expanded catalog of 12 allowlisted commodities |
| `/api/v1/market/latest?commodity=<name>` | `GET` | `MarketLatestResponse` | Returns latest validated AMIS wholesale price records |
| `/api/v1/market/movers` | `GET` | `MarketMoversResponse` | Returns observational top traded commodities with prices |
| `/api/v1/market/history?commodity=<name>&start=YYYY-MM-DD` | `GET` | `MarketHistoryResponse` | Returns historical price records with strict date validation |
| `/api/v1/market/summary?crop=<name>` | `GET` | `{"success": true, "data": ...}` | Backward-compatible dashboard summary |

---

## 5. Verification Matrix

| Test Suite | Scope | Result |
|---|---|---|
| **AMIS Connector Pipeline Tests** | `pytest Kisaan_Dost_Data/tests/test_amis_market_connector.py -v` | **6 / 6 PASS** |
| **Backend Market API Tests** | `pytest tests/test_market_api.py -v` | **7 / 7 PASS** |
| **Root Backend Tests** | `pytest tests -q -rs --tb=short` | **77 / 77 PASS** |
| **Data Pipeline Tests** | `pytest Kisaan_Dost_Data/tests -q -rs --tb=short` | **390 / 390 PASS** |
| **Flutter Unit & Widget Tests** | `flutter test` | **68 / 68 PASS** |
| **Flutter Static Analysis** | `flutter analyze` | **0 issues found (CLEAN)** |
| **Handoff Completeness Gate** | `python scripts/check_handoff_completeness.py` | **COMPLETE (0 Active Blockers)** |
