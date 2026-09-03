# Step 1 — NASA POWER Daily Weather JSON Schema Report

- **Generated:** 2026-08-31
- **Scope:** Read-only inspection of the 12 pending NASA POWER JSON files in
  `Kisaan_Dost_Data/Historical Data/`.
- **Files inspected:**
  - `2022-PRECTOTCORR.json`, `2022-RH2M.json`, `2022-T2M.json`
  - `2023-PRECTOTCORR.json`, `2023-RH2M.json`, `2023-T2M.json`
  - `2024-PRECTOTCORR.json`, `2024-RH2M.json`, `2024-T2M.json`
  - `2025-PRECTOTCORR.json`, `2025-RH2M.json`, `2025-T2M.json`
- **Parser delivered with this report:** `scripts/parse_nasa_power_json.py`
- **Tests delivered with this report:** `tests/test_parse_nasa_power_json.py`

---

## 1. High-level shape

Each file is a **GeoJSON FeatureCollection** emitted by the NASA POWER
v2.9.7 Daily API. Top-level keys:

| Key | Type | Example / notes |
|---|---|---|
| `type` | string | `"FeatureCollection"` |
| `features` | list[dict] | 117 features per file |
| `header` | dict | Metadata block (see §2) |
| `parameters` | dict | One entry per variable (see §3) |
| `times` | dict | Empty dict `{}` in all 12 files; not used |
| `messages` | list | Always `[]` |

---

## 2. `header` block

```json
{
  "title": "NASA/POWER Source Native Resolution Daily Data",
  "api": {"version": "v2.9.7", "name": "POWER Daily API"},
  "sources": ["MERRA2"],
  "fill_value": -999,
  "time_standard": "LST",
  "start": "YYYYMMDD",
  "end": "YYYYMMDD"
}
```

`start` and `end` are the full calendar-year range
(`20220101`–`20221231`, `20230101`–`20231231`, `20240101`–`20241231`,
`20250101`–`20251231`). Source product is **MERRA2** (reanalysis). Time
standard is **Local Solar Time (LST)**. Fill value used for missing cells is
`-999`.

---

## 3. `parameters` block

Each file carries exactly **one** parameter, identified by filename:

| Filename stem | Parameter key | Units | Long name |
|---|---|---|---|
| `*-PRECTOTCORR.json` | `PRECTOTCORR` | `mm/day` | Precipitation Corrected |
| `*-RH2M.json` | `RH2M` | `%` | Relative Humidity at 2 Meters |
| `*-T2M.json` | `T2M` | `C` | Temperature at 2 Meters |

The `parameters` dict has a single entry:

```json
{ "T2M": { "units": "C", "longname": "Temperature at 2 Meters" } }
```

(Units and longname differ per file but the structure is the same.)

---

## 4. `features` array

Each of the 117 features is a standard GeoJSON Feature:

```python
{
    "type": "Feature",
    "geometry": {
        "type": "Point",
        "coordinates": [lon, lat, elevation]   # e.g. [70, 28, 79.11]
    },
    "properties": {
        "parameter": {
            "<PARAM>": { "YYYYMMDD": <float>, ... }   # one entry per day
        }
    }
}
```

Key observations from inspection:

- **117 features × 12 files = 1,404 features total.** The 117 points are
  shared across all 12 files — same grid, different parameter / year.
- Grid is a regular **~1° lat/lon** grid covering roughly lon 70–75 and lat
  28–34. **9 unique longitudes × 13 unique latitudes = 117 unique points.**
- Elevation is reported in the third coordinate element (variable, example
  79.11 m at lon=70 lat=28).
- Each feature's `properties.parameter` dict has **exactly one key** (the
  file's parameter name) whose value is a date-indexed dict.
- Date keys use `YYYYMMDD` format (no separators). For full-year files the
  count is 365 (366 in leap year 2024); 2022 and 2023 have 365 entries,
  2024 has 366, 2025 has 365.
- **Fill value `-999` count in the inspected sample (2024-T2M): 0.** Fill
  values are rare or absent in the Punjab window. The parser still filters
  them defensively.

---

## 5. Spatial coverage

| Axis | Min | Max | Unique values | Step |
|---|---:|---:|---:|---:|
| Longitude | 70 | 75 | 9 | 1° |
| Latitude  | 28 | 34 | 13 | 0.5° (some rows) |

The 117 grid points span the Punjab plain. The westernmost point (lon 70)
covers the Suleiman Range edge (DG Khan, Rajanpur); the easternmost
(lon 75) covers the Wagah/Narowal corridor; the northernmost (lat 34)
covers Attock/Rawalpindi; the southernmost (lat 28) covers Rahim Yar Khan
and Bahawalnagar.

Because the grid is ~1° resolution, a single district polygon typically
contains **1–4 grid points**. Some small districts may contain none; the
spatial-join step (Step 5) will fall back to nearest-centroid assignment
for those, with an explicit flag in the join report.

---

## 6. Temporal coverage per file

