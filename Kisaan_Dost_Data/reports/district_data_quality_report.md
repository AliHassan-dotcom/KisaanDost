# District Data Quality Report — Kisaan Dost

- **Generated:** 2026-08-30
- **Input folder:** `D:\Kisaan_Dost_Data\District data`
- **Clean output:** `processed/district_master_clean.csv`
- **Data dictionary:** `processed/district_master_data_dictionary.csv`
- **Cleaning script:** `scripts/create_district_master_clean.py`
- **Validation script:** `scripts/validate_district_master.py`
- **Validator result:** PASSED — 0 errors, 9 warnings

## 1. Dataset overview

The district-level export contains **30 monthly CSV files** and **2 annual
land-cover CSVs** covering 34 Punjab districts. The clean dataset merges all
remote-sensing indicators horizontally by `(year, month, district)` into a single
long-format table.

| Metric | Value |
|---|---|
| Total clean rows | 1,904 |
| Districts | 34 |
| Date range | 2022-01-01 to 2026-08-01 |
| Unique month-dates | 56 |
| Columns | 18 |
| Legacy detailed rows (2022-2024) | 1,224 |
| Modern simplified rows (2025-2026) | 680 |

## 2. Temporal coverage

- **2022:** full year (12 months × 34 districts = 408 rows)
- **2023:** full year (408 rows)
- **2024:** full year (408 rows)
- **2025:** full year (408 rows)
- **2026:** January–August only (272 rows)
- **Missing:** 2026-09 through 2026-12 (not exported)

Every month in the covered range has exactly 34 district rows — no month is
partially missing.

## 3. Spatial coverage

- **Level:** District (not farm, not tehsil, not province-wide aggregate).
- **Districts:** 34 Punjab districts, consistently named across all files.
- **Boundaries:** No boundary shapefile or GeoJSON is available. Analysis is
tabulardistrict-level only; mapping is not possible without acquiring boundary data.

## 4. Cleaning steps applied

| Rule | Action |
|---|---|
| Keep raw files unchanged | All raw files opened read-only; nothing modified |
| Standardize district names | Trimmed whitespace, normalized internal spaces, kept `District` suffix (already consistent) |
| Standardize date column | Derived ISO 8601 `date` column (`YYYY-MM-01`) from `year` and `month` |
| Standardize units | Kept original units; documented in data dictionary. No conversions applied |
| Remove duplicate rows | None found; validator confirms no duplicate `(year, month, district)` keys |
| Do not invent missing values | Empty cells preserved where source data is missing or schema lacks the column |
| Keep landcover as support variable | `landcover_crops_km2` and `landcover_cropland_fraction` retained but flagged as support-only |
| Separate context tables | Crop PDFs and province-level image data documented as reference assets; not merged |
| Schema normalization | 2025-2026 single-value columns mapped to legacy column names with `missing_columns_note` |

## 5. Missing values and data gaps

| Column | Missing values | Reason |
|---|---|---|
| `NDVI_mean` | 6 | 2022-07 Narowal/Sialkot; 2024-01 Khanewal/Lodhran/Toba Tek Singh/Vehari |
| `NDWI_mean` | 6 | Same districts/months as NDVI |
| `rainfall_total_mm` | 34 | All districts for 2026-08 (entire month absent from source) |
| `rainfall_mean_mm_per_day` | 680 | 2025-2026 simplified schema provides only monthly total |
| `temp_max_c` | 680 | 2025-2026 simplified schema provides only mean temperature |
| `temp_min_c` | 680 | 2025-2026 simplified schema provides only mean temperature |
| `soil_moisture_7_28cm` | 680 | 2025-2026 simplified schema provides only topsoil value |
| `landcover_crops_km2` | 680 | 2025-2026 land-cover exports are annual `Cropland_Fraction` only |
| `landcover_cropland_fraction` | 1,224 | Annual fraction only available for 2025-2026; 2022-2024 use monthly class areas |

**No values were filled or interpolated.** Missing cells are preserved and
flagged in `missing_columns_note` where the schema change is the cause.

## 6. Suspicious values

- **Zero monsoon rainfall:** None flagged in the current clean dataset.
- **2026-08 rainfall:** Not zero — the entire month is **absent** from the source
  (34 missing rows). This is more severe than a zero value: it means no rainfall
  estimate exists for August 2026 at district level. The month should not be used
  for drought analysis without first verifying the source export.
