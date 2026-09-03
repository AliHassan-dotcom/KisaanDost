# Resume Blockers — Kisaan Dost

- **Generated:** 2026-08-31 (read-only inspection only; no files modified)
- **Inspection root:** `D:\KisaanDost` (skeleton) + `D:\KisaanDost\Kisaan_Dost_Data` (data)
- **Purpose:** Identify hard blockers and soft constraints before the next phase
  (NASA POWER weather ingestion + PBS/remote-sensing merge) begins.

## 1. Exact last completed step

**`scripts/validate_pbs_extracted_tables.py` — exit 0, all 37 checks passed
(2026-08-30 13:07 local time).**

That script validated the eight PBS Punjab Integrated Agricultural Census 2024
extracts produced by `scripts/extract_pbs_agricultural_census.py` earlier the same
day. It is the most recent action in the project's analysis pipeline. The
downstream output files it signed off on are:

| File | Rows | Status |
|---|---|---|
| `processed/pbs_farm_structure.csv` | 37 | final / validated |
| `processed/pbs_land_tenure.csv` | 37 | final / validated |
| `processed/pbs_irrigation.csv` | 37 | final / validated |
| `processed/pbs_crops.csv` | 703 | final / validated |
| `processed/pbs_machinery.csv` | 37 | final / validated |
| `processed/pbs_livestock.csv` | 333 | final / validated |
| `processed/pbs_modern_farming.csv` | 37 | final / validated |
| `processed/pbs_credit.csv` | 0 | intentionally empty (no district data published) |
| `processed/pbs_data_dictionary.csv` | 110 | reference |

The pipeline immediately before that produced the district-level remote-sensing
master (`processed/district_master_clean.csv`, 1,904 rows × 18 cols,
2022-01 to 2026-08, 34 districts) and the province-wide historical risk score
(`processed/Punjab_Monthly_Risk_Score_2022_2026.csv`, 56 rows × 45 cols).

Everything downstream of PBS extraction (weather ingestion, merge, ML, API,
UI) is **not yet started**.

---

## 2. Hard blockers (must resolve before any merge or weather ingestion)

### B1. District boundary GeoJSON is missing

- **Where needed:** `Kisaan_Dost_Data/Historical Data/*.json` are NASA POWER
  daily GeoJSONs with 117 point features on a ~1° grid across Punjab. To join
  them into `district_master_clean.csv`, each grid point must be assigned to one
  of 34 districts via a spatial join.
- **Why it blocks:** without district polygons (GeoJSON or shapefile), spatial
  aggregation from grid points to districts cannot be computed. Any alternative
  (nearest-district-centroid) is fragile and does not match the 34-district
  master's naming.
- **What is needed:** one GeoJSON (or shapefile) containing the 34 Punjab
  district polygons whose `district` name field matches the title-case names in
  `district_master_clean.csv` (e.g. "Attock District", "Lahore District").
- **Source candidates:** Pakistan Bureau of Statistics district boundary
  shapefiles, HDX Pakistan administrative boundaries, or Punjab IT Board GIS
  portal. Must be a license compatible with a hackathon demo (CC-BY / ODbL /
  public domain).

### B2. NASA POWER weather JSONs are not yet ingested

- **Files:** 12 GeoJSONs in `Kisaan_Dost_Data/Historical Data/`, covering
  2022-2025 × 3 parameters (`T2M`, `PRECTOTCORR`, `RH2M`). Each is daily data
  for the full calendar year at 117 point locations.
- **Not yet:** parsed, aggregated from daily to monthly, aggregated from grid
  points to districts, normalized to the `district_master_clean.csv` schema, or
  merged into it.
- **Dependency:** B1 must resolve first. Without district polygons, only a
  province-wide mean (mean of 117 points) is reproducible, which would match
  `Punjab_Monthly_*` but not `district_master_clean`.

### B3. PBS/remote-sensing final merge has not been performed

