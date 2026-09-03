# NASA POWER Regional API Schema Report

- **Generated:** 2026-08-31
- **Endpoint:** `https://power.larc.nasa.gov/api/temporal/daily/regional`
- **Query parameters:**
  - `latitude-min=27.7`, `latitude-max=34.0`
  - `longitude-min=69.9`, `longitude-max=75.4`
  - `community=ag`, `format=json`, `units=metric`
  - `header=true`, `time-standard=lst`
  - `parameters=T2M` (single parameter per request — API constraint)
  - `start=YYYYMMDD`, `end=YYYYMMDD`
- **Sample file:** `raw/regional/2024-T2M-regional.json` (736 KB)
- **Parser:** `scripts/parse_nasa_power_regional.py`
- **Tests:** `tests/test_nasa_power_regional.py`

---

## 1. Purpose

The NASA POWER regional endpoint provides a **Punjab-wide gridded
historical weather baseline** covering the bounding box
lat 27.7–34.0, lon 69.9–75.4. This is separate from the district-level
point queries used in Steps 1–6.

Use cases:
- Historical baseline for the entire Punjab region
- Cross-validation of point-level data
- Filling gaps in district-level coverage (future work)

---

## 2. Schema identity with point API

The regional endpoint returns the **exact same GeoJSON schema** as the
point-level API documented in `reports/step_weather_schema_report.md`:

- Top-level: `FeatureCollection` with `features`, `header`, `parameters`,
  `times`, `messages` keys.
- Each feature: `Point` geometry with `[lon, lat, elevation]` coordinates.
- Each feature's `properties.parameter`: single parameter key with
  date-indexed daily values.
- Header: `MERRA2` source, `LST` time standard, `-999` fill value.

The 117 grid points returned by the regional query are **identical** to
the 117 points in the point-level files (lon 70–75, lat 28–34, ~1° grid).

---

## 3. Key differences from point API

| Aspect | Point API | Regional API |
|---|---|---|
| Query | Single lat/lon | Bounding box (lat-min/max, lon-min/max) |
| Parameters | Up to 3 per request | **1 per request** (API constraint) |
| Response size | ~3 MB (full year, 1 param) | ~0.7 MB (full year, 1 param) |
| Grid coverage | Same 117 points | Same 117 points |

The regional API's single-parameter constraint means fetching a full
year of T2M + RH2M + PRECTOTCORR requires 3 separate requests.

---

## 4. Sample file inspection (2024-T2M-regional.json)

| Metric | Value |
|---|---|
| File size | 736,097 bytes |
| Features | 117 |
| Parameter | `T2M` |
| Units | `C` |
| Date range | 20240101 – 20241231 |
| Days | 366 (leap year) |
| Fill values | 0 (in Punjab window) |

---

## 5. API constraints and rate limits

- **Single parameter per request.** The API rejects multi-parameter
  regional queries with HTTP 422.
- **Date range required.** Omitting `start`/`end` returns HTTP 422.
- **No documented rate limit.** Fetches completed in <5 minutes for
  full-year single-parameter queries.

---

## 6. Relationship to district-level processing

The regional baseline is **kept separate** from the district-level weather
pipeline (Steps 1–6):

- District-level: point queries → spatial join → monthly aggregation
- Regional baseline: bounding-box query → standalone parser

The regional data can be used for:
- Cross-validation (regional grid vs district-assigned grid)
- Gap-filling for the 6 uncovered districts (future work)
- Punjab-wide climate summaries

The regional parser does **not** overwrite any district-level files.

---

## 7. Parser design

`scripts/parse_nasa_power_regional.py` is a thin wrapper around the
point-level parser logic. It:

- Accepts regional API JSON files (same schema).
- Enforces the same 8 invariants (FeatureCollection, fill_value, etc.).
- Emits normalized records with `source="nasa_power_regional_merra2"`
  (vs `"nasa_power_merra2"` for point-level).
- Preserves grid coordinates, date keys, and parameter names verbatim.

---

## 8. Test coverage

`tests/test_nasa_power_regional.py` covers:

- Schema validation on the sample file (2024-T2M-regional.json).
- Record count = 117 × 366 = 42,822.
- Date parsing correctness.
- Fill-value filtering (synthetic injection).
- Source field = `"nasa_power_regional_merra2"`.

All tests use the real regional API file on disk.

---

## 9. Future work

- Fetch RH2M and PRECTOTCORR regional baselines (2 additional requests per year).
- Aggregate regional grid to districts using the Step 5 spatial join.
- Compare regional baseline vs district-level aggregation for consistency.
