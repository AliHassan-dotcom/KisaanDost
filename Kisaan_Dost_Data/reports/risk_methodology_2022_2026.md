# Risk Methodology — Punjab-wide Crop-Stress Risk Score (2022–2026)

- **Generated:** 2026-08-29
- **Output:** `processed/Punjab_Monthly_Risk_Score_2022_2026.csv` (56 rows x 45 columns)
- **Script:** `scripts/create_historical_risk_score.py`
- **Chart:** `reports/risk_trends_2022_2026.png`

## 1. What this score is — and is not

This is a **transparent, rule-based, Punjab-wide crop-stress risk indicator**
built from monthly satellite and reanalysis aggregates. It is:

- NOT a machine-learning model (no training, no learned parameters);
- NOT a disease-detection or disease-prediction model;
- NOT district- or farm-specific (province-level monthly means only);
- Indicative only: it summarizes how far key crop-stress variables sit from
their 2022–2025 seasonal norm.

## 2. Baselines and expected seasonal changes

Month-of-year means over the four complete years 2022–2025, computed from the
monthly data only. 2026 never contributes to its own baseline, and the old
annual NDWI values are never used.

Expected month-over-month change for month *m*:

```
E[m] = baseline[m] - baseline[m-1]   (December wraps to January)
```

Example expected changes (NDVI):

| Month | Expected NDVI change | Expected NDWI change | Expected soil 0-7 cm change |
|---|---|---|---|
| 1 | +0.037872 | -0.012920 | +0.026509 |
| 4 | -0.156023 | +0.102870 | -0.021577 |
| 7 | +0.056655 | -0.012489 | +0.091563 |
| 8 | +0.083893 | -0.060480 | +0.012024 |

## 3. Components, weights, and severity formulas

Every component severity is clamped to [0, 1]. "Decline" terms compare the
actual month-over-month change against the expected seasonal change, so normal
seasonal dips (e.g., the April-May fallow NDVI drop) do not trigger stress.

| Component | Weight | Severity = 1 (full stress) when | Formula |
|---|---|---|---|
| NDVI stress | 0.25 | NDVI <= 80% of baseline, or decline 0.10 worse than the seasonal norm | max( (1 - NDVI/b)/0.20, (E - actual change)/0.10 ) |
| NDWI stress | 0.15 | NDWI >= 0.10 below baseline (more negative), or decline 0.08 worse than the seasonal norm | max( (b - NDWI)/0.10, (E - actual change)/0.08 ) |
| Soil moisture | 0.25 | either layer >= 0.05 m3/m3 below baseline | max over both layers of (b - value)/0.05 |
| Rainfall | 0.20 | monthly total <= 40% of normal | (1 - rain/b)/0.60 |
| Temperature | 0.15 | monthly mean >= +3 C above baseline | (temp - b)/3.0 |

**Weight rationale:** NDVI and soil moisture are the most direct crop-stress
signals (0.25 each). Rainfall is a key driver but already feeds through soil
moisture and NDVI (0.20). NDWI is noisy at monthly province scale and its
variant differs from the retired annual export (0.15). Monthly-mean temperature
acts as an amplifier rather than a direct signal (0.15).

For 2022-01 the change-based sub-terms are skipped (no prior month in the
series); only the below-baseline terms apply.

## 4. Aggregation and labels

```
risk_score = 0.25*s_ndvi + 0.15*s_ndwi + 0.25*s_soil + 0.20*s_rain + 0.15*s_temp
             (clamped to [0, 1], rounded to 2 decimals)
```

| Score | Level |
|---|---|
| 0.00-0.33 | Low |
| 0.34-0.66 | Medium |
| 0.67-1.00 | High |

Classification uses the rounded score. `main_risk_reason` is the sub-reason of
the highest weighted contribution ("no stress signals above baseline" when all
components are zero).

## 5. Suspicious-rainfall handling (2026-08)

The exported 2026-08 rainfall of 0.0 mm in a monsoon month is almost certainly
an artifact. Per the approved rule:

- The value is **preserved exactly** (never filled, never corrected);
- `data_quality_flag = suspicious_rainfall`;
- The rainfall component is **excluded** from the score and the remaining
  weights are renormalized (sum / 0.80), so the month is scored only on
  NDVI, NDWI, soil moisture, and temperature;
- `main_risk_reason` carries the suffix "; rainfall component excluded
  (suspicious zero value)";
- `recommended_action` = "verify rainfall source before using this month for
  drought conclusions".

## 6. Recommended-action mapping

Rule-based lookup by risk level and dominant driver (no disease language):

