# Monthly Data Quality Report — Kisaan Dost (Punjab, Pakistan)

- **Generated:** 2026-08-29
- **Raw data folder:** `D:\Kisaan_Dost_Data` (18 monthly CSV exports; raw files untouched)
- **Clean dataset:** `processed/Punjab_Monthly_Clean.csv` (32 rows x 22 columns)
- **Validation script:** `scripts/validate_monthly_data.py` (re-run: `cd D:\Kisaan_Dost_Data && python scripts/validate_monthly_data.py`)
- **Validator result:** PASSED — 0 errors, 8 warnings

## 1. Dataset overview

The monthly export contains **18 CSV files**: 6 variables (NDVI, NDWI, Rainfall,
Temperature, SoilMoisture, LandCover) x 3 years (2024, 2025, 2026). The earlier
annual `*_Stats_Punjab_*.csv` and `Punjab_Stats_*.csv` files are no longer present
in the folder; this export replaced them. All data is **Punjab-wide** (one
aggregate row per variable-month; no district, tehsil, or farm identifiers).

## 2. File inventory

| Variable | 2024 rows | 2025 rows | 2026 rows | Total months |
|---|---|---|---|---|
| NDVI | 12 | 12 | 8 | 32 |
| NDWI | 12 | 12 | 8 | 32 |
| Rainfall | 12 | 12 | 8 | 32 |
| Temperature | 12 | 12 | 8 | 32 |
| SoilMoisture | 12 | 12 | 8 | 32 |
| LandCover | 12 | 12 | 8 | 32 |

Total: 192 raw rows across 18 files, collapsing to 32 unique (year, month) pairs.

## 3. Temporal coverage

- **Range:** 2024-01 through 2026-08 (32 of 36 months in the 2024-01..2026-12 grid).
- **Missing months:** 2026-09, 2026-10, 2026-11, 2026-12. 2026 is a **partial
  year** (Jan-Aug only), consistent with the export date (2026-08-29). August
  2026 itself may be incomplete (see section 8).
- **Frequency:** monthly. Raw files carry separate integer `year` and `month`
  columns; there is no date column.
- **Month coverage is identical across all 6 variables** (verified by the
  validator), so all variables merge cleanly on (year, month) with no missing
  cells introduced.

## 4. Missing values and duplicates

- **Missing values:** none. Every numeric cell in all 18 files is populated.
- **Duplicate (year, month) records:** none in any file.
- **Duplicate columns:** none.

## 5. Units

| Variable | Column(s) | Unit |
|---|---|---|
| NDVI | `NDVI_mean` | unitless index (-1..1) |
| NDWI | `NDWI_mean` | unitless index (-1..1) |
| Rainfall | `rainfall_mean_mm_per_day` | mm/day |
| Rainfall | `rainfall_total_mm` | mm/month |
| Temperature | `temp_max_c`, `temp_mean_c`, `temp_min_c` | degrees Celsius |
| Soil moisture | `soil_moisture_0_7cm`, `soil_moisture_7_28cm` | m3/m3 volumetric water content (0-7 cm and 7-28 cm layers) |
| Land cover | 9 x `*_km2` columns | km2 of area per class |

## 6. Cleaning steps applied

| Rule | Action taken |
|---|---|
| Keep raw files unchanged | Raw files were opened read-only; nothing was modified, moved, renamed, or deleted |
| Parse and standardize the date column | Raw files have no date column (separate `year` + `month`); an ISO 8601 `date` column (YYYY-MM-01) was derived |
| Sort rows chronologically | Clean file sorted by (year, month); verified by the validator |
| Do not invent missing months or values | Only the 32 exported months exist in the clean file; 2026-09..2026-12 are absent |
| Do not fill missing values unless documented | No missing values were found; nothing was filled |
| Convert temperature from Kelvin only if Kelvin | Values are already Celsius (columns `temp_*_c`; observed range 2.28-45.52 deg C). **No conversion applied** |
| Keep rainfall in millimeters | Kept: monthly mean (mm/day) and monthly total (mm/month) |
| Keep NDVI and NDWI unitless | Kept unchanged |
| Preserve soil moisture and document units | Preserved exactly; units are m3/m3 volumetric for 0-7 cm and 7-28 cm layers |
| Add year, month, season columns | `year` and `month` retained as integers; `season` added (Pakistan Meteorological Department convention: Winter = Dec-Feb, Spring = Mar-May, Summer/monsoon = Jun-Sep, Autumn = Oct-Nov) |
| Report missing months and suspicious values | Section 8; the validator re-flags them on every run |

