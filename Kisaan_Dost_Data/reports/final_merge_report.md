# Step 7 — Versioned Master Merge Report

**Date:** 2026-08-31
**Script:** `scripts/build_versioned_master.py`
**Tests:** `tests/test_build_versioned_master.py` — 20 passed, 0 failed

## Objective

Merge validated monthly weather features (Step 6 output) into the authoritative district master, and isolate PBS census data for non-master units in a separate context file. No existing files were modified.

## Inputs

| File | Rows | Columns | Scope |
|------|------|---------|-------|
| `processed/district_master_clean.csv` | 1,904 | 18 | 34 districts × 56 months (2022-01 to 2026-08) |
| `processed/district_monthly_weather.csv` | 1,632 | 13 | 34 districts × 48 months (2022-01 to 2025-12) |
| `processed/pbs_*.csv` (8 files) | varies | varies | 37 districts (34 master + 3 extra) |

## Outputs

### `processed/kisaan_dost_master_v2.csv`

- **Rows:** 1,904 (identical to master — left join, no rows added or dropped)
- **Columns:** 27 (18 original + 9 weather)
- **Key:** (year, month, district) — 0 duplicates

**Weather columns appended:**

| Column | Type | Description |
|--------|------|-------------|
| `t2m_mean_c` | float/empty | Monthly mean 2m temperature (C) |
| `rh2m_mean_percent` | float/empty | Monthly mean 2m relative humidity (%) |
| `precip_total_mm` | float/empty | Monthly total precipitation (mm) |
| `grid_points_used` | int/empty | Count of grid points in aggregation |
| `polygon_point_count` | int/empty | Points matched via polygon PIP |
| `fallback_point_count` | int/empty | Points matched via nearest-centroid |
| `no_coverage_flag` | True/empty | True for 6 districts with no grid coverage |
| `source_provider` | string/empty | `nasa_power_merra2` when weather present |
| `source_files_covered` | string/empty | Pipe-delimited source file list |

### `processed/kisaan_dost_context_only.csv`

- **Rows:** 99
- **Columns:** 80 (union of all PBS table schemas + `source_table`)
- **Districts:** Chiniot District, Nankana Sahib District, Cholistan Area
- **Source tables:** 7 distinct PBS tables

## Weather Coverage Breakdown

| Category | Rows | Explanation |
|----------|------|-------------|
| Weather present | 1,344 | 28 covered districts × 48 months (2022–2025) |
| Weather null (uncovered) | 288 | 6 uncovered districts × 48 months |
| Weather null (out-of-range) | 272 | 34 districts × 8 months (2026-01 to 2026-08) |
| **Total** | **1,904** | |

### Uncovered Districts (no_coverage_flag=True)

Gujrat, Lodhran, Mianwali, Narowal, Pakpattan, Sheikhupura — all have ArcGIS polygons but no NASA POWER grid points fall inside them at ~1 degree resolution. Measurement columns are empty; metadata columns carry `grid_points_used=0` and `source_provider=nasa_power_merra2`.

## Merge Strategy

1. Load master (1,904 rows) and weather index keyed by `(year, month, normalized_district)`.
2. For each master row, look up weather by `(year, month, district)` — master already uses normalized names (e.g. "Attock District").
3. If match found: copy 9 weather columns.
4. If no match: set all 9 weather columns to empty string.
5. Write output preserving original column order with weather appended.

## Context File Strategy

1. Iterate all 8 PBS CSV files.
2. Extract rows where `district` is one of the 3 extra units (Chiniot District, Nankana Sahib District, Cholistan Area).
3. Add `source_table` column from the PBS filename.
4. Concatenate into a single file with a unified column schema (union of all PBS tables).

## Validation Summary

| Check | Result |
|-------|--------|
| Master row count = 1,904 | PASS |
| Master column count = 27 | PASS |
| Duplicate keys = 0 | PASS |
| Original 18 columns preserved verbatim | PASS |
| Weather present = 1,344 rows | PASS |
| Weather null = 560 rows | PASS |
| 6 uncovered districts flagged | PASS |
| Covered districts have weather in 2022–2025 | PASS |
| 2026 months have null weather | PASS |
| No dummy measurement values | PASS |
| Context rows = 99 | PASS |
| Context districts = 3 extra units only | PASS |
| No master districts in context file | PASS |
| source_table column present in context | PASS |

## Files Created

| File | Size | Description |
|------|------|-------------|
| `processed/kisaan_dost_master_v2.csv` | ~280 KB | Merged master with weather |
| `processed/kisaan_dost_context_only.csv` | ~60 KB | PBS context for 3 extra units |
| `scripts/build_versioned_master.py` | ~8 KB | Merge + context + validation logic |
| `tests/test_build_versioned_master.py` | ~7 KB | 20 tests across 4 classes |
| `reports/final_merge_report.md` | this file | |

## Known Limitations

1. **2026 weather gap:** Weather data only covers 2022–2025. The 272 rows for 2026 (Jan–Aug) have empty weather columns. This will be filled when 2026 daily data is fetched from Open-Meteo (Step 4 URL builder is ready for this).
2. **6 uncovered districts:** Grid resolution limitation (~1 degree). These districts have `no_coverage_flag=True` and empty measurement columns. Downstream ML should either exclude them or use spatial interpolation from neighboring districts.
3. **Context file schema width:** 80 columns is the union of all PBS table schemas. Many cells are empty for any given row because different PBS tables have different columns. This is by design — the context file is a reference, not an ML input.

## Next Step

Step 8 (preserve originals) is implicit — no files were modified or overwritten at any point in the pipeline. The weather pipeline is now complete through Step 7.
