# Step 5 — Weather Spatial Join Key Report

- **Generated:** 2026-08-31
- **Script:** `scripts/spatial_join_weather_to_districts.py`
- **Tests:** `tests/test_spatial_join_weather_to_districts.py` (35 tests, all passed in 20.45 s)
- **Output:** `processed/weather_join_keys.csv` (512,811 rows, 13 columns, ~69 MB)

---

## 1. Purpose

Map each of the 117 NASA POWER grid points (lon 70–75, lat 28–34) to one
of the 34 master Punjab districts and produce a join-key table that
downstream aggregation scripts can use to roll up daily weather values
into district-month cells.

---

## 2. Method

### 2.1 Point-in-polygon (primary)

Ray-casting algorithm (stdlib only — no shapely/geopandas) applied to
the 29 master-district polygons present in
`raw/arcgis/punjab_district_boundaries.geojson`. Chiniot and Nankana Sahib
(annex districts, present in ArcGIS but not in the 34-district master)
are excluded from PIP matching.

### 2.2 Nearest-centroid fallback

For grid points that do not fall inside any master-district polygon,
the Haversine distance to each of the 5 fallback district centroids is
computed, and the nearest is assigned. The 5 fallback districts are:

| District | Centroid lat | Centroid lon |
|---|---:|---:|
| Bhakkar | 31.6333 | 71.0667 |
| Jhang | 31.2781 | 72.3317 |
| Layyah | 30.9613 | 70.9390 |
| Muzaffargarh | 30.0703 | 71.1933 |
| Okara | 30.8138 | 73.4534 |

---

## 3. Summary statistics

| Metric | Count |
|---|---:|
| Total grid points | 117 |
| Grid points matched via polygon | 51 |
| Grid points matched via fallback | 66 |
| Unassigned grid points | 0 |
| Total join rows | 512,811 |
| Polygon-matched records | 223,533 |
| Fallback-matched records | 289,278 |
| Duplicate join keys | 0 |
| Districts with coverage | 28 / 34 |

---

## 4. Grid-point distribution by district

| District | Grid pts | Method | Distance range (km) |
|---|---:|---|---|
| Okara | 29 | nearest_centroid | 45.0 – 382.9 |
| Bhakkar | 21 | nearest_centroid | 22.8 – 295.3 |
| Bahawalpur | 8 | polygon | — |
| Jhang | 7 | nearest_centroid | 29.4 – 358.0 |
| Muzaffargarh | 6 | nearest_centroid | 9.5 – 297.1 |
| Rahim Yar Khan | 5 | polygon | — |
| Dera Ghazi Khan | 4 | polygon | — |
| Rajanpur | 3 | polygon | — |
| Bahawalnagar | 3 | polygon | — |
| Layyah | 3 | nearest_centroid | 30.0 – 103.4 |
| Khushab | 3 | polygon | — |
| Sargodha | 3 | polygon | — |
| Chakwal | 3 | polygon | — |
| Vehari | 2 | polygon | — |
| Sahiwal | 2 | polygon | — |
| Faisalabad | 2 | polygon | — |
| Kasur | 2 | polygon | — |
| Multan | 1 | polygon | — |
| Khanewal | 1 | polygon | — |
| Toba Tek Singh | 1 | polygon | — |
| Lahore | 1 | polygon | — |
| Hafizabad | 1 | polygon | — |
| Gujranwala | 1 | polygon | — |
| Mandi Bahauddin | 1 | polygon | — |
| Sialkot | 1 | polygon | — |
| Jhelum | 1 | polygon | — |
| Attock | 1 | polygon | — |
| Rawalpindi | 1 | polygon | — |

---

## 5. Districts with no coverage

Six master districts have ArcGIS polygons but no grid point falls inside
them. This is a resolution limitation of the ~1° NASA POWER grid:

| District | Centroid lat | Centroid lon | Reason |
|---|---:|---:|---|
| Gujrat | 32.5742 | 74.0754 | Small district, centroid between grid points |
| Lodhran | 29.5339 | 71.6324 | Narrow strip south of Multan, no grid point inside |
| Mianwali | 32.5839 | 71.5370 | North-western extent, between grid lines |
| Narowal | 32.1020 | 74.8730 | Small eastern district, between lon 74.375 and 75 |
| Pakpattan | 30.3500 | 73.3833 | Small central district, between grid points |
| Sheikhupura | 31.7131 | 73.9783 | Small district near Lahore, between grid points |

These 6 districts will have **no weather data** in downstream
aggregation. The aggregation step (Step 6) should flag them explicitly
in its output.

---

## 6. Known limitations

1. **Fallback distances are large.** Some grid points assigned to the
   5 fallback districts are >300 km from the centroid. This is because
   the fallback pool is restricted to 5 districts — a grid point near
   Gujrat (which has no coverage) gets assigned to the nearest of the
   5 fallback centroids (Jhang or Bhakkar), not to Gujrat itself.

2. **Coarse grid resolution.** The ~1° NASA POWER grid means many
   districts contain only 1–2 grid points. Aggregated values should
   be interpreted as area-representative, not district-precise.

3. **Annex districts excluded.** Chiniot and Nankana Sahib have ArcGIS
   polygons but are not master districts. Grid points falling in these
   polygons are treated as unmatched and assigned via fallback.

---

## 7. Output CSV schema

`processed/weather_join_keys.csv` — 512,811 rows × 13 columns:

| Column | Type | Description |
|---|---|---|
| `source_file` | string | NASA POWER JSON filename (e.g. `2024-T2M.json`) |
| `source_parameter` | string | `T2M`, `RH2M`, or `PRECTOTCORR` |
| `source_date` | string | ISO date (`YYYY-MM-DD`) |
| `grid_lon` | float | Original grid longitude |
| `grid_lat` | float | Original grid latitude |
| `grid_elevation_m` | float | Original grid elevation (m) |
| `district` | string | Assigned district name |
| `normalized_district` | string | `"<name> District"` form |
| `method` | string | `polygon` or `nearest_centroid` |
| `distance_km` | float | 0.0 for polygon; Haversine km for fallback |
| `is_fallback` | string | `"True"` or `"False"` |
| `boundary_match_status` | string | `matched` or `fallback_nearest_centroid` |
| `source_provider` | string | Always `nasa_power_merra2` |

---

## 8. Invariants enforced

1. Every grid point is assigned to exactly one district (0 unassigned).
2. No duplicate join keys (unique on source_file + parameter + date + grid_lon + grid_lat).
3. Grid coordinates are preserved verbatim from the NASA POWER JSON.
4. Fallback assignments only use the 5 named districts.
5. All 12 JSON files are processed (4 years × 3 parameters).
6. Output column order is fixed and documented above.

---

## 9. Test coverage (35 tests)

| Class | Tests | Scope |
|---|---:|---|
| TestPointInPolygon | 6 | Ray-casting with square, triangle, concave polygon |
| TestPointInGeometry | 3 | Polygon + MultiPolygon + unknown geometry |
| TestHaversine | 4 | Zero, known, antipodal, symmetry |
| TestRealDataLoaders | 3 | ArcGIS GeoJSON (31 features), centroids (34 master), fallback list (5) |
| TestGridMapping | 9 | 117 points, mapping completeness, polygon/fallback counts, distance, fields |
| TestOutputCSV | 10 | Columns, duplicates, providers, methods, statuses, coordinates, dates, count |

All 35 passed.

---

## 10. Stop note

Step 5 complete. No files were modified outside the explicit deliverables.
Awaiting Step 6 directive.
