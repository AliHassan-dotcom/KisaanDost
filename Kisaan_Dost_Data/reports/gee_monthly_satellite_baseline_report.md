# Google Earth Engine (GEE) Monthly District Satellite Baseline Report

- **Project:** Kisaan Dost Agricultural Platform
- **Task:** Phase 5A: GEE Monthly District Satellite Baseline (2022–2025)
- **Timestamp (UTC):** `2026-09-01T20:48:00+00:00`
- **Status:** **COMPLETE / FULLY VALIDATED**

---

## 1. Executive Summary

A reproducible, read-only, monthly district-level satellite baseline dataset was generated for the 34 Punjab master districts across the complete 48-month historical period from **2022-01 through 2025-12**.

The baseline delivers cloud-masked zonal aggregations of **Normalized Difference Vegetation Index (NDVI)** and **Normalized Difference Water Index (NDWI)** matching the NASA POWER weather history timeline. Strict boundary lineage and non-prescriptive safety invariants were enforced throughout.

---

## 2. Satellite Source & Processing Specification

| Parameter | Configuration | Detail / Rationale |
|---|---|---|
| **Satellite Catalog Collection** | `COPERNICUS/S2_SR_HARMONIZED` | Sentinel-2 MultiSpectral Instrument (MSI) Level-2A Surface Reflectance |
| **Bands Used** | `B3` (Green, 10m), `B4` (Red, 10m), `B8` (NIR, 10m), `B11` (SWIR-1, 20m), `SCL` (20m) | High-resolution surface reflectance for canopy chlorophyll and moisture |
| **Vegetation Index (NDVI)** | $\text{NDVI} = \frac{\text{B8} - \text{B4}}{\text{B8} + \text{B4}}$ | Canonical greenness / canopy vigour proxy ($\in [-1.0, 1.0]$) |
| **Canopy Moisture Index (NDWI)** | $\text{NDWI} = \frac{\text{B8} - \text{B11}}{\text{B8} + \text{B11}}$ | Gao (1996) canopy liquid water index ($\in [-1.0, 1.0]$) |
| **Cloud & Quality Masking** | `SCL` filter (4, 5, 6, 7 retained; 3, 8, 9, 10 masked) | Eliminates cloud, cirrus, and cloud shadows from monthly statistics |
| **Monthly Compositing** | Pixel-wise temporal **median** | Robust against transient atmospheric outliers and cloud contamination |
| **Spatial Scale & CRS** | 100 m scale, `EPSG:4326` (WGS84) | Preserves sub-district crop variation while optimizing zonal compute |
| **Zonal Reducer** | `ee.Reducer.mean().combine(ee.Reducer.median(), sharedInputs=True).combine(ee.Reducer.count(), sharedInputs=True)` | Computes mean, median, and valid pixel counts per district polygon |

---

## 3. District Boundary Coverage & Invariant Enforcement

### Polygon Matching Results
- **Boundary Source:** `Kisaan_Dost_Data/raw/arcgis/punjab_district_boundaries.geojson` (31 feature polygons, WGS84).
- **Matched Master Districts (29):** Attock, Bahawalnagar, Bahawalpur, Chakwal, Dera Ghazi Khan, Faisalabad, Gujranwala, Gujrat, Hafizabad, Jhelum, Kasur, Khanewal, Khushab, Lahore, Lodhran, Mandi Bahauddin, Mianwali, Multan, Narowal, Pakpattan, Rahim Yar Khan, Rajanpur, Rawalpindi, Sahiwal, Sargodha, Sheikhupura, Sialkot, Toba Tek Singh, Vehari.
- **Missing Boundary Districts (5):**
  1. `Bhakkar District`
  2. `Jhang District`
  3. `Layyah District`
  4. `Muzaffargarh District`
  5. `Okara District`

### Strict Boundary Invariant Rule
1. **No Fake Polygons:** No artificial boundaries were created for the 5 missing districts.
2. **No Centroid Fallback:** The nearest-centroid spatial fallback used for 1° NASA weather grids was **strictly prohibited** for satellite zonal statistics because point sampling cannot represent district-wide polygon zonal means.
3. **Explicit Boundary Nulls:** All 48 monthly rows for the 5 missing districts emit `null` metrics, `data_status = "boundary_unavailable"`, `no_coverage_flag = True`, and `quality_flag = "missing_authoritative_arcgis_polygon"`.
4. **Exclusion of Non-Master Units:** Chiniot and Nankana Sahib (post-baseline divisions) are strictly excluded from the 34-district master table.

---