| Level | Dominant driver | Action |
|---|---|---|
| Low | any | No immediate action; conditions near seasonal normal - continue routine monitoring. |
| Medium | NDVI | Monitor crop vigor; inspect fields for stress symptoms. |
| Medium | NDWI | Monitor surface-water availability; check irrigation supplies. |
| Medium | soil | Check soil moisture in the field; plan irrigation and conserve water. |
| Medium | rainfall | Monitor water reserves; schedule supplemental irrigation if dryness persists. |
| Medium | temperature | Watch for heat stress; adjust irrigation timing to cooler hours. |
| High | NDVI | Alert: vegetation-stress indicators high - assess crop condition in the field. |
| High | NDWI / soil / rainfall | Alert: drought-stress indicators high - issue farmer advisory; prioritize irrigation and water conservation. |
| High | temperature | Alert: heat-stress indicators high - issue heat advisory; protect crops and livestock. |
| any | suspicious rainfall | verify rainfall source before using this month for drought conclusions |

## 7. Results

| Level | Count |
|---|---|
| Low | 42 |
| Medium | 14 |
| High | 0 |

Medium months:

| Month | Score | Main risk reason |
|---|---|---|
| 2022-04 | 0.57 | rainfall 45% of normal |
| 2022-05 | 0.44 | rainfall 31% of normal |
| 2023-02 | 0.36 | rainfall 53% of normal |
| 2023-08 | 0.58 | soil moisture below baseline (0-7 cm, 0.153 vs 0.227 m3/m3) |
| 2023-09 | 0.34 | soil moisture below baseline (7-28 cm, 0.156 vs 0.207 m3/m3) |
| 2024-01 | 0.61 | NDVI below baseline (78% of normal) |
| 2024-06 | 0.37 | rainfall 54% of normal |
| 2024-07 | 0.49 | soil moisture below baseline (0-7 cm, 0.150 vs 0.215 m3/m3) |
| 2024-11 | 0.39 | rainfall 21% of normal |
| 2025-01 | 0.46 | rainfall 33% of normal |
| 2025-04 | 0.41 | rainfall 55% of normal |
| 2026-02 | 0.47 | rainfall 38% of normal |
| 2026-07 | 0.49 | soil moisture below baseline (0-7 cm, 0.148 vs 0.215 m3/m3) |
| 2026-08 | 0.45 | soil moisture below baseline (0-7 cm, 0.169 vs 0.227 m3/m3); rainfall component excluded (suspicious zero value) |

The consecutive Jul-2026 / Aug-2026 Medium ratings (both soil-moisture driven)
suggest an emerging mid-2026 dry signal, but August cannot be confirmed until
its rainfall is verified. No month reaches High: with four-year baselines and
heavily irrigated Punjab agriculture, High requires several simultaneous severe
deviations, which did not occur in this window.

## 8. Changes from the 2024–2025 risk score

| Aspect | Previous (`Punjab_Monthly_Risk_Score.csv`) | This file (`Punjab_Monthly_Risk_Score_2022_2026.csv`) |
|---|---|---|
| Input rows | 32 | 56 |
| Baseline years | 2024, 2025 | 2022, 2023, 2024, 2025 |
| Baseline observations per month | 2 | 4 |
| Expected seasonal change | from 2024-2025 | from 2022-2025 |
| Weights and thresholds | unchanged | unchanged |
| 2026-08 handling | unchanged | unchanged |
| Medium months | 5 | 14 |

The increase in Medium months is expected: the longer history includes the dry
pre-monsoon periods of 2022 and 2023 that were absent from the 2024-2026 file.

## 9. Limitations

1. **Four-year baselines are short.** They are better than the two-year baseline
   used previously, but still sensitive to inter-annual variability; they should
   be treated as a working climatology, not a true 30-year normal.
2. **Province-level monthly means** smooth away district-level droughts or
   floods; a district in crisis may not move the provincial average.
3. **Irrigation decouples vegetation from rainfall** in Punjab — low rainfall
   with normal NDVI is common (Jan-Aug 2026: rainfall -34% vs 2022-2025, NDVI
   near the middle of the range).
4. **Land-cover areas are never used as crop-health signals**, only for the
   `coverage_quality` flag (mosaic gaps in 6 months).
5. **2026 is partial** (Jan-Aug); annual statements about 2026 are impossible
   until the year completes, and 2026-08 rainfall is unverified.

## 10. Reproduction

```
cd D:\KisaanDost_Data
python scripts/create_historical_features.py   # run first
python scripts/create_historical_risk_score.py
```

Deterministic and re-runnable; requires matplotlib for the chart. All weights
and thresholds are constants at the top of `scripts/create_historical_risk_score.py`.
