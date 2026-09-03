# Feature Engineering Report — Historical Monthly Punjab Dataset (2022–2026)

- **Generated:** 2026-08-29
- **Input:** `processed/Punjab_Monthly_Clean_2022_2026.csv` (56 rows x 26 columns, 2022-01 to 2026-08)
- **Output:** `processed/Punjab_Monthly_Features_2022_2026.csv` (56 rows x 41 columns)
- **Script:** `scripts/create_historical_features.py`
- **Chart:** `reports/monthly_trends_2022_2026.png`
- **Raw exports were not read for modification and remain untouched.**

## 1. Baseline definition

All baselines are **month-of-year means over the four complete years (2022, 2023,
2024, 2025)**, computed from the monthly data only. 2026 never contributes to
its own baseline. The old annual NDWI values are never used anywhere in this
pipeline.

| Month | NDVI | NDWI | Rainfall (mm) | Temp mean (C) | Soil 0-7 cm | Soil 7-28 cm |
|---|---|---|---|---|---|---|
| 1 | 0.373141 | -0.391773 | 20.014 | 12.373 | 0.138545 | 0.155460 |
| 2 | 0.435533 | -0.456331 | 15.589 | 16.705 | 0.139345 | 0.159161 |
| 3 | 0.415226 | -0.443294 | 26.161 | 22.053 | 0.148366 | 0.164179 |
| 4 | 0.259203 | -0.340424 | 14.981 | 28.158 | 0.126788 | 0.154427 |
| 5 | 0.204418 | -0.287705 | 17.567 | 32.572 | 0.114267 | 0.139210 |
| 6 | 0.219010 | -0.287480 | 39.293 | 34.254 | 0.123537 | 0.146083 |
| 7 | 0.275665 | -0.299969 | 159.209 | 32.131 | 0.215099 | 0.211268 |
| 8 | 0.359558 | -0.360448 | 116.342 | 30.787 | 0.227124 | 0.241602 |
| 9 | 0.392313 | -0.404507 | 44.701 | 30.476 | 0.170083 | 0.206564 |
| 10 | 0.338652 | -0.387453 | 7.380 | 26.303 | 0.128563 | 0.165166 |
| 11 | 0.272259 | -0.329861 | 4.084 | 20.116 | 0.124322 | 0.155379 |
| 12 | 0.335269 | -0.378853 | 3.206 | 14.872 | 0.112036 | 0.147426 |

## 2. New feature columns (15 added; all 26 clean columns retained)

| Column | Formula | Notes |
|---|---|---|
| `ndvi_baseline` | mean(`NDVI_mean`) for month *m* across 2022–2025 | supporting column; same value repeated for every row of month *m* |
| `ndwi_baseline` | mean(`NDWI_mean`) for month *m* across 2022–2025 | same value repeated for every row of month *m* |
| `rainfall_baseline_mm` | mean(`rainfall_total_mm`) for month *m* across 2022–2025 | same value repeated for every row of month *m* |
| `temperature_baseline_c` | mean(`temp_mean_c`) for month *m* across 2022–2025 | same value repeated for every row of month *m* |
| `soil_moisture_0_7cm_baseline` | mean(`soil_moisture_0_7cm`) for month *m* across 2022–2025 | same value repeated for every row of month *m* |
| `soil_moisture_7_28cm_baseline` | mean(`soil_moisture_7_28cm`) for month *m* across 2022–2025 | same value repeated for every row of month *m* |
| `ndvi_anomaly` | `NDVI_mean` − `ndvi_baseline` | negative = less green than normal |
| `ndwi_anomaly` | `NDWI_mean` − `ndwi_baseline` | negative = drier surface than normal |
| `ndvi_change_monthly` | `NDVI_mean`[m] − `NDVI_mean`[m−1] | blank for 2022-01 (no prior month; not invented) |
| `ndwi_change_monthly` | `NDWI_mean`[m] − `NDWI_mean`[m−1] | blank for 2022-01 |
| `rainfall_anomaly_mm` | `rainfall_total_mm` − `rainfall_baseline_mm` | negative = drier than the 2022–25 normal |
| `temperature_anomaly_c` | `temp_mean_c` − `temperature_baseline_c` | positive = warmer than normal |
| `soil_moisture_0_7cm_anomaly` | `soil_moisture_0_7cm` − baseline | negative = topsoil drier than normal |
| `soil_moisture_7_28cm_anomaly` | `soil_moisture_7_28cm` − baseline | negative = subsoil drier than normal |
| `soil_moisture_change` | `soil_moisture_0_7cm`[m] − [m−1] | topsoil layer (fastest stress response); blank for 2022-01 |

