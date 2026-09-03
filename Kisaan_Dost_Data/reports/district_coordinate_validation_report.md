# Step 3 — District Coordinate Validation Report

- **Generated:** 2026-08-31
- **Output CSV:** `processed/district_coordinates.csv` (41 rows × 8 columns)
- **Builder:** `scripts/build_district_coordinates.py`
- **Tests:** `tests/test_build_district_coordinates.py` — 15/15 pass
- **Source of coordinates:** verbatim from the project prompt (41-entry
  Punjab district coordinate mapping). No coordinates were invented,
  interpolated, or rounded.

---

## 1. Output schema

`processed/district_coordinates.csv` columns:

| Column | Type | Example | Notes |
|---|---|---|---|
| `district` | string | `Rahim Yar Khan` | Original prompt spelling |
| `normalized_district` | string | `Rahim Yar Khan District` | title-case + ` District`; used as the join key against the 34-district master |
| `latitude` | float | `28.4212` | WGS84, 4 decimal places |
| `longitude` | float | `70.2989` | WGS84, 4 decimal places |
| `source` | string | `project_prompt` | Constant across all 41 rows |
| `source_timestamp` | ISO-8601 | `2026-08-31T...` | Build time (UTC) |
| `is_master_district` | string | `True` / `False` | `True` iff in the 34-district master |
| `notes` | string | (see §6) | Empty for master, one of 3 tags for non-master |

---

## 2. Validation summary

| Metric | Value |
|---|---:|
| Total coordinates loaded | **41** |
| Master districts (per master CSV) | 34 |
| Master districts matched in coordinate table | **34 / 34** |
| Master districts missing from coordinate table | **0** |
| Extra non-master entries | 7 |
| Duplicate district names | 0 |
| Latitude range | 28.4212 (Rahim Yar Khan) – 33.9070 (Murree) |
| Longitude range | 70.2989 (Rahim Yar Khan) – 74.8730 (Narowal) |

All 34 districts in `processed/district_master_clean.csv` have a
corresponding coordinate row — no district in the master is missing a
lat/lng.

---

## 3. Master-district match list (34)

The 34 rows where `is_master_district = True`:

1. Attock — 33.7660, 72.3609
2. Bahawalnagar — 29.9987, 73.2536
3. Bahawalpur — 29.3956, 71.6836
4. Bhakkar — 31.6333, 71.0667
5. Chakwal — 32.9328, 72.8630
6. Dera Ghazi Khan — 30.0489, 70.6403
7. Faisalabad — 31.4504, 73.1350
8. Gujranwala — 32.1877, 74.1945
9. Gujrat — 32.5742, 74.0754
10. Hafizabad — 32.0709, 73.6880
11. Jhang — 31.2781, 72.3317
12. Jhelum — 32.9405, 73.7276
13. Kasur — 31.1156, 74.4503
14. Khanewal — 30.3017, 71.9321
15. Khushab — 32.2952, 72.3501
16. Lahore — 31.5204, 74.3587
17. Layyah — 30.9613, 70.9390
18. Lodhran — 29.5339, 71.6324
19. Mandi Bahauddin — 32.5861, 73.4917
20. Mianwali — 32.5839, 71.5370
21. Multan — 30.1575, 71.5249
22. Muzaffargarh — 30.0703, 71.1933
23. Narowal — 32.1020, 74.8730
24. Okara — 30.8138, 73.4534
25. Pakpattan — 30.3500, 73.3833
26. Rahim Yar Khan — 28.4212, 70.2989
27. Rajanpur — 29.1044, 70.3297
28. Rawalpindi — 33.5651, 73.0169
29. Sahiwal — 31.6701, 73.1068
30. Sargodha — 32.0836, 72.6711
31. Sheikhupura — 31.7131, 73.9783
32. Sialkot — 32.4945, 74.5229
33. Toba Tek Singh — 30.9667, 72.4833
34. Vehari — 30.0419, 72.3441

---

## 4. Extra non-master entries (7)

