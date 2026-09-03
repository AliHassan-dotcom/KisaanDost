# Step 4 — Open-Meteo URL Template Report

- **Generated:** 2026-08-31
- **Generator:** `scripts/build_open_meteo_url.py`
- **Tests:** `tests/test_build_open_meteo_url.py` — 27/27 pass
- **Coordinate source:** `processed/district_coordinates.csv` (Step 3 output)

---

## 1. Purpose

Produce a valid Open-Meteo `/v1/forecast` URL for any of:

1. A Punjab district name (resolved against the 41-entry coordinate table).
2. Raw latitude + longitude (used directly).

The template's parameter set, variable ordering, and defaults are preserved
**verbatim** from the project prompt — no variable dropped, no ordering
rearranged, no default swapped.

---

## 2. Public API

```python
from scripts.build_open_meteo_url import build_url, resolve_district, all_urls

# Mode 1: by district name (case-insensitive; " District" suffix optional)
url = build_url(district="Lahore")

# Mode 2: by raw coordinates
url = build_url(latitude=31.5204, longitude=74.3587)

# Lookup only — returns the matching CSV row
row = resolve_district("Rahim Yar Khan")

# All 41 URLs at once
entries = all_urls()
```

CLI:

```
python scripts/build_open_meteo_url.py Lahore
python scripts/build_open_meteo_url.py --lat 31.5204 --lon 74.3587
python scripts/build_open_meteo_url.py --all
```

---

## 3. Template preservation — parameter by parameter

The generated URL for `Lahore`:

```
https://api.open-meteo.com/v1/forecast
  ?latitude=31.5204
  &longitude=74.3587
  &current=temperature_2m,relative_humidity_2m,precipitation,wind_speed_10m
  &hourly=temperature_2m,relative_humidity_2m,dewpoint_2m,precipitation,
          vapour_pressure_deficit,et0_fao_evapotranspiration,
          wind_speed_10m,wind_gusts_10m,weather_code,
          soil_temperature_0cm,soil_temperature_6cm,soil_temperature_18cm,
          soil_moisture_0_to_1cm,soil_moisture_1_to_3cm,
          soil_moisture_3_to_9cm,soil_moisture_9_to_27cm,
          shortwave_radiation,direct_normal_irradiance
  &daily=temperature_2m_max,precipitation_sum,precipitation_probability_max,
         shortwave_radiation_sum,et0_fao_evapotranspiration
  &models=ecmwf_ifs,best_match
  &timezone=auto
```

| Param | Value | Matches prompt template? |
|---|---|---|
| base | `https://api.open-meteo.com/v1/forecast` | ✓ |
| `latitude` / `longitude` | resolved from CSV or raw | (variable) |
| `current` (4 vars) | `temperature_2m, relative_humidity_2m, precipitation, wind_speed_10m` | ✓ |
| `hourly` (18 vars) | `temperature_2m, relative_humidity_2m, dewpoint_2m, precipitation, vapour_pressure_deficit, et0_fao_evapotranspiration, wind_speed_10m, wind_gusts_10m, weather_code, soil_temperature_0cm, soil_temperature_6cm, soil_temperature_18cm, soil_moisture_0_to_1cm, soil_moisture_1_to_3cm, soil_moisture_3_to_9cm, soil_moisture_9_to_27cm, shortwave_radiation, direct_normal_irradiance` | ✓ |
| `daily` (5 vars) | `temperature_2m_max, precipitation_sum, precipitation_probability_max, shortwave_radiation_sum, et0_fao_evapotranspiration` | ✓ |
| `models` | `ecmwf_ifs,best_match` | ✓ |
| `timezone` | `auto` | ✓ |

**Ordering assertion** (verified by test
`test_parameter_ordering`): the raw query string emits keys in exactly
`latitude, longitude, current, hourly, daily, models, timezone` — no
reordering.

**No percent-encoded commas**: commas inside list values are emitted as
literal `,` (via `urlencode(..., safe=",")`), not `%2C`. Verified by test
`test_no_percent_encoded_commas`.

---

## 4. Validation cases

### 4.1 District lookup success

