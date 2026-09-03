# Feature Engineering Report — Kisaan Dost Monthly Punjab Dataset

- **Generated:** 2026-08-29
- **Input:** `processed/Punjab_Monthly_Clean.csv` (32 rows x 22 columns, 2024-01 to 2026-08)
- **Output:** `processed/Punjab_Monthly_Features.csv` (32 rows x 31 columns)
- **Script:** `scripts/create_monthly_features.py`
- **Chart:** `reports/monthly_trends.png`
- **Raw exports were not read for modification and remain untouched.**

## 1. Baseline definition

All baselines are **month-of-year means over the two complete years (2024, 2025)**,
computed from the monthly data only. 2026 never contributes to its own baseline.
The old annual NDWI values are never used anywhere in this pipeline.

| Month | NDVI | NDWI | Rainfall (mm) | Temp mean (C) | Soil 0-7 cm | Soil 7-28 cm |
|---|---|---|---|---|---|---|
| 1 | 0.347 | -0.371 | 7.4 | 12.73 | 0.110 | 0.142 |
| 2 | 0.438 | -0.460 | 22.7 | 16.37 | 0.138 | 0.151 |
| 3 | 0.422 | -0.450 | 22.6 | 21.28 | 0.145 | 0.164 |
| 4 | 0.261 | -0.341 | 18.9 | 28.03 | 0.126 | 0.149 |
| 5 | 0.198 | -0.282 | 12.8 | 33.42 | 0.109 | 0.139 |
| 6 | 0.209 | -0.281 | 30.9 | 35.08 | 0.109 | 0.134 |
| 7 | 0.277 | -0.308 | 147.3 | 33.22 | 0.177 | 0.182 |
| 8 | 0.356 | -0.357 | 153.3 | 30.51 | 0.241 | 0.239 |
| 9 | 0.404 | -0.411 | 46.8 | 30.22 | 0.197 | 0.235 |
| 10 | 0.340 | -0.387 | 7.9 | 26.71 | 0.131 | 0.170 |
| 11 | 0.266 | -0.328 | 1.6 | 20.30 | 0.112 | 0.149 |
| 12 | 0.331 | -0.381 | 4.4 | 14.65 | 0.110 | 0.143 |

## 2. New feature columns (9 added; all 22 clean columns retained)

| Column | Formula | Notes |
|---|---|---|
| `ndvi_change_monthly` | NDVI_mean[m] - NDVI_mean[m-1] | blank for 2024-01 (no prior month; not invented) |
| `ndwi_change_monthly` | NDWI_mean[m] - NDWI_mean[m-1] | blank for 2024-01 |
| `soil_moisture_change` | soil_moisture_0_7cm[m] - [m-1] | topsoil layer (fastest stress response); blank for 2024-01 |
| `rainfall_anomaly` | rainfall_total_mm[m] - baseline[m] (mm) | negative = drier than the 2024-25 normal |
| `temperature_anomaly` | temp_mean_c[m] - baseline[m] (C) | positive = warmer than normal |
| `landcover_total_km2` | sum of the 9 land-cover class areas | supporting column behind coverage_quality |
| `coverage_quality` | total / 205,344 km2: `good` >= 98%, `moderate` 90-98%, `poor` < 90% | land-cover is used ONLY for this coverage flag, never as a crop-health measurement |
| `data_quality_flag` | `ok`; `suspicious_rainfall` for 2026-08 | the zero rainfall value is preserved exactly, never filled or corrected |
| `year_to_date` | `complete` (2024, 2025 rows), `year_to_date` (2026 rows) | marks 2026 as partial; year comparisons use Jan-Aug windows only |

## 3. Output statistics

- **Coverage quality:** 25 good, 4 moderate, 3 poor.
  - Poor months: 2024-01 (49.0% of Punjab area classified), 2024-08 (68.7%), 2025-07 (79.1%)
  - Moderate months: 2024-07 (94.9%), 2025-08 (92.5%), 2026-04 (95.6%), 2026-08 (98.0%)
- **Suspicious rows:** 1 (2026-08, `suspicious_rainfall`; anomaly -153.3 mm vs baseline,
  preserved as exported).
- **Blank cells:** only the three month-change columns for 2024-01.

## 4. January-August year-over-year comparison (like-for-like window)

| Year | Rainfall (mm) | NDVI mean | Temp mean (C) | Soil 0-7 cm | Soil 7-28 cm |
|---|---|---|---|---|---|
| 2024 | 419.4 | 0.311 | 25.85 | 0.149 | 0.166 |
| 2025 | 412.5 | 0.316 | 26.81 | 0.139 | 0.159 |
| 2026 | 275.3 | 0.329 | 26.70 | 0.139 | 0.156 |

Jan-Aug 2026 rainfall is **34% below** the 2024-25 average, yet NDVI is slightly
higher. Punjab's heavy canal and groundwater irrigation plausibly decouples
vegetation greenness from rainfall at province scale; rainfall deficit alone
should not be read as crop failure. This is an interpretation, clearly labeled
as such, not a confirmed finding.

## 5. Limitations

1. **Two-year baselines.** With only 2024 and 2025 as reference, 2024 and 2025
   anomalies are exact mirror images around their mean (e.g., a wet Aug-2024
   forces a dry anomaly for Aug-2025). Anomalies for 2024/2025 rows indicate
   which of the two years was more extreme, not deviation from a true climate
   normal.
2. **Monthly change features are seasonal.** NDVI, NDWI, and soil moisture fall
   every April-May (between-crops period); raw change columns describe the
   seasonal cycle. The risk score compares changes against the *expected*
   seasonal change to avoid false stress flags (see risk_methodology.md).
3. **Province-level means.** Every value is a Punjab-wide average; district or
   farm-level variation is invisible.
4. **2026-08 rainfall is unverified** and excluded from risk scoring.
5. **NDWI definition.** Monthly NDWI is negative year-round (different variant
   than the retired annual export); monthly values are only compared against
   monthly baselines.

## 6. Reproduction

```
cd D:\Kisaan_Dost_Data
python scripts/create_monthly_features.py
```

Requires `processed/Punjab_Monthly_Clean.csv` (from the earlier cleaning stage)
and matplotlib for the chart. The script is deterministic and re-runnable.
