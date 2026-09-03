# Resume State Manifest — Kisaan Dost

- **Generated:** 2026-08-31 (read-only inspection only)
- **Inspection root:** `D:\KisaanDost` (project skeleton) with nested data folder
  `D:\KisaanDost\Kisaan_Dost_Data` (canonical source of truth for all analysis)
- **Companion files:** `resume_state_manifest.json` (full machine-readable
  manifest with sha256 hashes for every file), `resume_blockers.md` (hard
  blockers and soft constraints for the next session)
- **Method:** every file was hashed with sha256; every CSV was parsed with
  `csv.reader` (excel dialect) to count rows/columns and detect `year`,
  `month`, `date`, and `district` columns for coverage summaries. No file was
  modified.

---

## 1. Totals

| Metric | Count |
|---|---:|
| Total files cataloged | 196 |
| Existing (code + config + skeleton + scripts + raw GEE + raw PBS PDFs) | 150 |
| Final (cleaned outputs + validated reports) | 32 |
| Pending (new weather JSONs — not yet ingested) | 12 |
| Ignore (scratch `_tmp_*` files from a prior session) | 2 |

**Total size of cataloged data (excluding skeleton):** ≈ 87 MB, dominated by
the four crop-statistic PDFs (65 MB) and the twelve NASA POWER GeoJSONs
(15.8 MB).

---

## 2. Status legend

| Status | Meaning |
|---|---|
| `final` | Cleaned / validated output of a prior pipeline step. **Must not be overwritten.** |
| `existing-raw` | Source data as exported from GEE, PBS PDF, or reference image. Must not be overwritten. |
| `existing` | Project skeleton or script. Stable. |
| `pending` | New input — valid format, not yet ingested or merged. |
| `ignore` | Transient scratch files from a prior session; should be triaged, not used as inputs. |

---

## 3. Processed / final outputs (authoritative source of truth)

### 3.1 District-level remote-sensing master

| File | Rows | Cols | Date range | Districts | sha256 prefix |
|---|---:|---:|---|---:|---|
| `Kisaan_Dost_Data/processed/district_master_clean.csv` | 1,904 | 18 | 2022-01 to 2026-08 | 34 | `f7f533559add` |
| `Kisaan_Dost_Data/processed/district_master_data_dictionary.csv` | 18 | 3 | — | — | `cc89c3e133db` |

Join key: `(year, month, district)`. Column set:
`NDVI_mean`, `NDWI_mean`, `rainfall_total_mm`, `rainfall_mean_mm_per_day`,
`temp_max_c`, `temp_mean_c`, `temp_min_c`, `soil_moisture_0_7cm`,
`soil_moisture_7_28cm`, `landcover_crops_km2`, `landcover_cropland_fraction`,
`NDVI_delta`, `NDWI_delta`, `soil_0_7_delta`, `soil_7_28_delta`.
Validated by `scripts/validate_district_master.py` (0 errors, 9 warnings).

### 3.2 Province-wide monthly aggregates

| File | Rows | Cols | Date range | sha256 prefix |
|---|---:|---:|---|---|
| `Punjab_Monthly_Clean.csv` | 32 | 22 | 2024-01 to 2026-08 | `db646abe4b53` |
| `Punjab_Monthly_Clean_2022_2026.csv` | 56 | 26 | 2022-01 to 2026-08 | `a7ebad131f58` |
| `Punjab_Monthly_Features.csv` | 32 | 31 | 2024-01 to 2026-08 | `cf7bbeca1e02` |
| `Punjab_Monthly_Features_2022_2026.csv` | 56 | 41 | 2022-01 to 2026-08 | `2a694fd54501` |
| `Punjab_Monthly_Risk_Score.csv` | 32 | 35 | 2024-01 to 2026-08 | `60fa251b6005` |
| `Punjab_Monthly_Risk_Score_2022_2026.csv` | 56 | 45 | 2022-01 to 2026-08 | `2d16e65e3c35` |

The `_2022_2026` variants are the current authoritative province-wide series;
the older 2024-01-onward files are retained for reproducibility.

### 3.3 PBS Punjab Integrated Agricultural Census 2024 extracts

All extracted from `IAC-Punjab-Report-25-05-2026-1-1_copy.pdf` (288 pages,
native text). Validated by `scripts/validate_pbs_extracted_tables.py` —
**exit 0, 37/37 checks passed** (4 info notes on known census rounding /
intentional blanks). Coverage: 36 districts + Cholistan Area = 37 reporting
units.