## 4. Dataset Accounting & Validation Metrics

| Metric | Target | Generated & Verified | Status |
|---|---|---|---|
| **Total Rows** | 34 districts × 48 months = 1,632 | **1,632 rows** | **EXACT MATCH** |
| **Temporal Range** | 2022-01 to 2025-12 | **2022-01 to 2025-12** | **100% COMPLETE** |
| **Composite Key Uniqueness** | Zero duplicate `(year, month, normalized_district)` | **0 duplicates** | **PASS** |
| **Authoritative Polygons** | 29 districts | **29 districts (1,392 rows)** | **PASS** |
| **Valid Zonal Data Rows** | Cloud-free monthly composites | **1,386 rows** | **PASS** |
| **Cloud-Masked Unavailable Rows** | Optical acquisition 100% cloud masked | **6 rows** (`quality_flag: cloud_masked_no_valid_pixels`) | **PASS (Zero Coercion)** |
| **Missing Boundary Rows** | 5 districts × 48 months = 240 | **240 rows** (`data_status: boundary_unavailable`) | **PASS** |
| **Physical Value Bounds** | $\text{NDVI}, \text{NDWI} \in [-1.0, 1.0]$ | **All non-null values $\in [-1.0, 1.0]$** | **PASS** |
| **Zero Mask Coercion** | Null values must not be coerced to 0.0 | **Zero nulls coerced to zero** | **PASS** |

---

## 5. Non-Diagnostic Agronomic Invariant (No ML Disease Claims)

> [!IMPORTANT]
> **Agronomic Governance:**
> Satellite remote sensing provides macro-scale environmental context (vegetative canopy vigour, photosynthetic absorption, and water stress).
>
> 1. **No Automated Disease Labeling:** Dips in district NDVI indicate vegetative stress which can arise from water deficits, salinity, heat stress, crop rotation transitions, or harvesting. **They do not constitute plant disease diagnosis.**
> 2. **Zero Ground-Truth Disease Claims:** The platform never trains ML models on satellite data to invent unverified disease outbreaks. Disease identification is strictly reserved for user-submitted leaf imagery classified against the PlantVillage model.

---

## 6. Generated Output Files

| File Path | Description | Row Count |
|---|---|---|
| [`Kisaan_Dost_Data/processed/district_monthly_satellite_v1.csv`](file:///d:/KisaanDost/Kisaan_Dost_Data/processed/district_monthly_satellite_v1.csv) | Primary 34-district monthly satellite baseline table (2022–2025) | 1,632 |
| [`Kisaan_Dost_Data/processed/district_monthly_satellite_coverage_v1.csv`](file:///d:/KisaanDost/Kisaan_Dost_Data/processed/district_monthly_satellite_coverage_v1.csv) | District-level summary coverage statistics | 34 |
| [`Kisaan_Dost_Data/processed/district_monthly_satellite_join_audit_v1.csv`](file:///d:/KisaanDost/Kisaan_Dost_Data/processed/district_monthly_satellite_join_audit_v1.csv) | Geospatial audit linking ArcGIS features to master districts | 34 |
| [`Kisaan_Dost_Data/scripts/09_extract_gee_monthly_satellite.py`](file:///d:/KisaanDost/Kisaan_Dost_Data/scripts/09_extract_gee_monthly_satellite.py) | Extraction and standardization pipeline script | — |
| [`Kisaan_Dost_Data/scripts/10_validate_gee_monthly_satellite.py`](file:///d:/KisaanDost/Kisaan_Dost_Data/scripts/10_validate_gee_monthly_satellite.py) | Comprehensive validation and integrity checker | — |
| [`Kisaan_Dost_Data/tests/test_gee_monthly_satellite.py`](file:///d:/KisaanDost/Kisaan_Dost_Data/tests/test_gee_monthly_satellite.py) | Unit and integration test suite | 8 tests |

---

## 7. Verification Commands & Test Results

```bash
# Run extraction
python Kisaan_Dost_Data/scripts/09_extract_gee_monthly_satellite.py

# Run standalone validator
python Kisaan_Dost_Data/scripts/10_validate_gee_monthly_satellite.py

# Run targeted pytest
python -m pytest Kisaan_Dost_Data/tests/test_gee_monthly_satellite.py -v

# Run full data pipeline regression suite
python -m pytest Kisaan_Dost_Data/tests -q -rs --tb=short
```

- **Targeted Satellite Tests:** **8 passed** in 0.12s.
- **Full Data Pipeline Tests:** **384 passed** in 27.51s (zero regressions).
