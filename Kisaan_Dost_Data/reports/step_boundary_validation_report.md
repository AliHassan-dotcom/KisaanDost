# Step 2 — Punjab Boundary Validation Report

- **Generated:** 2026-08-31
- **Source URL:** `https://services5.arcgis.com/sjP4Ugu5s0dZWLjd/arcgis/rest/services/Pakistan_Administrative_district_boundary_Punjab/FeatureServer/0/query?where=1%3D1&outFields=*&returnGeometry=true&f=geojson&outSR=4326&resultRecordCount=1000`
- **Saved file:** `raw/arcgis/punjab_district_boundaries.geojson` (2,121,419 bytes)
- **Layer name (from FeatureServer metadata):** `Punjab_District_Boundaries`
- **Authoritative feature count (returnCountOnly=true):** **31**
- **maxRecordCount (layer metadata):** 1,000 — not hit; no pagination needed.
- **Validator:** `scripts/validate_punjab_boundaries.py` — exit code 0
- **Tests:** `tests/test_validate_punjab_boundaries.py` — 13/13 pass

---

## 1. Source and fetch

A single GET to the FeatureServer's `/query` endpoint with
`where=1=1&outFields=*&returnGeometry=true&f=geojson&outSR=4326` returned the
full dataset in one response (no pagination). `User-Agent` was set to
`KisaanDost/1.0`. The payload is a valid GeoJSON FeatureCollection with
`crs.properties.name = "EPSG:4326"` (WGS84).

---

## 2. Schema validation

| Check | Result |
|---|---|
| Top-level `type == "FeatureCollection"` | pass |
| CRS is EPSG:4326 | pass |
| Every feature has non-empty `DISTRICT` property | pass (31/31) |
| Every geometry is Polygon or MultiPolygon | pass (31/31) |
| No duplicate district names | pass |
| All vertex coords within Punjab envelope (lon 68–77, lat 26–36) | pass |

Zero warnings, zero hard errors.

---

## 3. Feature inventory

31 features, all with `properties.PROVINCE = "Punjab"` and `properties.DISTRICT`
(single-word title-case, no " District" suffix). 30 Polygons + 1 MultiPolygon.

| # | District | Type | Vertices | Lon min | Lon max | Lat min | Lat max |
|---:|---|---|---:|---:|---:|---:|---:|
| 1 | Attock | Polygon | 2,568 | 71.705 | 72.924 | 33.000 | 34.006 |
| 2 | Bahawalnagar | Polygon | 1,520 | 72.287 | 73.972 | 28.854 | 30.377 |
| 3 | Bahawalpur | Polygon | 1,401 | 70.893 | 72.853 | 27.799 | 29.874 |
| 4 | Chakwal | Polygon | 2,456 | 71.803 | 73.246 | 32.543 | 33.215 |
| 5 | Chiniot | Polygon | 960 | 72.423 | 73.209 | 31.360 | 31.992 |
| 6 | Dera Ghazi Khan | Polygon | 2,178 | 69.915 | 70.909 | 29.570 | 31.339 |
| 7 | Faisalabad | Polygon | 1,766 | 72.669 | 73.670 | 30.693 | 31.790 |
| 8 | Gujranwala | Polygon | 1,141 | 73.679 | 74.568 | 31.814 | 32.549 |
| 9 | Gujrat | Polygon | 936 | 73.579 | 74.477 | 32.391 | 33.004 |
| 10 | Hafizabad | Polygon | 567 | 73.142 | 73.827 | 31.757 | 32.344 |
| 11 | Jhelum | Polygon | 2,393 | 72.604 | 73.799 | 32.424 | 33.249 |
| 12 | Kasur | Polygon | 1,762 | 73.634 | 74.703 | 30.627 | 31.341 |
| 13 | Khanewal | Polygon | 1,794 | 71.538 | 72.478 | 29.867 | 30.740 |
| 14 | Khushab | Polygon | 1,915 | 71.609 | 72.632 | 31.524 | 32.729 |
| 15 | Lahore | Polygon | 1,576 | 74.002 | 74.655 | 31.225 | 31.715 |
| 16 | Lodhran | Polygon | 1,371 | 71.335 | 72.144 | 29.352 | 29.943 |
| 17 | Mandi Bahauddin | Polygon | 1,221 | 73.046 | 73.883 | 32.121 | 32.742 |
| 18 | Mianwali | Polygon | 1,514 | 71.107 | 71.960 | 32.165 | 33.241 |
| 19 | Multan | Polygon | 1,676 | 71.022 | 71.839 | 29.378 | 30.449 |
| 20 | Nankana Sahib | Polygon | 1,658 | 73.341 | 74.034 | 31.018 | 31.586 |
| 21 | Narowal | Polygon | 1,120 | 74.595 | 75.381 | 31.922 | 32.497 |
| 22 | Pakpattan | Polygon | 3,050 | 72.811 | 73.622 | 29.997 | 30.654 |
| 23 | Rahim Yar Khan | MultiPolygon | 1,312 | 69.469 | 71.119 | 27.705 | 29.230 |
| 24 | Rajanpur | Polygon | 1,453 | 69.321 | 70.728 | 28.407 | 29.949 |
| 25 | Rawalpindi | Polygon | 5,657 | 72.632 | 73.640 | 33.062 | 34.018 |
| 26 | Sahiwal | Polygon | 3,950 | 72.386 | 73.343 | 30.172 | 30.931 |
| 27 | Sargodha | Polygon | 2,357 | 72.216 | 73.300 | 31.572 | 32.592 |
| 28 | Sheikhupura | Polygon | 1,708 | 73.263 | 74.701 | 31.347 | 32.068 |
| 29 | Sialkot | Polygon | 1,767 | 74.199 | 74.947 | 32.047 | 32.843 |
| 30 | Toba Tek Singh | Polygon | 2,161 | 72.139 | 72.839 | 30.527 | 31.379 |
| 31 | Vehari | Polygon | 2,246 | 71.738 | 72.972 | 29.585 | 30.368 |

