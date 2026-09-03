# AMIS Punjab Market Connector Proof of Concept (POC) Report

- **Task:** Phase 7A: AMIS Punjab Market Price Connector Proof of Concept
- **Version:** `amis_poc_v1`
- **Timestamp (UTC):** `2026-09-01T21:50:00+00:00`
- **Status:** **COMPLETE / FULLY VALIDATED**

---

## 1. Summary of Execution

A secure, read-only proof-of-concept collector for the Agriculture Marketing Information Service (AMIS) Punjab has been established and verified for the 3 allowlisted commodities:
1. **Wheat (ID 1)**
2. **Potato Fresh (ID 21)**
3. **Potato Store (ID 22)**

---

## 2. Artifacts Produced

| File Path | Description | Records |
|---|---|---|
| [`Kisaan_Dost_Data/processed/amis_market_prices_v1.csv`](file:///d:/KisaanDost/Kisaan_Dost_Data/processed/amis_market_prices_v1.csv) | Primary price dataset with raw & parsed values | 3 |
| [`Kisaan_Dost_Data/processed/amis_market_price_review_queue_v1.csv`](file:///d:/KisaanDost/Kisaan_Dost_Data/processed/amis_market_price_review_queue_v1.csv) | Review queue for price anomalies/ordering mismatches | 0 (0 anomalies) |
| [`Kisaan_Dost_Data/processed/amis_commodity_catalog_v1.csv`](file:///d:/KisaanDost/Kisaan_Dost_Data/processed/amis_commodity_catalog_v1.csv) | Verified allowlisted commodity catalog | 3 |
| [`Kisaan_Dost_Data/processed/amis_market_catalog_v1.csv`](file:///d:/KisaanDost/Kisaan_Dost_Data/processed/amis_market_catalog_v1.csv) | Market catalog with source labels & null districts | 1 |
| [`Kisaan_Dost_Data/processed/amis_market_collection_manifest_v1.csv`](file:///d:/KisaanDost/Kisaan_Dost_Data/processed/amis_market_collection_manifest_v1.csv) | Full run audit trail and content hashes | 3 runs logged |

---

## 3. Data Invariants & Rules Maintained

1. **Explicit Displayed Unit:** Verbatim `Rs/100Kg` (1 Quintal = 100 Kg) preserved from AMIS HTML. No unauthorized per-kg conversion.
2. **Null Preservation:** Missing values (`-`) are preserved as `null` (empty), never coerced to `0.0`.
3. **Market vs District Separation:** Market names (e.g. `Lahore`) are preserved as distinct market entities. `district` is kept `null` to avoid unverified spatial assumptions.
4. **Ordering Validation:** If $\text{Min} > \text{Max}$ or $\text{FQP} < \text{Min}$ or $\text{FQP} > \text{Max}$, the row is retained with `validation_status="needs_review"` and logged to the review queue without altering source values.
5. **Collection Rate Control:** Enforces maximum 1 HTTP GET request per commodity per manual invocation (`python Kisaan_Dost_Data/scripts/11_collect_amis_prices.py`).