- **Status confirmed by user:** explicitly flagged as "not yet completed".
- **Inputs ready:** `district_master_clean.csv` (34 districts × 56 months) and
  the seven non-empty PBS CSVs (37 reporting units, including three extra units
  — Chiniot, Nankana Sahib, Cholistan Area — that are not in the 34-district
  master).
- **Join key:** `district` (title-case). A left-join on the 34-district master
  will automatically drop the three PBS-only units; they should be preserved as
  a province-context annex rather than silently dropped.
- **Dependency on B2:** the user's own instruction is that the merge must wait
  until the weather JSONs and boundary source are in. So B1 → B2 → B3 is the
  critical path.

---

## 3. Soft constraints (do not block, but must be decided before the merge)

### S1. ML model remains deferred

Per the saved project memory (`kisaan-dost-project-state.md`, 2026-08-29), the
rule-based risk score is the current scoring method and ML is deferred. The new
weather variables (T2M mean, PRECTOTCORR total, RH2M mean) will enrich the
rule-based score but do not change the decision to defer ML.

### S2. Scope of the weather join

Three design choices must be made before writing the ingestion script:

1. **Aggregation level.** Aggregate grid points to district-month, or keep
   province-month only? (District requires B1; province-only does not.)
2. **Temporal aggregation.** Daily → monthly means for T2M and RH2M; daily →
   monthly sum for PRECTOTCORR. Confirm units: mm/day vs mm total.
3. **Fill strategy.** If a district has no grid point inside its polygon, fall
   back to the nearest grid point, or leave it null?

### S3. Three census-only reporting units

PBS reports Chiniot District, Nankana Sahib District, and Cholistan Area, which
are absent from the 34-district remote-sensing master. Decision needed: keep
them as a separate `pbs_context_only.csv` (recommended), or drop them before
the merge.

### S4. `_tmp_annex.txt` and `_tmp_method.txt` (scratch files)

Two files at the data root are named `_tmp_*` and dated 2026-08-30. They are
almost certainly transient working notes from the PBS extraction session. Not a
blocker, but they should be either renamed to durable names or deleted before
the next phase begins — leaving `_tmp_` scratch files around risks accidental
overwrites.

### S5. Bash path ambiguity on this machine

Inspection observed that the Bash shell on this Windows machine resolves
`D:/Kisaan_Dost_Data` as if it were `D:/KisaanDost/Kisaan_Dost_Data` (a
nested copy exists inside the project). Python's `Path.resolve()` returns
different absolute paths for the two strings and `samefile()` is False, so
they are genuinely distinct directories. All new scripts should use Python
`Path.resolve()` or fully qualified Windows paths to avoid ambiguity. Not a
blocker for analysis, but a landmine for any future shell commands that touch
the data path.

### S6. Khanewal unirrigated_area blank in PBS Table 4.2

Census source printed `-` for Khanewal's unirrigated area; the extract
faithfully preserves a blank. Not a blocker — irrigated area is 99.1% of the
cultivated total — but any derived "percent irrigated" column must treat the
missing value as "approximately 0", not as zero.

---

## 4. Summary: what the next session should do

1. Source a 34-district Punjab GeoJSON (resolves B1).
2. Write a NASA POWER ingestion script that spatially joins daily grid values
   to district polygons and aggregates to district-month (resolves B2).
3. Validate the weather join against the existing temperature / rainfall /
   soil-moisture columns already in `district_master_clean.csv` (they were
   exported from GEE and serve as an independent cross-check on NASA POWER
   values).
4. Finalize the PBS/RS merge design (S2, S3) and produce one merged table.
5. Decide S4 (scratch files) and S5 (path hygiene) before any new scripts are
   written.

Until B1 is resolved, **no merge should happen**. The existing cleaned files
(`district_master_clean.csv`, `Punjab_Monthly_Risk_Score_2022_2026.csv`, all
`pbs_*.csv` files) remain the authoritative source of truth and must not be
overwritten.