The following columns are carried through unchanged from the clean dataset:
`landcover_total_km2`, `coverage_quality`, `data_quality_flag`, `year_to_date`.
Land-cover area is used **only** for the coverage-quality flag, never as a
crop-health measurement.

## 3. Output statistics

- **Coverage quality:** 45 good, 5 moderate, 6 poor.
  - Poor months: 2022-07 (46.6% of Punjab area classified), 2022-08 (79.4%),
    2023-07 (94.5%), 2024-01 (49.0%), 2024-08 (68.7%), 2025-07 (79.1%)
  - Moderate months: 2022-01 (95.7%), 2024-07 (94.9%), 2025-08 (92.5%),
    2026-03 (95.6%), 2026-08 (98.0%)
- **Suspicious rows:** 1 (2026-08, `suspicious_rainfall`; anomaly −116.3 mm vs
  baseline, preserved as exported).
- **Blank cells:** only the three month-change columns for 2022-01.

## 4. January–August year-over-year comparison (like-for-like window)

| Year | Rainfall (mm) | NDVI mean | Temp mean (C) | Soil 0-7 cm | Soil 7-28 cm |
|---|---|---|---|---|---|
| 2022 | 157.2 | 0.354 | 27.10 | 0.137 | 0.156 |
| 2023 | 357.7 | 0.372 | 26.65 | 0.161 | 0.186 |
| 2024 | 419.4 | 0.311 | 25.85 | 0.149 | 0.166 |
| 2025 | 412.5 | 0.316 | 26.81 | 0.139 | 0.159 |
| 2026 | 275.3 | 0.329 | 26.70 | 0.139 | 0.156 |

Jan-Aug 2026 rainfall is **34% below** the 2022–2025 average and the lowest in
the five-year window, yet NDVI is near the middle of the range. Punjab's heavy
canal and groundwater irrigation plausibly decouples vegetation greenness from
rainfall at province scale; rainfall deficit alone should not be read as crop
failure. This is an interpretation, clearly labeled as such, not a confirmed
finding.

## 5. Changes from the 2024–2025 feature file

| Aspect | Previous (`Punjab_Monthly_Features.csv`) | This file (`Punjab_Monthly_Features_2022_2026.csv`) |
|---|---|---|
| Input rows | 32 | 56 |
| Baseline years | 2024, 2025 | 2022, 2023, 2024, 2025 |
| Baseline observations per month | 2 | 4 |
| New anomaly columns | rainfall, temperature only | NDVI, NDWI, rainfall, temperature, soil moisture (both layers) |
| Baseline columns | not explicit | explicit baseline columns for every indicator |
| Coverage-quality poor months | 3 | 6 |
| 2026-08 handling | unchanged | unchanged (rainfall preserved, flagged suspicious) |

## 6. Limitations

1. **Four-year baselines are short.** They are better than the two-year
   baseline used previously, but still sensitive to inter-annual variability;
   they should be treated as a working climatology, not a true 30-year normal.
2. **Monthly change features are seasonal.** NDVI, NDWI, and soil moisture fall
   every April-May (between-crops period); raw change columns describe the
   seasonal cycle. The risk score compares changes against the *expected*
   seasonal change to avoid false stress flags (see
   `risk_methodology_2022_2026.md`).
3. **Province-level means.** Every value is a Punjab-wide average; district or
   farm-level variation is invisible.
4. **2026-08 rainfall is unverified** and excluded from risk scoring.
5. **NDWI definition.** Monthly NDWI is negative year-round (different variant
   than the retired annual export); monthly values are only compared against
   monthly baselines.
6. **Poor land-cover coverage months** (section 3) should be normalized or
   excluded in any analysis that uses land-cover class areas.

## 7. Reproduction

```
cd D:\KisaanDost_Data
python scripts/create_historical_features.py
```

Requires `processed/Punjab_Monthly_Clean_2022_2026.csv` (from
`scripts/create_historical_monthly_clean.py`) and matplotlib for the chart. The
script is deterministic and re-runnable.
