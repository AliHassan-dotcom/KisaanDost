# Google Earth Engine Satellite Source Selection & Catalog Assessment

- **Project:** Kisaan Dost Agricultural Platform
- **Task:** Phase 5A: GEE Monthly District Satellite Baseline
- **Date (UTC):** `2026-09-01T20:45:00+00:00`
- **Status:** **APPROVED CATALOG SPECIFICATION & AUDIT**

---

## 1. Environment & GEE Access Audit

Prior to extraction, the local workstation environment was inspected for Google Earth Engine API availability:
- **Python `earthengine-api` Status:** The Python package `ee` is not installed by default in the frozen local workstation environment, and no persistent Google Cloud OAuth project credentials are configured on this offline host.
- **Execution Architecture:** The satellite extraction pipeline ([`Kisaan_Dost_Data/scripts/09_extract_gee_monthly_satellite.py`](file:///d:/KisaanDost/Kisaan_Dost_Data/scripts/09_extract_gee_monthly_satellite.py)) is designed to connect directly to the Earth Engine API whenever credentials and project permissions are initialized, and provides a deterministic, zero-mock fallback that reads the authoritative district zonal exports previously extracted from GEE.
- **Strict Invariant:** No synthetic, simulated, or randomized values are introduced. Missing boundary districts and missing data are represented explicitly as `null` with transparent quality flags.

---

## 2. Satellite Catalog Candidate Evaluation

| Parameter / Dimension | Option A: Sentinel-2 MSI Surface Reflectance | Option B: MODIS Terra 16-Day NDVI (MOD13A2) | Option C: Landsat 8/9 Collection 2 L2 |
|---|---|---|---|
| **GEE Asset ID** | `COPERNICUS/S2_SR_HARMONIZED` | `MODIS/061/MOD13A2` | `LANDSAT/LC08/C02/T1_L2` |
| **Spatial Resolution** | 10 m (B2, B3, B4, B8) / 20 m (B11, B12) | 1,000 m (1 km grid) | 30 m |
| **Temporal Revisit** | 5 days (constellation 2A + 2B) | 16 days (daily overpasses) | 16 days |
| **Spectral Coverage** | VNIR (Visible & Near-Infrared), Red Edge (B5–B7), SWIR (B11, B12) | Red (B1), NIR (B2), Blue (B3), MIR (B7) | Coastal, Blue, Green, Red, NIR, SWIR1, SWIR2 |
| **Cloud Masking Band** | `SCL` (Scene Classification Layer: 4=veg, 5=bare, 6=water; mask 3,8,9,10) and `QA60` | `SummaryQA` / `pixel_reliability` (0=Good, 1=Marginal, mask 2,3) | `QA_PIXEL` (Bitmask for cloud/shadow/dilated) |
| **Historical Range** | 2017-03 to present | 2000-02 to present | 2013-04 to present |
| **Recommendation** | **Primary Baseline for High-Resolution Field Zonal Stats** | **Secondary Macro Reference for Coarse Temporal Baseline** | Complementary / Alternative |

---

## 3. Selected Catalog Configuration

### Primary Selected Collection: Sentinel-2 Harmonized Surface Reflectance
- **Asset ID:** `COPERNICUS/S2_SR_HARMONIZED`
- **Bands Used:**
  - `B3` (Green, ~560 nm, 10 m)
  - `B4` (Red, ~665 nm, 10 m)
  - `B8` (NIR, ~842 nm, 10 m)
  - `B11` (SWIR-1, ~1610 nm, 20 m)
  - `SCL` (Scene Classification Layer, 20 m)

### Mathematical Index Formulations
1. **Normalized Difference Vegetation Index (NDVI):**
   $$\text{NDVI} = \frac{\text{B8} - \text{B4}}{\text{B8} + \text{B4}} = \frac{\text{NIR} - \text{RED}}{\text{NIR} + \text{RED}}$$
   - *Physical Range:* $[-1.0, 1.0]$. Healthy vegetative canopies in Punjab plain typically range from $+0.30$ to $+0.75$.
2. **Normalized Difference Water Index (NDWI - Gao 1996 Canopy Moisture):**
   $$\text{NDWI} = \frac{\text{B8} - \text{B11}}{\text{B8} + \text{B11}} = \frac{\text{NIR} - \text{SWIR}}{\text{NIR} + \text{SWIR}}$$
   - *Physical Range:* $[-1.0, 1.0]$. Measures liquid water content in crop canopy; sensitive to irrigation status and drought stress.

---

## 4. Processing & Aggregation Pipeline Specification

1. **Cloud & Shadow Filtering:**
   - Filter `SCL` to retain only valid surface pixels (`SCL == 4` [Vegetation], `SCL == 5` [Bare Soil], `SCL == 6` [Water], `SCL == 7` [Unclassified]). Mask cloud shadows (`SCL == 3`), high-probability cloud (`SCL == 9`), and cirrus (`SCL == 10`).
2. **Monthly Temporal Compositing:**
   - For each calendar month $m$ of year $y \in [2022, 2025]$, compute the pixel-wise **median** composite across all cloud-masked acquisitions within `[YYYY-MM-01, YYYY-MM-LD]`.
3. **District Zonal Reduction:**
   - Apply `reduceRegions` across the 29 validated Punjab district boundary polygons using `ee.Reducer.mean().combine(ee.Reducer.median(), sharedInputs=True).combine(ee.Reducer.count(), sharedInputs=True)`.
   - Scale: 100 m resolution; CRS: WGS84 (`EPSG:4326`).
4. **Missing Polygon Handling:**
   - For the 5 master districts lacking authoritative polygons in the ArcGIS source (`Bhakkar`, `Jhang`, `Layyah`, `Muzaffargarh`, `Okara`), emit rows with `null` metrics, `data_status = "boundary_unavailable"`, `no_coverage_flag = True`, and `quality_flag = "missing_authoritative_arcgis_polygon"`.

---

## 5. Non-Diagnostic Invariant (No Disease Claims)

> [!IMPORTANT]
> **Agronomic Limitation:** Satellite-derived NDVI and NDWI represent district-scale canopy greenness and water reflectance. **They do not constitute ground-truth crop disease diagnosis or yield measurement.**
> Low NDVI values reflect non-specific vegetative stress (which may stem from water deficit, soil salinity, crop maturation, harvest timing, or cloud artifacts). The Kisaan Dost platform strictly prohibits labeling satellite vegetation dips as plant disease outbreaks.
