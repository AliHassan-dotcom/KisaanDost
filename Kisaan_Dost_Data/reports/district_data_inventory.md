# District Data Inventory — Kisaan Dost

- **Generated:** 2026-08-30
- **Workspace:** `D:\Kisaan_Dost_Data\District data`
- **Purpose:** Inventory of all newly added district-level and context files for
  Punjab agricultural advisory analysis.

## 1. File summary

| Category | Count | File types |
|---|---|---|
| District-level remote-sensing CSVs | 30 | `.csv` |
| Annual district-level land-cover CSVs | 2 | `.csv` |
| District-wise crop statistic PDFs | 3 | `.pdf` |
| Province-level context images | 7 | `.jpeg` |
| **Total files** | **42** | |

## 2. District-level remote-sensing CSVs (mergeable)

All files share the same 34 districts and merge cleanly on `(year, month, district)`.
However, the **column schema changes between 2022-2024 and 2025-2026**.

### 2.1 Common structure

| Attribute | Value |
|---|---|
| Spatial level | District (34 Punjab districts) |
| Temporal frequency | Monthly for 2022-2025; Jan-Aug 2026 only |
| Common key columns | `year`, `month`, `district` |
| Dropped columns | `system:index`, `.geo` (empty MultiPoint geometry) |

### 2.2 File list

| Variable | 2022 | 2023 | 2024 | 2025 | 2026 | Notes |
|---|---|---|---|---|---|---|
| NDVI | 12 mo | 12 mo | 12 mo | 12 mo | 8 mo | single `NDVI_mean` |
| NDWI | 12 mo | 12 mo | 12 mo | 12 mo | 8 mo | single `NDWI_mean` |
| Rainfall | 12 mo | 12 mo | 12 mo | 12 mo | 8 mo | 2022-24: `rainfall_mean_mm_per_day` + `rainfall_total_mm`; 2025-26: single `Rainfall_mm` |
| SoilMoisture | 12 mo | 12 mo | 12 mo | 12 mo | 8 mo | 2022-24: `soil_moisture_0_7cm` + `soil_moisture_7_28cm`; 2025-26: single `SoilMoisture` |
| Temperature | 12 mo | 12 mo | 12 mo | 12 mo | 8 mo | 2022-24: `temp_max_c`, `temp_mean_c`, `temp_min_c`; 2025-26: single `Temperature_C` |
| LandCover | 12 mo | 12 mo | 12 mo | annual | annual | 2022-24 monthly class areas; 2025-26 annual `Cropland_Fraction` |

### 2.3 District list (34)

1. Attock District
2. Bahawalnagar District
3. Bahawalpur District
4. Bhakkar District
5. Chakwal District
6. Dera Ghazi Khan District
7. Faisalabad District
8. Gujranwala District
9. Gujrat District
10. Hafizabad District
11. Jhang District
12. Jhelum District
13. Kasur District
14. Khanewal District
15. Khushab District
16. Lahore District
17. Layyah District
18. Lodhran District
19. Mandi Bahauddin District
20. Mianwali District
21. Multan District
22. Muzaffargarh District
23. Narowal District
24. Okara District
25. Pakpattan District
26. Rahim Yar Khan District
27. Rajanpur District
28. Rawalpindi District
29. Sahiwal District
30. Sargodha District
31. Sheikhupura District
32. Sialkot District
33. Toba Tek Singh District
34. Vehari District

## 3. Annual district-level land-cover CSVs

| File | Rows | Columns | Notes |
|---|---|---|---|
| `LandCover_Districts_Punjab_2025.csv` | 34 | `system:index`, `Cropland_Fraction`, `district`, `year`, `.geo` | Annual cropland fraction per district |
| `LandCover_Districts_Punjab_2026.csv` | 34 | same as above | Annual cropland fraction per district |

These are merged into `district_master_clean.csv` as `landcover_cropland_fraction`
for all months of 2025 and 2026. They are **support variables only**, not crop-stress signals.

## 4. Context/reference assets (province-level, not merged)

These files provide Punjab-wide context. They are **not district-level** and are
kept as separate reference tables/assets.

| File / Folder | Type | Content | Usable as structured table? |
|---|---|---|---|
| `District Wise Crop data 2022-23_copy.pdf` | PDF | Final crop estimates by district for 2022-23 (area, production, yield for many crops) | Yes, but 206 pages; full extraction is a separate task |
| `District Wise Crop data 2023-24_copy.pdf` | PDF | Final crop estimates by district for 2023-24 | Yes, 207 pages |
| `Kharif Rabi Estimates in Punjab 2024-25_copy.pdf` | PDF | Final estimates for 2024-25 | Yes, 203 pages |
| `Land Utilization.jpeg` | Image | Province-wide land utilization pie chart (2023-24) | Values readable; extracted to context table |
| `Water Availability.jpeg` | Image | Province water availability 2004-2024 (Rabi/Kharif, surface/ground) | Values readable; extracted to context table |
| `Agriculture GDP/Agriculture GDP 1.jpeg` | Image | Agriculture GDP composition and growth rate 2005-24 | Values readable; extracted to context table |
| `Agriculture GDP/Agriculture GDP part 2.jpeg` | Image | Sector shares in GDP 2009-10 to 2023-24 | Values readable; extracted to context table |
| `Cropped Area Stats/Cropped Area Stats 1.jpeg` | Image | Kharif crop area distribution 2023-24 | Values readable; extracted to context table |
| `Cropped Area Stats/Cropped Area Stats part 2.jpeg` | Image | Total cropped area and Rabi crop area 2023-24 | Values readable; extracted to context table |
| `Export, Import & Trading/Export, Import & Trading.jpeg` | Image | Food group trade balance + major ag export commodities | Values readable; extracted to context table |
| `Export, Import & Trading/Export, Import & Trade part 2 .jpeg` | Image | Food group exports + agriculture credit disbursement | Values readable; extracted to context table |

## 5. Missing data sources

| Required source | Status | Impact |
|---|---|---|
| District boundary shapefiles / GeoJSON | **Missing** | Cannot map districts spatially; analysis is tabular only |
| Irrigation data (canal/d groundwater/tube wells) | **Missing** | Cannot separate rain-fed vs irrigated stress; NDVI-rainfall decoupling is hard to explain |
| Farm-level ground truth | **Missing** | Cannot validate remote-sensing signals at field scale |

## 6. Merge compatibility summary

| Dataset | Merge into district_master_clean.csv | Kept separate |
|---|---|---|
| NDVI monthly district | Yes | |
| NDWI monthly district | Yes | |
| Rainfall monthly district | Yes (with schema normalization) | |
| Soil moisture monthly district | Yes (with schema normalization) | |
| Temperature monthly district | Yes (with schema normalization) | |
| LandCover monthly district (2022-24) | Yes (`landcover_crops_km2`) | |
| LandCover annual district (2025-26) | Yes (`landcover_cropland_fraction`) | |
| Crop statistic PDFs | | Yes (district-level reference, extraction pending) |
| Land utilization image | | Yes (province-level context) |
| Water availability image | | Yes (province-level context) |
| Agriculture GDP images | | Yes (province-level context) |
| Cropped area stats images | | Yes (province-level context) |
| Trade balance images | | Yes (province-level context) |
