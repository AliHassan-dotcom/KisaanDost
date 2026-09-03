# Step 6 — Monthly Weather Aggregation Report

- **Generated:** 2026-08-31
- **Script:** `scripts/aggregate_weather_monthly.py`
- **Tests:** `tests/test_aggregate_weather_monthly.py` (22 tests, all passed in 18.92 s)
- **Output:** `processed/district_monthly_weather.csv` (1,632 rows × 13 columns)

---

## 1. Purpose

Aggregate daily NASA POWER weather records (from Step 1) to district-month
level using the spatial join keys (from Step 5). Produce a single table
suitable for merging with `district_master_clean.csv` in Step 7.

---

## 2. Aggregation rules

| Parameter | Daily value | Monthly aggregation |
|---|---|---|
| `T2M` (°C) | Daily mean 2-m temperature | **arithmetic mean** |
| `RH2M` (%) | Daily mean 2-m relative humidity | **arithmetic mean** |
| `PRECTOTCORR` (mm/day) | Daily corrected precipitation rate | **sum** (result in mm) |

No interpolation of missing values. No invented data. Districts with no
grid coverage are flagged explicitly.

---

## 3. Summary statistics

| Metric | Count |
|---|---:|
| Total daily records processed | 512,811 |
| Unmatched records (no grid mapping) | 0 |
| Total output rows | 1,632 |
| Valid weather rows (covered districts) | 1,344 |
| Null weather rows (uncovered districts) | 288 |
| Unique districts | 34 |
| Covered districts | 28 |
| Uncovered districts | 6 |
| Year-months | 48 (2022-01 through 2025-12) |
| Duplicate (year, month, district) keys | 0 |
| JSON files processed | 12 |

---

## 4. Row count derivation

- 34 master districts × 48 months = **1,632 total rows**
- 28 covered districts × 48 months = **1,344 valid weather rows**
- 6 uncovered districts × 48 months = **288 null weather rows**

---

## 5. Uncovered districts

These 6 master districts have no NASA POWER grid points assigned (see
Step 5 report §5 for the resolution-limitation explanation):

| District | Null rows |
|---|---:|
| Gujrat | 48 |
| Lodhran | 48 |
| Mianwali | 48 |
| Narowal | 48 |
| Pakpattan | 48 |
| Sheikhupura | 48 |

Each row carries `no_coverage_flag = "True"` and empty weather fields.
The downstream merge (Step 7) should preserve these rows so the master
table retains all 34 districts × 48 months.

---

## 6. Output CSV schema

`processed/district_monthly_weather.csv` — 1,632 rows × 13 columns:

| Column | Type | Description |
|---|---|---|
| `year` | int | Calendar year (2022–2025) |
| `month` | int | Calendar month (1–12) |
| `district` | string | District name |
| `normalized_district` | string | `"<name> District"` form |
| `t2m_mean_c` | float/null | Monthly mean 2-m temperature (°C); empty if uncovered |
| `rh2m_mean_percent` | float/null | Monthly mean 2-m relative humidity (%); empty if uncovered |
| `precip_total_mm` | float/null | Monthly total precipitation (mm); empty if uncovered |
| `grid_points_used` | int | Number of grid points contributing to this cell |
| `polygon_point_count` | int | Grid points matched via polygon |
| `fallback_point_count` | int | Grid points matched via nearest-centroid fallback |
| `no_coverage_flag` | string | `"True"` if district has no grid coverage; `"False"` otherwise |
| `source_provider` | string | Always `nasa_power_merra2` |
| `source_files_covered` | string | Pipe-delimited list of source JSON filenames |

---

## 7. Data quality checks

### 7.1 Value ranges

| Parameter | Min observed | Max observed | Expected range |
|---|---:|---:|---|
| `t2m_mean_c` | -10 to 50 | ✓ | Punjab seasonal extremes |
| `rh2m_mean_percent` | 0 to 100 | ✓ | Physical bounds |
| `precip_total_mm` | ≥ 0 | ✓ | Non-negative |

### 7.2 Grid-point accounting

For every covered row: `polygon_point_count + fallback_point_count ==
grid_points_used`. Verified by test.

### 7.3 Source files

Every covered row has exactly 3 source files (one per parameter):
`YYYY-PRECTOTCORR.json`, `YYYY-RH2M.json`, `YYYY-T2M.json`.

---

## 8. Invariants enforced

1. One row per (year, month, district) — 0 duplicate keys.
2. All 34 master districts present in every month.
3. Uncovered districts have empty weather fields + `no_coverage_flag="True"`.
4. Covered districts have non-empty weather fields + `no_coverage_flag="False"`.
5. Grid-point counts are non-negative and internally consistent.
6. No interpolation, no invented data.

---

## 9. Test coverage (22 tests)

| Class | Tests | Scope |
|---|---:|---|
| TestDataLoaders | 5 | Grid mapping (117 points), master districts (34) |
| TestOutputCSV | 13 | Columns, row count, duplicates, districts, year-months, coverage flags |
| TestAggregationLogic | 4 | Value ranges, non-negative precip, source file format |

All 22 passed.

---

## 10. Known limitations

1. **6 districts have no weather data.** Gujrat, Lodhran, Mianwali,
   Narowal, Pakpattan, Sheikhupura — due to ~1° grid resolution (Step 5).

2. **Coarse spatial representation.** Most districts are represented by
   1–8 grid points. Aggregated values are area-representative, not
   district-precise.

3. **No gap-filling.** If a grid point has missing daily values within a
   month (rare in this dataset), the monthly aggregation uses only the
   available days. No interpolation is performed.

---

## 11. Stop note

Step 6 complete. No files were modified outside the explicit deliverables.
Awaiting Step 7 directive (versioned master merge).
