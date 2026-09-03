# Satellite API, Flutter Charts & Explainable Attention Integration Report

- **Project:** Kisaan Dost Agricultural Platform
- **Task:** Phase 5B: Real Satellite API, Flutter Charts, and Explainable Attention Status
- **Timestamp (UTC):** `2026-09-01T21:30:00+00:00`
- **Status:** **COMPLETE / FULLY VERIFIED**

---

## 1. Executive Summary

Phase 5B successfully connects the verified 34-district monthly Sentinel-2 satellite baseline (`district_monthly_satellite_v1.csv`, 2022–2025) to the **FastAPI backend** and the **Flutter mobile application**. 

All placeholder mock data paths were replaced with source-traceable historical satellite data when `USE_MOCKS=false`, while preserving the offline mock repository when `USE_MOCKS=true`. An explainable, strictly non-diagnostic attention engine was integrated across the backend and mobile UI without creating ML disease claims or ungrounded yield predictions.

---

## 2. Part A — Formula & Spectral Index Integrity Verification

The satellite index mathematical formulations and catalog mappings were cross-checked:
- **NDVI:** $\text{NDVI} = \frac{\text{B8} - \text{B4}}{\text{B8} + \text{B4}}$ (Sentinel-2 NIR band 8, Red band 4, 10m).
- **NDWI:** $\text{NDWI} = \frac{\text{B8} - \text{B11}}{\text{B8} + \text{B11}}$ (Gao 1996 Canopy Moisture: NIR band 8, SWIR band 11, 20m).
- **Synthetic Controlled Matrix:** Verified in automated unit tests (`tests/test_satellite_api.py::test_formula_synthetic_band_integrity`).
- **Detailed Audit Report:** Documented in [`reports/satellite_formula_integrity_check.md`](file:///d:/KisaanDost/reports/satellite_formula_integrity_check.md).

---

## 3. Part B — FastAPI Satellite Service & Endpoints

A read-only service ([`app/backend/services/satellite_service.py`](file:///d:/KisaanDost/app/backend/services/satellite_service.py)) and router ([`app/backend/routers/satellite.py`](file:///d:/KisaanDost/app/backend/routers/satellite.py)) were implemented with JWT authentication and strict input validation:

| Endpoint | Method | Description | Response Model |
|---|---|---|---|
| `/api/v1/satellite/districts` | `GET` | Returns 34 master districts and boundary availability | `SatelliteDistrictsResponse` |
| `/api/v1/satellite/latest` | `GET` | Latest historical observation and attention status | `SatelliteRecord` |
| `/api/v1/satellite/history` | `GET` | Monthly time series with optional `start` & `end` filters | `SatelliteHistoryResponse` |
| `/api/v1/satellite/coverage` | `GET` | District geospatial boundary and month coverage | `SatelliteCoverageResponse` |
| `/api/v1/dashboard` | `GET` | Consolidated farmer dashboard (historical satellite card) | `DashboardResponse` |

### Security & Invariant Rules Enforced
1. **JWT Authentication:** All satellite endpoints enforce authentication via `get_current_user`.
2. **Zero Null Coercion:** Missing boundary records and cloud-masked months remain exact `null` (never coerced to `0.0`).
3. **No Filesystem Leakage:** Local file paths (e.g. `D:\`, `.csv`) are strictly stripped from all API outputs.
4. **District Defaulting:** Defaults to the authenticated farmer's profile district when query parameters are omitted.

---

## 4. Part C — Explainable Non-Diagnostic Attention Engine

An explainable attention classifier was integrated into the service:

| Attention Status | Criteria / Trigger | Agronomic Semantics |
|---|---|---|
| `normal_observation` | Month-over-month $\Delta \text{NDVI} \ge -0.15$ and $\Delta \text{NDWI} \ge -0.15$ | Canopy greenness and moisture within seasonal expectations. |
| `vegetation_attention` | Month-over-month $\Delta \text{NDVI} < -0.15$ | Relative drop in canopy photosynthetic biomass. Non-diagnostic. |
| `water_attention` | Month-over-month $\Delta \text{NDWI} < -0.15$ | Relative drop in canopy liquid water content. Non-diagnostic. |
| `insufficient_satellite_data` | `quality_flag == "cloud_masked_no_valid_pixels"` | 100% optical cloud/fog masking in acquisition period. |
| `boundary_unavailable` | District in unmapped list (`Bhakkar`, `Jhang`, `Layyah`, `Muzaffargarh`, `Okara`) | Provincial GIS boundary polygon unavailable; metrics withheld. |

> [!IMPORTANT]
> **Safety Invariant:** The attention engine never uses clinical disease, pest, pesticide, or yield estimation terms. It reports only observational vegetative canopy changes and explicit physical evidence strings.

---

## 5. Part D — Flutter Mobile App Integration

1. **Repositories & Models:**
   - [`mobile_app/lib/models/satellite_summary.dart`](file:///d:/KisaanDost/mobile_app/lib/models/satellite_summary.dart)
   - [`mobile_app/lib/models/satellite_record.dart`](file:///d:/KisaanDost/mobile_app/lib/models/satellite_record.dart)
   - [`mobile_app/lib/models/satellite_coverage.dart`](file:///d:/KisaanDost/mobile_app/lib/models/satellite_coverage.dart)
   - [`mobile_app/lib/repositories/satellite_repository_impl.dart`](file:///d:/KisaanDost/mobile_app/lib/repositories/satellite_repository_impl.dart) (live API client)
   - [`mobile_app/lib/repositories/mock/mock_satellite_repository.dart`](file:///d:/KisaanDost/mobile_app/lib/repositories/mock/mock_satellite_repository.dart) (offline fallback)
2. **Interactive UI Screens & Widgets:**
   - [`mobile_app/lib/screens/satellite_screen.dart`](file:///d:/KisaanDost/mobile_app/lib/screens/satellite_screen.dart): Interactive 34-district selector, status badges, attention card with color-coded alerts, metric cards (NDVI/NDWI mean and median), boundary unavailable warnings, and localized English/Urdu strings.
   - [`mobile_app/lib/widgets/satellite_trend_chart.dart`](file:///d:/KisaanDost/mobile_app/lib/widgets/satellite_trend_chart.dart): Pure Flutter `CustomPaint` / `Canvas` time-series sparkline plotting NDVI (green) and NDWI (blue) across 2022–2025.
   - [`mobile_app/lib/widgets/satellite_card.dart`](file:///d:/KisaanDost/mobile_app/lib/widgets/satellite_card.dart): Dashboard card displaying "Historical Satellite", last available period ("2025-12"), and non-diagnostic trend.

---

## 6. Verification & Test Summary

| Test Suite | Scope / Command | Status |
|---|---|---|
| **Backend Satellite Tests** | `pytest tests/test_satellite_api.py -v` | **12 / 12 PASS** |
| **All Backend Root Tests** | `pytest tests -q -rs --tb=short` | **61 / 61 PASS** |
| **GEE Satellite Tests** | `pytest Kisaan_Dost_Data/tests/test_gee_monthly_satellite.py -v` | **8 / 8 PASS** |
| **Data Pipeline Tests** | `pytest Kisaan_Dost_Data/tests -q -rs --tb=short` | **384 / 384 PASS** |
| **Flutter Unit & Widget Tests** | `flutter test` | **56 / 56 PASS** |
| **Flutter Static Analysis** | `flutter analyze` | **0 issues found (CLEAN)** |
| **Handoff Completeness Check** | `python scripts/check_handoff_completeness.py` | **COMPLETE (0 Active Blockers)** |
