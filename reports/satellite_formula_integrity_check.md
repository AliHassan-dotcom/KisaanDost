# Satellite Formula & Source Integrity Check Report

- **Project:** Kisaan Dost Agricultural Platform
- **Task:** Phase 5B Part A: Satellite Formula & Index Integrity Validation
- **Timestamp (UTC):** `2026-09-01T21:00:00+00:00`
- **Status:** **VERIFIED / PASS**

---

## 1. Mathematical Index Formulations

### Normalized Difference Vegetation Index (NDVI)
- **Spectral Bands:** Sentinel-2 MSI `B8` (Near-Infrared / NIR, center wavelength ~842 nm, 10m) and `B4` (Red, center wavelength ~665 nm, 10m).
- **Formula:**
  $$\text{NDVI} = \frac{\text{B8} - \text{B4}}{\text{B8} + \text{B4}} = \frac{\text{NIR} - \text{RED}}{\text{NIR} + \text{RED}}$$
- **Physical Bounds:** $[-1.0, 1.0]$.
- **Agronomic Semantics:** Quantifies active photosynthetic canopy biomass and chlorophyll absorption across Punjab crop zones.

### Normalized Difference Water Index (NDWI - Gao 1996)
- **Spectral Bands:** Sentinel-2 MSI `B8` (Near-Infrared / NIR, center wavelength ~842 nm, 10m) and `B11` (Shortwave-Infrared / SWIR-1, center wavelength ~1610 nm, 20m).
- **Formula:**
  $$\text{NDWI} = \frac{\text{B8} - \text{B11}}{\text{B8} + \text{B11}} = \frac{\text{NIR} - \text{SWIR}}{\text{NIR} + \text{SWIR}}$$
- **Physical Bounds:** $[-1.0, 1.0]$.
- **Agronomic Semantics:** Quantifies crop canopy liquid water content and vegetative hydration stress.

---

## 2. Synthetic Band Verification Matrix

The mathematical expressions were verified against synthetic controlled band values to ensure numerical stability and bound compliance:

| Case | NIR (B8) | Red (B4) | SWIR (B11) | Computed NDVI | Computed NDWI | Expected Physical Condition |
|---|---|---|---|---|---|---|
| **Dense Healthy Crop** | 0.80 | 0.10 | 0.20 | $+0.7778$ | $+0.6000$ | Vigorous green canopy, high hydration |
| **Moderate Crop** | 0.50 | 0.25 | 0.35 | $+0.3333$ | $+0.1765$ | Normal vegetative stage |
| **Water Stressed Crop** | 0.40 | 0.30 | 0.55 | $+0.1429$ | $-0.1579$ | Low chlorophyll, dry canopy |
| **Bare Soil / Fallow** | 0.20 | 0.20 | 0.25 | $0.0000$ | $-0.1111$ | Unplanted / dry field |
| **Open Water / Canal** | 0.05 | 0.10 | 0.02 | $-0.3333$ | $+0.4286$ | Water surface |

---

## 3. Script & Catalog Alignment Check

1. **Extraction Script:** [`Kisaan_Dost_Data/scripts/09_extract_gee_monthly_satellite.py`](file:///d:/KisaanDost/Kisaan_Dost_Data/scripts/09_extract_gee_monthly_satellite.py) maps to catalog asset `COPERNICUS/S2_SR_HARMONIZED`.
2. **Band Definitions:** Verified bands `B4` (Red), `B8` (NIR), and `B11` (SWIR) are designated consistently in `gee_source_selection.md` and `gee_monthly_satellite_baseline_report.md`.
3. **Data Integrity:** All 1,632 rows in [`Kisaan_Dost_Data/processed/district_monthly_satellite_v1.csv`](file:///d:/KisaanDost/Kisaan_Dost_Data/processed/district_monthly_satellite_v1.csv) maintain non-null values strictly within $[-1.0, 1.0]$, and preserve exact `null` representation for missing boundaries and cloud-masked periods.