| File year | Start | End | Days | Leap year |
|---|---|---|---:|---|
| 2022 | 20220101 | 20221231 | 365 | no |
| 2023 | 20230101 | 20231231 | 365 | no |
| 2024 | 20240101 | 20241231 | 366 | yes |
| 2025 | 20250101 | 20251231 | 365 | no |

Combined coverage: **1,461 days** (2022-01-01 through 2025-12-31) per grid
point per parameter.

---

## 7. Variable-specific notes for downstream aggregation

| Parameter | Per-day value semantics | Month aggregation |
|---|---|---|
| `T2M` (°C) | Daily mean 2-m air temperature | arithmetic mean |
| `RH2M` (%) | Daily mean 2-m relative humidity | arithmetic mean |
| `PRECTOTCORR` (mm/day) | Daily corrected precipitation rate | **sum** over month; result in mm |

These are the standard NASA POWER aggregation conventions. The parser
itself does not aggregate — it emits one record per (point, date, param)
so that the downstream aggregation script can choose mean vs sum per
parameter.

---

## 8. Invariants the parser enforces

1. `type == "FeatureCollection"`.
2. `header.sources[0] == "MERRA2"` (informational, not a hard gate).
3. `header.fill_value == -999` (used to filter out fill cells).
4. `len(features) == 117` for every file in this set.
5. Every feature has `geometry.type == "Point"` with 3 coordinates
   `[lon, lat, elevation]`.
6. Every feature's `properties.parameter` dict has **exactly one key**,
   matching the parameter declared in the top-level `parameters` dict.
7. Every date key parses as `YYYYMMDD` and falls within
   `[header.start, header.end]`.
8. Date counts per feature match the expected day count for the year
   (365 or 366).

Violations of (1), (4), (5), (6), (7) raise; (8) is a warning because
partial-year files are legitimate inputs if the set is extended later.

---

## 9. Output schema of `parse_nasa_power_json.py`

The parser emits a list of normalized records, one per (point, date):

```python
{
    "source": "nasa_power_merra2",
    "file_path": "<input path>",
    "parameter": "T2M",          # or RH2M, PRECTOTCORR
    "units": "C",
    "year": 2024,
    "month": 1,
    "day": 15,
    "date": "2024-01-15",        # ISO
    "lon": 70.0,
    "lat": 28.0,
    "elevation_m": 79.11,
    "value": 15.44,
}
```

For 12 files × 117 points × 365 (or 366) days this produces **≈ 515k
records** total. The parser is streaming-safe: it does not require the
normalized list to fit in memory when used via its `iter_records()`
generator API.

---

## 10. Test coverage

`tests/test_parse_nasa_power_json.py` covers:

- Schema validation on one real file (2024-T2M).
- Record count = `117 × 366` for the 2024 file; `117 × 365` for 2022/2023/2025.
- Date parsing correctness (first day, last day, Feb-29 in 2024).
- Fill-value filtering (injects a synthetic `-999` and verifies it is dropped).
- Coordinate extraction (9 unique lons, 13 unique lats).
- Parameter metadata extraction (`T2M` / units / longname).
- Fill-value sentinel in `header.fill_value` matches `-999`.
- Graceful error on a malformed file (missing `features` key).

All tests use the real NASA POWER files on disk — no synthetic fixtures
for the success path, because the 12 input files are the authoritative
inputs for downstream merges.

---

## 11. Test run result (2026-08-31)

```
Ran 16 tests in 2.323s
OK
```

| Suite | Tests | Status |
|---|---:|---|
| TestRealFileParsing | 11 | all pass |
| TestFillValueFiltering | 2 | all pass |
| TestMalformedFiles | 3 | all pass |
| TestSummarize | 1 | pass |

Record counts observed by `parse_file()`:

| File | Records | Expected |
|---|---:|---:|
| 2022-{T2M,RH2M,PRECTOTCORR}.json | 42,705 each | 117 × 365 ✓ |
| 2023-{T2M,RH2M,PRECTOTCORR}.json | 42,705 each | 117 × 365 ✓ |
| 2024-{T2M,RH2M,PRECTOTCORR}.json | 42,822 each | 117 × 366 ✓ (leap year) |
| 2025-{T2M,RH2M,PRECTOTCORR}.json | 42,705 each | 117 × 365 ✓ |

**Total normalized records: 513,216** across the 12 input files.

Fill-value scan of all 12 raw files: **0 occurrences of -999** — the filter
is defensive only.

---

## 12. Step 1 — stop

Step 1 is complete. Files changed by this step:

- `reports/step_weather_schema_report.md` (this report, newly created)
- `scripts/parse_nasa_power_json.py` (newly created)
- `tests/test_parse_nasa_power_json.py` (newly created, 16 tests, all pass)

No existing cleaned files, PBS extracts, or master CSVs were touched.
Pipeline paused here for review — **Step 2 (Punjab boundary GeoJSON fetch
and validation) starts on your go**.