Preserved as the user instructed ("Do not drop any provided coordinate
entries"). These do not appear in the 34-district master and will be
filtered out by any left-join against it.

| # | District | Lat | Lon | `notes` | Justification |
|---:|---|---:|---:|---|---|
| 1 | Chiniot | 31.7200 | 72.9780 | annex unit | Created after the master was defined; documented in `pbs_extraction_quality_report.md` §3. Polygon available from ArcGIS boundary (Step 2). |
| 2 | Nankana Sahib | 31.4492 | 73.7124 | annex unit | Same reason as Chiniot. Polygon available from ArcGIS boundary. |
| 3 | Kot Addu | 30.4700 | 70.9667 | tehsil promoted | Historically a tehsil of Muzaffargarh; gazetted as a district in 2022. Not in the 34-district master. |
| 4 | Murree | 33.9070 | 73.3903 | tehsil promoted | Historically a tehsil of Rawalpindi; elevated to district status in 2023. Hill-station belt, not agricultural plains. |
| 5 | Talagang | 32.9272 | 72.4158 | newly created district | Separated from Chakwal (2022). Not in master. |
| 6 | Taunsa | 30.7036 | 70.6506 | tehsil promoted | Historically a tehsil of DG Khan. |
| 7 | Wazirabad | 32.4431 | 74.1202 | tehsil promoted | Historically a tehsil of Gujranwala. |

The two annex units (Chiniot, Nankana Sahib) were also surfaced in the
boundary validation report as "extra in GeoJSON" — their polygons are
available if needed for future spatial joins.

The four "tehsil promoted" entries and the one "newly created district"
entry are coordinate-only; no boundary polygon exists for them in the
ArcGIS source.

---

## 5. Name normalization rules

| Rule | Example |
|---|---|
| `district` column: copy prompt name verbatim (no casing change, no suffix). | `"Rahim Yar Khan"` |
| `normalized_district` column: `{district} District` (exact match to the master's `district` column). | `"Rahim Yar Khan District"` |
| Matching uses **exact string equality** on `normalized_district` against `district_master_clean.district`. No fuzzy or stem matching. |
| Coordinate values are taken verbatim from the prompt (4 decimal places). No rounding beyond what the prompt already specified. |

---

## 6. Coverage implications for downstream steps

**Step 4 (Open-Meteo URL builder)** can accept any of the 41 entries by
name, plus raw lat/lng pairs. The URL generator will not enforce
`is_master_district` — it is the caller's responsibility to decide
whether to include annex/tehsil-promoted entries.

**Step 5 (spatial join)** will use only the 34 master-district rows.
The 7 non-master rows are preserved in the coordinate CSV for reference
but will not be used as join keys. The 5 master districts that are
**missing from the ArcGIS boundary** (Bhakkar, Jhang, Layyah,
Muzaffargarh, Okara) all have coordinate rows here, so they will be
served by the nearest-centroid fallback documented in
`step_boundary_validation_report.md` §5.

**Step 7 (versioned master merge)** will join weather aggregates to
`district_master_clean.csv` on `normalized_district`; only the 34 master
districts will carry weather features.

---

## 7. Test run result (2026-08-31)

```
Ran 15 tests in 0.093s
OK
```

| Suite | Tests | Status |
|---|---:|---|
| TestBuild | 9 | all pass |
| TestWriteAndRead | 1 | pass |
| TestValidate | 5 | all pass |

Key assertions covered:
- Row count exactly 41 (no truncation, no inflation).
- Column schema exactly 8 fields in the documented order.
- Every prompt (name, lat, lon) appears in the output with 4-decimal fidelity.
- `is_master_district = True` for exactly 34 entries; `False` for exactly 7.
- Master-district validation reports zero missing.
- Extra non-master set equals `{Chiniot, Kot Addu, Murree, Nankana Sahib, Talagang, Taunsa, Wazirabad}`.
- No duplicate district names.
- CSV write+read roundtrip preserves field names and row count.

---

## 8. Step 3 — stop

Step 3 is complete. Files changed by this step:

- `processed/district_coordinates.csv` (new, 41 rows × 8 cols)
- `scripts/build_district_coordinates.py` (new)
- `tests/test_build_district_coordinates.py` (new, 15 tests, all pass)
- `reports/district_coordinate_validation_report.md` (this report, new)

No existing cleaned files were touched. `district_master_clean.csv` was
**read** for validation only (mtime unchanged).

Pipeline paused here for review — **Step 4 (Open-Meteo URL generator)
starts on your go**.