# PBS Punjab Integrated Agricultural Census 2024 — Extraction Quality Report

**Source:** IAC-Punjab-Report-25-05-2026-1-1_copy.pdf  
**Source size:** 26.8 MB, 288 pages  
**PDF type:** Native text (Microsoft Word for Microsoft 365, created 2026-05-25); no OCR required  
**Extraction date:** 2026-08-30  
**Script:** `scripts/extract_pbs_agricultural_census.py`  
**Validator:** `scripts/validate_pbs_extracted_tables.py` — exit code 0 (all checks passed)

---

## 1. Source Tables Extracted

| Census Table | Title | PDF Pages | Geographic Level | Rows in Output |
|---|---|---|---|---|
| 1.0 | Important Agricultural Census Items | 70–78 (9 pages) | District + Division + Province | Used as primary source for farm structure and crop areas |
| 1.1 | Number and Area of Farms (Acres) | 79 | District + Division + Province | Used for cross-check only |
| 1.3 | Tenure Classification of Farms and Farm Area | 81 | District + Division + Province | pbs_land_tenure.csv (37 rows) |
| 4.2 | Cultivated Area by Mode of Irrigation | 96 | District + Division + Province | pbs_irrigation.csv (37 rows) |
| 6.5 | Share of Different Crops Area | 129 | District + Division + Province | pbs_crops.csv (703 rows) |
| 6.19 | Farms Reporting Use of Green-House Technology (Tunnel Farming) | 145 | District + Division + Province | pbs_modern_farming.csv (37 rows) |
| 7.1 | Livestock Population by Administrative Unit | 147 | District + Division + Province | pbs_livestock.csv (333 rows) |
| 8.1 | Tractors by Type of Ownership | 250 | District + Division + Province | pbs_machinery.csv (37 rows) |
| 8.11 | Tubewells and Lift Pumps by Operating Power | 271 | District + Division + Province | pbs_machinery.csv (37 rows) |
| 8.16 | Use of Ploughing Implements for Land Operation | 276–277 | District + Division + Province | pbs_machinery.csv (implements_notes column) |

---

## 2. Output Files

| File | Rows | Columns | Coverage | Merge-safe for district advisory |
|---|---|---|---|---|
| pbs_farm_structure.csv | 37 | 9 | 36 districts + Cholistan Area | YES — join on district name |
| pbs_land_tenure.csv | 37 | 18 | 36 districts + Cholistan Area | YES |
| pbs_irrigation.csv | 37 | 21 | 36 districts + Cholistan Area | YES |
| pbs_crops.csv | 703 | 9 | 37 × 19 crop types | YES — 19 rows per district |
| pbs_machinery.csv | 37 | 22 | 36 districts + Cholistan Area | YES |
| pbs_livestock.csv | 333 | 6 | 37 × 9 animal types | YES — 9 rows per district |
| pbs_modern_farming.csv | 37 | 18 | 36 districts + Cholistan Area | YES |
| pbs_credit.csv | 0 | — | Intentionally empty | NOT APPLICABLE — see §5 |
| pbs_data_dictionary.csv | 110 | 6 | All output fields | Reference only |

---

## 3. District Coverage

**Census geography:** 36 districts across 9 divisions + Cholistan Area (special non-district unit within Bahawalpur Division). Total: 37 reporting units in all output CSVs.

**Master list alignment:** `district_master_clean.csv` contains 34 districts (title-case, e.g. "Bahawalnagar District"). Three units are present in the census but absent from the master:

| Unit | Reason absent from master |
|---|---|
| Chiniot District | Created after the remote-sensing master was defined (Faisalabad Division) |
| Nankana Sahib District | Created after the remote-sensing master was defined (Lahore Division) |
| Cholistan Area | Sub-area of Bahawalpur, not an administrative district |

All three are included in the output CSVs and flagged in the `notes` column. The district advisory system should handle them as context-only assets or drop them before merging with the 34-district master.

All 34 master districts are present in every output CSV with exact matching names.

---

## 4. Extraction Method and Known Challenges

### Text-layer extraction (no OCR)
The PDF embeds a native text layer (Word-generated). All values were read directly from the text layer using `pdfplumber`. Character-level coordinate extraction was used only for decoding column headers that are printed rotated 90° in Tables 4.2, 6.5, 8.11, and 8.16.

### Rotated column headers (Tables 4.2, 6.5, 8.11, 8.16)
These tables have their column headers printed vertically. `pdfplumber.extract_text()` returns them reversed or interleaved. Resolution: `page.chars` objects were extracted, filtered for non-upright characters, clustered by x0 coordinate (±12 px), and each cluster read bottom-to-top to recover the correct header text. Column order was verified against the census footnotes and cross-checked with Table 7.1 (livestock) and Table 8.1 (tractors).

