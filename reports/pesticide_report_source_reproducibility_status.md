# Pesticide Report Source Reproducibility Status

## Current Status: RESTORED & FULLY REPRODUCIBLE

The official Punjab annual report PDF has been restored into the project-relative data directory at `Kisaan_Dost_Data/Annual Report 2024-25_copy.pdf`. The end-to-end extraction pipeline ([`scripts/07_ingest_pesticide_report.py`](file:///d:/KisaanDost/scripts/07_ingest_pesticide_report.py)) and validator ([`scripts/08_validate_pesticide_report.py`](file:///d:/KisaanDost/scripts/08_validate_pesticide_report.py)) have been executed, producing 100% deterministic, source-traceable outputs.

---

## Source Provenance & Integrity

| Property | Value |
|---|---|
| **Document Title** | Pest Warning and Quality Control of Pesticides Annual Report |
| **Reporting Period** | 2024-25 |
| **In-Repository Path** | `Kisaan_Dost_Data/Annual Report 2024-25_copy.pdf` |
| **Source Provenance** | Copied from external workstation backup (`D:\Kisaan_Dost_Data\Annual Report 2024-25_copy.pdf`) |
| **File Size** | `8,058,335` bytes |
| **Cryptographic Hash (SHA-256)** | `d8088a00e0614407091bbc56df42b152ec300787f3f0863eea529c158416c725` |
| **Page Count** | 43 |
| **Text Layer** | Readable (45,005 characters, 0 OCR errors) |

---

## Validated Extraction Outputs

| Path | Purpose | Verified State |
|---|---|---|
| `data/processed/pesticide_report_facts.csv` | Structured, source-traceable advisory facts | **72 facts**; all source page/excerpt checks pass. |
| `data/processed/pesticide_report_chunks.jsonl` | Page-preserving text chunks | **43 chunks**; 100% unique chunk IDs. |
| `data/processed/pesticide_report_review_queue.csv` | Human review backlog | **1 queued fact** (`fact_00028`, ambiguous dose). |
| `data/processed/pesticide_report_ingestion_meta.json` | Ingestion metadata & run statistics | 43 pages, 45,005 characters, status `ok`. |
| `reports/pesticide_report_analysis.md` | Category and crop distribution analysis | Generated and updated. |
| `reports/pesticide_report_extraction_quality.md` | Extraction quality report | **0 dose-integrity violations**, 100% valid page citations. |

---

## Safety & Non-Prescription Invariant

The Punjabi pesticide advisory feature adheres to strict agronomic safety invariants:
1. **Source Excerpt Requirement:** Every fact requires a verbatim source excerpt and page number from the official report.
2. **Zero Dose Hallucination:** The official document contains pest thresholds and chemical registrations without quantitative per-acre dosages. The system never interpolates or hallucinates dosage, directing farmers to consult certified extension officers.

---

## Blocker Status

- **Blocker 1 (Model Path Resolution):** **RESOLVED**
- **Blocker 2 (Pesticide PDF Portability):** **RESOLVED**
- **Overall Codebase Status:** **100% SELF-CONTAINED & FULLY VERIFIED**
