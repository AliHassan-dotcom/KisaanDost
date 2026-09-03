# Pesticide Extraction Reproducibility Comparison Report

- **Task:** Phase 3 Extraction Reproducibility Verification
- **Timestamp (UTC):** `2026-09-01T20:36:00+00:00`
- **Project Root:** `D:\KisaanDost`
- **Status:** **100% DETERMINISTIC MATCH / REPRODUCIBLE**

---

## 1. Executive Summary

Following the restoration of the official Punjab pesticide annual report PDF (`Annual Report 2024-25_copy.pdf`) to `Kisaan_Dost_Data/Annual Report 2024-25_copy.pdf`, the entire extraction pipeline ([`scripts/07_ingest_pesticide_report.py`](file:///d:/KisaanDost/scripts/07_ingest_pesticide_report.py)) and validator ([`scripts/08_validate_pesticide_report.py`](file:///d:/KisaanDost/scripts/08_validate_pesticide_report.py)) were executed.

The newly generated artifacts were compared against the prior validated baseline. **All metrics, fact counts, chunk counts, categories, review items, and verbatim excerpts match with 100% determinism.**

---

## 2. Metric-by-Metric Comparison

| Metric / Dimension | Prior Baseline Value | Rerun Generated Value | Match Status | Notes |
|---|---|---|---|---|
| **Source File Path** | `../Kisaan_Dost_Data/...` (external) | `Kisaan_Dost_Data/...` (in-repo) | **MATCH** | Restored to project-relative path |
| **Source File Size** | `8,058,335` bytes | `8,058,335` bytes | **EXACT MATCH** | Byte-identical |
| **Source SHA-256** | `d8088a00e061...` | `d8088a00e061...` | **EXACT MATCH** | Checksum verified |
| **PDF Page Count** | 43 | 43 | **EXACT MATCH** | 43 pages processed |
| **Extractable Text Chars** | 45,005 | 45,005 | **EXACT MATCH** | Zero text loss |
| **Extracted Facts Count** | 72 | 72 | **EXACT MATCH** | 72 advisory facts |
| **Extracted Chunks Count** | 43 | 43 | **EXACT MATCH** | Page-bounded chunks |
| **Review Queue Count** | 1 | 1 | **EXACT MATCH** | Fact `fact_00028` (ambiguous dose) |
| **Facts with Explicit Dose** | 0 | 0 | **EXACT MATCH** | Zero unverified dosages |
| **Dose Integrity Violations** | 0 | 0 | **EXACT MATCH** | Zero invented doses |
| **Table Warnings** | 33 | 33 | **EXACT MATCH** | QC filters applied consistently |
| **Validator Success** | `PASS` (0 errors) | `PASS` (0 errors) | **EXACT MATCH** | Clean validation output |

---

## 3. Fact Categories & Crop Distribution Breakdown

### Facts by Category
| Category | Count | Status |
|---|---|---|
| `pesticide_quality_control` | 26 | Verified |
| `pest_warning` | 21 | Verified |
| `general_agricultural_advisory` | 9 | Verified |
| `crop_disease_warning` | 7 | Verified |
| `pesticide_safety` | 5 | Verified |
| `inspection` | 3 | Verified |
| `laboratory_result` | 1 | Verified |
| **Total** | **72** | **100% Consistent** |

### Facts by Crop Mention
- `rice`: 18 facts
- `vegetables`: 11 facts
- `pulses`: 9 facts
- `sugarcane`: 8 facts
- `cotton`: 7 facts
- `citrus`: 6 facts
- `maize`: 6 facts
- `wheat`: 5 facts
- `mango`: 5 facts

---

## 4. Dose Safety & Non-Prescription Invariant

- **Explicit Dose Text in Source:** The official annual report contains qualitative advisories, pest outbreak thresholds, pesticide registrations, QC seizure figures, and chemical recommendations, but does not state dosage formulas per acre.
- **Strict Invariant Enforced:** Ingestion correctly outputs `explicit_dose_text: ""` for all 72 facts.
- **Zero Hallucination:** The system never attempts to invent, hallucinate, or interpolate pesticide dosages. The mobile app and API faithfully present `dose_guidance: "No official dose guidance in source document. Consult local extension officer before application."`.

---

## 5. Conclusion

The Punjabi pesticide advisory extraction pipeline is **fully portable and reproducible** from the in-repository PDF `Kisaan_Dost_Data/Annual Report 2024-25_copy.pdf`.