### Split large numbers
The PDF text layer emits some 7-digit numbers as two adjacent word objects, e.g. `5` + `,050,236`. Fixed by `merge_number_fragments()`: adjacent words are merged when the gap is < 3.5 px, the first word is a numeric token, and the second word matches `(,\d{3})+` (a comma-leading continuation). The merged result must match `\d{1,3}(,\d{3})+`.

### Table 1.0 wide format (9 pages)
Table 1.0 uses a transposed layout across 9 division pages: administrative units are columns, census items are rows. The first column on each page contains column numbers (1–48 across all pages); a hardcoded map translates these to unit names. This parser handles the province page (column 1=PUNJAB, 2=Bahawalpur Division, 3–7=4 districts + Cholistan), six division pages (5–8 columns each), and the Sargodha division page (5 columns).

### Table 8.16 sub-row format
Each district block in Table 8.16 contains an "Owned" and "Rented" sub-row with 15 implement counts. A dedicated parser tracks the current unit name and assigns the "Owned" row values to that unit.

---

## 5. Missing Data and Limitations

### Agricultural credit (pbs_credit.csv is intentionally empty)
The census questionnaire (Form-2, Part-13) collected agricultural loan data — loan access, sources, and amounts. **No district-level credit table was published in the Punjab report.** The questionnaire pages appear on PDF pages 285–286 (Form-2) but contain no tabulated district data. `pbs_credit.csv` has a header row only and zero data rows, documenting this limitation explicitly.

### Sprinkler/drip/central pivot not published separately
Table 4.2 publishes a single combined column for "sprinkler + drip + central pivot" irrigated area. The census did not publish separate district-level counts or areas for each method. The combined area is carried in `pbs_irrigation.csv` (`sprinkler_drip_pivot_area`) and in `pbs_modern_farming.csv`. The `sprinkler`, `drip`, and `central_pivot` columns in `pbs_modern_farming.csv` are intentionally blank.

### Lift pump area not in Table 4.2
The census reports lift pump equipment counts in Table 8.11 but does not separately report area irrigated by lift pump in Table 4.2. The `lift_pump_area` column in `pbs_irrigation.csv` is blank for all districts.

### Khanewal District — unirrigated_area
Table 4.2 prints `-` (no value) for Khanewal's unirrigated area. The `unirrigated_area` field is blank in the output, preserving the source value. Khanewal's irrigated area (836,232 acres) accounts for 99.1% of cultivated area (843,405 acres); the remaining 7,173 acres are likely a reporting artefact rather than truly missing.

### Yak/Dzo/Dzomo — livestock counts
Table 7.1 lists Yak/Dzo/Dzomo as an animal type in the column header. No Punjab district reported any count; all 37 values are blank (`-` in source). This is expected — these animals are not farmed in the Punjab plains.

### Cholistan Area — average farm size
Table 1.0 reports average farm size as 14.6 acres for Cholistan Area, but no farm count was published separately for it in Table 1.0 page 70 (the Cholistan column shows only aggregate areas). The farm count (19,536) was read from the Bahawalpur division page; average farm size came from the same page.

---

## 6. Validation Results

Validator: `python scripts/validate_pbs_extracted_tables.py` → **exit code 0 (all passed)**

**Passed:** 37 checks  
**Info notes (acceptable known issues):** 4

| # | Issue | Category |
|---|---|---|
| 1 | Sum of cultivated_area across 37 rows = 29,644,854, expected 29,644,855 | Census source rounding (1 acre) |
| 2 | Tenure sub-type counts off by 1 in 10 districts | Census source rounding (1 farm unit) |
| 3 | Khanewal District unirrigated_area blank | Census reported '-' (no value) |
| 4 | Yak/Dzo/Dzomo count blank in all 37 districts | Species not present in Punjab |

---

## 7. Grand Total Cross-Checks

| Metric | Sum of 37 rows | Punjab Table 1.0 total | Match |
|---|---|---|---|
| Farm count | 5,050,236 | 5,050,236 | Exact |
| Total farm area (acres) | 31,039,972 | 31,039,972 | Exact |
| Cultivated area (acres) | 29,644,854 | 29,644,855 | Off by 1 (rounding) |

---

## 8. Tables Safe for District-Level Merging

All 8 data CSVs (excluding pbs_credit.csv) are safe for district-level merging against `district_master_clean.csv` using the `district` column. Use left-join on the 34-district master; the 3 extra rows (Chiniot, Nankana Sahib, Cholistan Area) will be excluded automatically.

## 9. Tables That Must Remain Separate Context Assets

| Table | Reason |
|---|---|
| pbs_credit.csv | No district data published; intentionally empty |
| Division-level and province-level rows (embedded in each CSV) | Not in master; excluded automatically when joining on district name |

---

## 10. Source Citation

Pakistan Bureau of Statistics (PBS). *Punjab Integrated Agricultural Census 2024*. Islamabad: PBS, 2026. Survey period: September–November 2024 + January–February 2025. Reference year: 2024. Two-stage mouza/block sampling, 15% margin of error at 95% CI, representative at district level.
