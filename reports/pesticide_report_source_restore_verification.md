# Official Pesticide Report Source Restore & Reproducibility Verification Report

- **Task:** Phase 3: Official Pesticide Report Source Portability Restore + Reproducibility Verification
- **Timestamp (UTC):** `2026-09-01T20:37:00+00:00`
- **Project Root:** `D:\KisaanDost`
- **Status:** **SUCCESS / BLOCKER 2 RESOLVED**

---

## 1. Provenance & Source Portability Verification

The verified official Punjab annual report was copied from the external workstation path into the project's relative data directory.

| Attribute | External Original | In-Project Destination | Status |
|---|---|---|---|
| **Path** | `D:\Kisaan_Dost_Data\Annual Report 2024-25_copy.pdf` | `D:\KisaanDost\Kisaan_Dost_Data\Annual Report 2024-25_copy.pdf` | Restored |
| **Size** | `8,058,335` bytes | `8,058,335` bytes | **EXACT MATCH** |
| **SHA-256** | `d8088a00e0614407091bbc56df42b152ec300787f3f0863eea529c158416c725` | `d8088a00e0614407091bbc56df42b152ec300787f3f0863eea529c158416c725` | **EXACT MATCH** |
| **Pages** | 43 | 43 | **EXACT MATCH** |
| **Text Layer** | Readable (45,005 characters) | Readable (45,005 characters) | **EXACT MATCH** |

> **Blocker 2 (Pesticide PDF Source Portability) is now fully RESOLVED.** The project repository is self-contained and reproducible.

---

## 2. Ingestion Pipeline & Validation Results

### Exact Commands Run
1. `python scripts/07_ingest_pesticide_report.py`
   - **Result:** Status `ok`, 72 facts, 43 chunks, 1 review item, 43 pages, 33 table warnings.
2. `python scripts/08_validate_pesticide_report.py`
   - **Result:** Success `True`, 0 errors, 0 info items, 0 dose integrity violations.

### Comparison Against Prior Baseline
- **Fact Count:** 72 (Exact match)
- **Chunk Count:** 43 (Exact match)
- **Review Queue Count:** 1 (`fact_00028`, ambiguous dose — exact match)
- **Dose Integrity Violations:** 0 (Exact match)

Detailed CSV comparison is recorded in [`reports/pesticide_extraction_reproducibility_comparison.csv`](file:///d:/KisaanDost/reports/pesticide_extraction_reproducibility_comparison.csv).

---

## 3. Test & API Regression Verification

| Test Suite | Scope | Result |
|---|---|---|
| **Python Pesticide Tests** | `pytest tests/test_07_ingest_pesticide_report.py tests/test_08_validate_pesticide_report.py tests/test_pest_alerts_api.py -v --tb=short` | **25 passed in 19.61s** |
| **Flutter Pest Alert Tests** | `flutter test test/unit/pest_models_test.dart test/unit/pest_provider_test.dart test/widget/pest_alerts_screen_test.dart` | **12 passed in 2.0s** |
| **Root Backend Tests** | `python -m pytest tests -q -rs --tb=short` | **49 passed in 25.10s** |

---

## 4. Safety & Invariant Guarantees

1. **Zero Invented Dosages:** The ingestion engine enforces verbatim source excerpt matches for any dose text. Since the source document provides qualitative chemical names and pest thresholds without numeric per-acre formulas, `explicit_dose_text` is empty for all 72 facts.
2. **Untouched Subsystems:**
   - ML model checkpoint (`best_plantvillage_model_v2.pt`), weights, and class mapping were **not modified**.
   - NASA POWER weather datasets and joins were **not modified**.
   - JWT authentication, user store, and role guards were **not modified**.
   - Flutter UI layouts were **not modified**.

---

## 5. Rollback Instructions

If rollback is required:
1. Delete `Kisaan_Dost_Data/Annual Report 2024-25_copy.pdf`.
2. Revert `scripts/07_ingest_pesticide_report.py` default path to `../Kisaan_Dost_Data/...`.