| File | Rows | Cols | Districts | sha256 prefix |
|---|---:|---:|---:|---|
| `pbs_farm_structure.csv` | 37 | 9 | 37 | `f39ccb40fc28` |
| `pbs_land_tenure.csv` | 37 | 18 | 37 | `4a721141ee96` |
| `pbs_irrigation.csv` | 37 | 21 | 37 | `d50650d33c3b` |
| `pbs_crops.csv` | 703 | 9 | 37 | `efa0815faefe` |
| `pbs_machinery.csv` | 37 | 22 | 37 | `0672eec5a8f7` |
| `pbs_livestock.csv` | 333 | 6 | 37 | `cd8bdee0c82a` |
| `pbs_modern_farming.csv` | 37 | 18 | 37 | `9ccbc4441d9e` |
| `pbs_credit.csv` | 0 | 7 | 0 | `945eecd858a8` |
| `pbs_data_dictionary.csv` | 110 | 6 | — | `89f5072ed025` |

Note: three PBS reporting units (Chiniot District, Nankana Sahib District,
Cholistan Area) are not in the 34-district remote-sensing master. A
left-join from `district_master_clean.csv` will drop them automatically —
see `resume_blockers.md` §S3 for the recommended context-only handling.

---

## 4. Pending inputs (new NASA POWER weather JSONs, not yet ingested)

| File | Parameter | Date range | Features | sha256 prefix |
|---|---|---|---:|---|
| `Historical Data/2022-PRECTOTCORR.json` | PRECTOTCORR (corrected precipitation) | 20220101 – 20221231 | 117 | `9b0fd9ee1f32` |
| `Historical Data/2022-RH2M.json` | RH2M (2-m relative humidity) | 20220101 – 20221231 | 117 | `087c5dfd6386` |
| `Historical Data/2022-T2M.json` | T2M (2-m air temperature) | 20220101 – 20221231 | 117 | `e982c69ba71a` |
| `Historical Data/2023-PRECTOTCORR.json` | PRECTOTCORR | 20230101 – 20231231 | 117 | `6a346a639b1c` |
| `Historical Data/2023-RH2M.json` | RH2M | 20230101 – 20231231 | 117 | `5f1c8d7dbda9` |
| `Historical Data/2023-T2M.json` | T2M | 20230101 – 20231231 | 117 | `6a2b0ae4afad` |
| `Historical Data/2024-PRECTOTCORR.json` | PRECTOTCORR | 20240101 – 20241231 | 117 | `ed2b915f5b02` |
| `Historical Data/2024-RH2M.json` | RH2M | 20240101 – 20241231 | 117 | `bf2f2eafdfb6` |
| `Historical Data/2024-T2M.json` | T2M | 20240101 – 20241231 | 117 | `cd82f4913f59` |
| `Historical Data/2025-PRECTOTCORR.json` | PRECTOTCORR | 20250101 – 20251231 | 117 | `a1c814c635ec` |
| `Historical Data/2025-RH2M.json` | RH2M | 20250101 – 20251231 | 117 | `5b43c96abe6d` |
| `Historical Data/2025-T2M.json` | T2M | 20250101 – 20251231 | 117 | `569c9fc07797` |