Columns not carried into the clean file (documented, dropped by design):
- `system:index` — a per-file row counter with no analytical content.
- `.geo` — empty MultiPoint geometry (`{"type":"MultiPoint","coordinates":[]}`) in every row of every file.

Values in the clean file are byte-identical to the raw exports (full original
precision preserved; the validator checks every value against the raw files).

## 7. Spatial level

Punjab-wide aggregates only. NDVI/NDWI/rainfall/temperature/soil moisture are
province-level means; LandCover columns are province-level class areas in km2.
No district, tehsil, farm, or pixel identifiers exist anywhere in the export.

## 8. Suspicious values and data-quality concerns

**Zero rainfall in a monsoon month**

| Location | Value | Concern | Action |
|---|---|---|---|
| 2026-08, `rainfall_total_mm` and `rainfall_mean_mm_per_day` | 0.0 | August is a monsoon month (Aug 2024: 176.0 mm; Aug 2025: 130.6 mm). Zero is almost certainly a partial-month export artifact or a data gap, not real weather | Preserved as-is; flagged |

**Land-cover class totals below Punjab's area (partial mosaic coverage)**

The nine land-cover classes should sum to roughly Punjab's area of 205,344 km2.
Seven months fall more than 2% short, meaning parts of the province were not
classified (likely cloud cover / mosaic gaps):

| Month | Class sum (km2) | Shortfall (km2) | Shortfall % |
|---|---|---|---|
| 2024-01 | 100,682 | 104,662 | 51% |
| 2024-07 | 194,813 | 10,531 | 5% |
| 2024-08 | 141,166 | 64,178 | 31% |
| 2025-07 | 162,388 | 42,956 | 21% |
| 2025-08 | 189,996 | 15,348 | 7% |
| 2026-04 | 196,352 | 8,992 | 4% |
| 2026-08 | 201,237 | 4,107 | 2% |

Implication: land-cover class areas are **not directly comparable across
months** without normalizing by classified area. All other months sum to
~205,190 km2 as expected.

**Other concerns**

1. **NDWI definition mismatch.** Monthly `NDWI_mean` is negative in all 32
   months (-0.474 to -0.278; 2024 average -0.359), while the earlier annual
   export reported positive means (2024: +0.072; 2025: +0.041; 2026: +0.015).
   The two exports almost certainly use different NDWI variants or sources.
   Do not mix annual and monthly NDWI values.
2. **Rainfall totals differ from the earlier annual export**: monthly sums are
   2024: 469.1 mm vs 482.0 mm (-2.7%); 2025: 484.2 mm vs 531.3 mm (-8.9%);
   2026 Jan-Aug: 275.3 mm vs 284.3 mm (-3.2%). Likely different aggregation
   windows or methods. (Annual figures from the inspection record of
   2026-08-29; those files no longer exist.)
3. **Land-cover volatility.** Class areas swing heavily month to month (e.g.,
   `crops_km2` 44,213 -> 127,428 km2 between Jan and Feb 2024). This is
   classification noise plus seasonality, not real land change; treat as
   approximate.
4. **Raw column order is inconsistent** across variables (`month`/`year`
   positioned differently per file) — handled by name in cleaning, but a hazard
   for positional parsing.
5. **2026 is partial** (8 months) and August 2026 may itself be incomplete;
   year-over-year comparisons for 2026 must use Jan-Aug windows only.

## 9. Limitations

- Punjab-wide aggregates only; no district/farm-level analysis is possible
  with this export.
- 32 monthly observations per variable — small for modelling; a longer history
  or finer spatial resolution would be needed for robust ML.
- Land-cover months with coverage gaps (section 8) should be normalized or
  excluded in any analysis that uses them.

## 10. Next steps (awaiting approval)

No machine-learning model or risk score has been created, per instructions.
When approved, sensible next steps: seasonal climatology baselines, anomaly
detection (e.g., drought stress from NDVI + rainfall + soil moisture), and a
crop-calendar-aware risk score for Punjab-wide advisory content.