Global bbox (all 31): lon 69.321–75.381, lat 27.705–34.018. Matches the
expected Punjab extent.

---

## 4. Coverage against the 34-district master

Reference: `processed/district_master_clean.csv` (34 districts, names are
title-case with " District" suffix, e.g. "Bahawalnagar District").

**Matched (29):** Attock, Bahawalnagar, Bahawalpur, Chakwal, Dera Ghazi Khan,
Faisalabad, Gujranwala, Gujrat, Hafizabad, Jhelum, Kasur, Khanewal, Khushab,
Lahore, Lodhran, Mandi Bahauddin, Mianwali, Multan, Narowal, Pakpattan,
Rahim Yar Khan, Rajanpur, Rawalpindi, Sahiwal, Sargodha, Sheikhupura,
Sialkot, Toba Tek Singh, Vehari.

**Missing in the ArcGIS GeoJSON (5):**

| Missing district | Division (per PBS census) | Note |
|---|---|---|
| Bhakkar District | Sargodha | Western Punjab, irrigated by Jhang branch canal |
| Jhang District | Sargodha | Large Chenab-corridor district |
| Layyah District | Sargodha | Indus-left-bank district |
| Muzaffargarh District | Multan | Southwestern Punjab, between Indus and Chenab |
| Okara District | Sahiwal | Central Punjab, NE of Sahiwal |

All five are contiguous, forming a corridor running roughly
south-southwest from Jhang through Bhakkar/Layyah to Muzaffargarh. This is
a **known incompleteness in the ArcGIS source dataset**, not a fetch or
filter issue — `returnCountOnly=true` on the same layer returns exactly 31.

**Extra in the ArcGIS GeoJSON (2, both expected):**

| Extra | Reason |
|---|---|
| Chiniot | Created post-census-baseline; documented in `pbs_extraction_quality_report.md` §3 |
| Nankana Sahib | Same reason as Chiniot |

These two units exist in the PBS 2024 census but not in our 34-district
master. They will be excluded from any district-level merge (left-join on
the 34-district master drops them automatically).

---

## 5. Implications for Step 5 (spatial join)

Step 5 must assign each of the 117 NASA POWER grid points to one of the
34 master districts. With only 29 polygon matches, the spatial join will:

1. Use ray-casting point-in-polygon for districts with a boundary.
2. **Fall back to nearest-centroid assignment for Bhakkar, Jhang, Layyah,
   Muzaffargarh, and Okara.** The district coordinate table built in
   Step 3 supplies the centroid for every master district.
3. Emit a join-key table (`processed/weather_join_keys.csv`) with a
   `method` column (`polygon` vs `nearest_centroid`) and a `distance_km`
   column so downstream steps can flag records that used the fallback.

The fallback records are not dummy data — they use real NASA POWER grid
points and real district centroids — but the join is approximate. The
Step 5 report will quantify the approximation (max fallback distance, mean
fallback distance, which grid points were reused).

---

## 6. Test run result (2026-08-31)

```
Ran 13 tests in 0.858s
OK
```

| Suite | Tests | Status |
|---|---:|---|
| TestRealFile | 9 | all pass |
| TestMalformedFiles | 4 | all pass |

Real-file tests assert: feature count = 31, CRS = WGS84, geometry types
∈ {Polygon, MultiPolygon}, vertex counts within 100–50k, bboxes inside
Punjab envelope, no duplicate names, the 5 missing districts match the
known set, the 2 extras match the known set, no warnings emitted.

Malformed-file tests assert: wrong `type`, missing `DISTRICT` property,
unsupported geometry type (Point), and duplicate names all raise
`BoundaryValidationError`.

---

## 7. Step 2 — stop

Step 2 is complete. Files changed by this step:

- `raw/arcgis/punjab_district_boundaries.geojson` (new, 2.1 MB, fetched from ArcGIS)
- `scripts/validate_punjab_boundaries.py` (new)
- `tests/test_validate_punjab_boundaries.py` (new, 13 tests, all pass)
- `reports/step_boundary_validation_report.md` (this report, new)

No existing cleaned files, PBS extracts, or NASA POWER JSONs were touched.

**Blocker surfaced:** 5 of the 34 master districts have no polygon in the
ArcGIS source. Documented in §4; Step 5 will handle them via
nearest-centroid fallback with an explicit audit trail.

Pipeline paused here for review — **Step 3 (build the 41-district
coordinate table and cross-check against the 34-district master) starts on
your go**.