**Format:** NASA POWER v2.9.7 daily GeoJSON, source product **MERRA2**,
time standard **LST**, fill value **-999**. Each file has 117 Point features
on a ~1° grid across Punjab. The sample grid point is at lon=70, lat=28.
Each feature's `properties` dict holds a single named parameter whose value
is a date → value map (length matches the file's date range).

**What has not been done:** parsing, daily→monthly aggregation, spatial
aggregation from 117 grid points to 34 districts, or merge into
`district_master_clean.csv`. All of this is blocked on the missing district
boundary GeoJSON (see `resume_blockers.md` §B1).

---

## 5. Raw inputs (not yet ingested or merged, preserved as-is)

### 5.1 GEE district-level monthly CSVs (30 files)

All at `Kisaan_Dost_Data/District data/<Variable>_Districts_Punjab_<Year>[_Monthly].csv`.
34 districts × 12 months (2022-2025) or 8 months (2026 Jan-Aug).

| Variable | Files | Typical rows | Typical cols | Notes |
|---|---:|---:|---:|---|
| NDVI | 5 | 408 (or 272 in 2026) | ~7 | single `NDVI_mean` |
| NDWI | 5 | 408 / 272 | ~7 | single `NDWI_mean` |
| Rainfall | 5 | 408 / 272 | ~8 | 2022-24 has `rainfall_mean_mm_per_day` + `rainfall_total_mm`; 2025-26 single `Rainfall_mm` |
| SoilMoisture | 5 | 408 / 272 | ~8 | 2022-24 has two layers; 2025-26 single `SoilMoisture` |
| Temperature | 5 | 408 / 272 | ~9 | 2022-24 has max/mean/min; 2025-26 single `Temperature_C` |
| LandCover | 5 | 408 / 34 | 14→5 | 2022-24 monthly class areas; 2025-26 annual `Cropland_Fraction` |

All already merged into `district_master_clean.csv`; the raw exports are
kept as immutable inputs.

### 5.2 GEE province-level monthly CSVs (30 files)

At `Kisaan_Dost_Data/<Variable>_Punjab_<Year>_Monthly.csv`. Each is a single
Punjab-wide mean per month (≈12–20 rows × 4–6 cols). Already merged into
the `Punjab_Monthly_*` series.

### 5.3 Crop-statistics PDFs (4 files, 65 MB total)

| File | Pages | Year |
|---|---:|---|
| `District Wise Crop data 2022-23_copy.pdf` | 206 | 2022-23 |
| `District Wise Crop data 2023-24_copy.pdf` | 207 | 2023-24 |
| `Kharif Rabi Estimates in Punjab 2024-25_copy.pdf` | 203 | 2024-25 |
| `IAC-Punjab-Report-25-05-2026-1-1_copy.pdf` | 288 | 2024 (census) |

The IAC census PDF has already been extracted into the PBS CSV set (§3.3).
The three district-wise crop-statistic PDFs have not been tabularly
extracted — they are 200+ pages each and full extraction is a separate task.

### 5.4 Province-level context images (8 files, ≈877 KB)

`Land Utilization.jpeg`, `Water Availability.jpeg`, plus six images across
`Agriculture GDP/`, `Cropped Area Stats/`, `Export, Import & Trading/`.
Values are readable but have not been tabulated; they are reference-only.

---

## 6. Reports and scripts (existing, final)

### 6.1 Reports (14 files)

| File | Topic |
|---|---|
| `monthly_data_quality_report.md` | 2024-onward monthly data quality |
| `monthly_data_quality_2022_2026.md` | Full 2022-2026 monthly quality check |
| `data_dictionary.csv` | Variable dictionary for the 2024-onward series |
| `feature_engineering_report.md` | 2024-onward feature design |
| `feature_engineering_report_2022_2026.md` | Full 2022-2026 feature design |
| `risk_methodology.md` | Rule-based risk score design (2024-onward) |
| `risk_methodology_2022_2026.md` | Full 2022-2026 risk score design |
| `monthly_trends.png`, `monthly_trends_2022_2026.png` | Trend charts |
| `risk_trends.png`, `risk_trends_2022_2026.png` | Risk score charts |
| `district_data_inventory.md` | District-level data inventory |
| `district_data_quality_report.md` | `district_master_clean` quality report |
| `pbs_extraction_quality_report.md` | PBS census extraction quality report |

### 6.2 Scripts (11 files)

| Script | Purpose |
|---|---|
| `create_historical_monthly_clean.py` | Produces `Punjab_Monthly_Clean_2022_2026.csv` |
| `create_historical_features.py` | Produces `Punjab_Monthly_Features_2022_2026.csv` |
| `create_historical_risk_score.py` | Produces `Punjab_Monthly_Risk_Score_2022_2026.csv` |
| `create_monthly_features.py` | 2024-onward feature engineering |
| `create_risk_score.py` | 2024-onward risk score |
| `create_district_master_clean.py` | Merges 30 district CSVs into `district_master_clean.csv` |
| `validate_monthly_data.py` | 2024-onward monthly validator |
| `validate_historical_monthly_data.py` | Historical monthly validator |
| `validate_district_master.py` | District-master validator |
| `extract_pbs_agricultural_census.py` | PBS PDF extractor |
| `validate_pbs_extracted_tables.py` | PBS extract validator (exit 0) |

---

## 7. Project skeleton (`D:\KisaanDost\*`, excluding `Kisaan_Dost_Data`)

| Category | Count | Notes |
|---|---:|---|
| Skeleton code (`.py`, `.dart`, `.tsx`, `.ts`, `.css`) | 47 | Backend FastAPI endpoints, Flutter feature stubs, Next.js pages — all placeholder |
| Skeleton config (READMEs, Docker, Makefile, pubspec, tsconfig, etc.) | 15 | Standard repo scaffolding |
| Skeleton other (Makefile, `.gitkeep`, etc.) | 1 | — |
| Architecture docs | 4 | System architecture, data flow, ERD, deployment |

None of these files are the target of the next phase. They are stable and
untouched by the analysis work.

---

## 8. Scratch files (ignore)

Two files at the data root dated 2026-08-30, named `_tmp_annex.txt`
(7,765 bytes) and `_tmp_method.txt` (12,762 bytes). Almost certainly
transient working notes from the PBS extraction session. They should be
renamed to durable names or deleted before the next phase, but they are
not inputs to any merge.

---

## 9. Exact last completed step (single line)

> **`scripts/validate_pbs_extracted_tables.py` exit 0 — 2026-08-30 13:07
> local time.** Every file produced before that moment is `final` or
> `existing-raw` in this manifest. The next pipeline step (NASA POWER
> weather ingestion) is blocked on the missing district boundary GeoJSON.