| Input | Resolved lat | Resolved lon | URL |
|---|---:|---:|---|
| `Lahore` | 31.5204 | 74.3587 | (see §3) |
| `lahore` | 31.5204 | 74.3587 | identical to above (case-insensitive) |
| `Lahore District` | 31.5204 | 74.3587 | identical (suffix tolerated) |
| `Rahim Yar Khan` | 28.4212 | 70.2989 | lat/lon substituted, rest unchanged |
| `Chiniot` (annex) | 31.7200 | 72.9780 | URL built normally; `is_master_district=False` |
| `Kot Addu` (tehsil promoted) | 30.4700 | 70.9667 | URL built normally |

### 4.2 Raw lat/lng success

```
>>> build_url(latitude=31.5204, longitude=74.3587)
https://api.open-meteo.com/v1/forecast?latitude=31.5204&longitude=74.3587&...
```

Identical to the district-lookup URL for Lahore (coordinates match to 4
decimal places).

### 4.3 Lookup failure

```
>>> build_url(district="Not A District")
DistrictNotFoundError: district 'Not A District' not found in
    district_coordinates.csv. Available: ['Attock', ..., 'Wazirabad']
```

The exception lists all 41 available district names so callers can
suggest a close match to the user.

### 4.4 Rejected inputs

| Input | Error |
|---|---|
| `district="Lahore"` AND `latitude=...` | `ValueError` (ambiguous mode) |
| `latitude=...` only (no longitude) | `ValueError` (partial coords) |
| `latitude=95.0` | `ValueError` (out of [-90, 90]) |
| `longitude=200.0` | `ValueError` (out of [-180, 180]) |
| No inputs at all | `ValueError` |

---

## 5. Annex / non-master district handling

The generator **does not filter by `is_master_district`**. If a caller
asks for Chiniot, Nankana Sahib, Kot Addu, Murree, Talagang, Taunsa, or
Wazirabad, the URL is built normally — Open-Meteo has no concept of our
master list.

The accompanying `row` from `resolve_district()` carries the truth value
of `is_master_district` and the `notes` tag (`annex unit`, `newly created
district`, `tehsil promoted`) so downstream code can decide whether to
cache the response, merge it into the 34-district master, or keep it as a
separate reference series.

For downstream weather ingestion:

- **Master districts (34):** URLs emitted, responses intended for merge
  into `district_master_clean.csv`.
- **Annex units (2):** URLs emitted, responses kept separate or dropped
  by left-join at merge time.
- **Newly created + tehsil-promoted (5):** URLs emitted, responses kept
  as supplementary context only.

---

## 6. Test run result (2026-08-31)

```
Ran 27 tests in 0.077s
OK
```

| Suite | Tests | Status |
|---|---:|---|
| TestDistrictLookup | 7 | all pass |
| TestBuildUrlDistrict | 9 | all pass |
| TestBuildUrlRaw | 6 | all pass |
| TestAllUrls | 3 | all pass |
| TestAnnexAndNonMaster | 2 | all pass |

Key assertions:
- Parameter ordering exactly `latitude, longitude, current, hourly, daily, models, timezone`.
- Current (4), hourly (18), daily (5) variable lists match the template.
- Models = `ecmwf_ifs,best_match` (order preserved).
- Timezone = `auto`.
- No percent-encoded commas in the URL.
- District lookup is case-insensitive and tolerates " District" suffix.
- Annex + tehsil-promoted entries build valid URLs with the right coordinates.
- `all_urls()` emits 41 entries: 34 master + 2 annex + 5 tehsil/newly-created.

---

## 7. JSON / Flutter helper (not implemented here)

The user's rules explicitly keep any JSON or Flutter helper **separate and
dynamic**. This report documents only the Python URL generator. A
future Flutter `OpenMeteoUrlBuilder` or JSON config writer, if
requested, will read the same coordinate CSV at runtime and emit the same
URL shape — it must not be hard-coded here, so that any change to the
template propagates from one source of truth.

---

## 8. Step 4 — stop

Step 4 is complete. Files changed by this step:

- `scripts/build_open_meteo_url.py` (new)
- `tests/test_build_open_meteo_url.py` (new, 27 tests, all pass)
- `reports/open_meteo_url_template_report.md` (this report, new)

No existing cleaned files were touched. The coordinate CSV from Step 3
was read but not modified.

Pipeline paused here for review — **Step 5 (spatial join of the 117
NASA POWER grid points to district polygons, with nearest-centroid
fallback for the 5 missing districts) starts on your go**.