- **Temperature and soil moisture 2025-2026:** Values are available but the loss
  of min/max and subsoil layers reduces heat-stress and deep-drought diagnostic
  power.

## 7. Schema inconsistency (2022-2024 vs 2025-2026)

The 2025-2026 exports switched to simplified single-value columns:

| Indicator | 2022-2024 | 2025-2026 | Impact |
|---|---|---|---|
| Rainfall | `rainfall_mean_mm_per_day` + `rainfall_total_mm` | `Rainfall_mm` | Cannot validate mean×days≈total; no daily pattern |
| Temperature | `temp_max_c`, `temp_mean_c`, `temp_min_c` | `Temperature_C` | Cannot detect heat extremes or diurnal range |
| Soil moisture | `soil_moisture_0_7cm`, `soil_moisture_7_28cm` | `SoilMoisture` | Only topsoil signal; subsoil drought invisible |
| LandCover | 9 class areas per month | Annual `Cropland_Fraction` | Cannot track monthly crop-area dynamics; static fraction only |

The clean dataset handles this by mapping modern columns to legacy names and
leaving unavailable legacy columns empty, with an explanatory note in
`missing_columns_note`.

## 8. Duplicates

No duplicate `(year, month, district)` records exist in the clean dataset.

## 9. Merge conflicts

| Conflict | Resolution |
|---|---|
| Column order varies across raw files | Handled by name-based merge, not position |
| Different column names for same concept (e.g., `Rainfall_mm` vs `rainfall_total_mm`) | Normalized to legacy names with schema flag |
| LandCover 2025/2026 are annual, not monthly | Merged as annual `landcover_cropland_fraction` applied to all months of the year |
| Missing NDVI/NDWI rows | Preserved as empty cells; no fill |
| 2026-08 rainfall completely missing | Preserved as empty cells; flagged in this report |

## 10. Missing data sources (blockers for deeper analysis)

| Source | Status | Why it matters |
|---|---|---|
| District boundaries (shapefile/GeoJSON) | Missing | Required for maps, spatial joins, and visual district identification |
| Irrigation/canal water data | Missing | Punjab agriculture is heavily irrigated; without irrigation data, rainfall deficits do not directly translate to crop stress |
| Farm-level ground truth | Missing | Cannot validate or train field-level models |

## 11. Province-level context assets

The following image/PDF files were inspected and documented as context. They are
not merged into the district analytical table because they are province-level or
require separate extraction:

- `District Wise Crop data 2022-23_copy.pdf` — district-level crop area/production/yield
- `District Wise Crop data 2023-24_copy.pdf` — district-level crop area/production/yield
- `Kharif Rabi Estimates in Punjab 2024-25_copy.pdf` — district-level crop estimates
- `Land Utilization.jpeg` — province-wide land utilization shares
- `Water Availability.jpeg` — province water availability by Rabi/Kharif and source
- `Agriculture GDP/*.jpeg` — agriculture GDP composition and growth rates
- `Cropped Area Stats/*.jpeg` — Kharif/Rabi cropped area distribution
- `Export, Import & Trading/*.jpeg` — food group trade balance and credit disbursement

## 12. Recommended analysis structure

For district-level advisory use, the clean dataset supports:

1. **District-level time-series monitoring** of NDVI, NDWI, rainfall, temperature,
   and soil moisture across 2022-2026.
2. **District-month anomaly detection** by comparing each district-month to its
   2022-2025 month-of-year baseline (computed separately per district).
3. **Ranking districts** by stress indicators within a given month.
4. **Tracking seasonal progression** per district.

Limitations to respect:
- Do not use land-cover area as a crop-health signal; use only as a support/context variable.
- Do not mix 2022-2024 detailed metrics with 2025-2026 simplified metrics without documenting the schema change.
- Exclude or flag 2026-08 rainfall until the source export is verified.
- Do not build farm-level or disease-diagnosis models with this data.
- Any spatial mapping requires acquiring district boundary files separately.

## 13. Reproduction

```bash
cd D:\KisaanDost_Data
python scripts/create_district_master_clean.py
python scripts/validate_district_master.py
```
