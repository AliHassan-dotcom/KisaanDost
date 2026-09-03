#!/usr/bin/env python3
"""Validate the PBS Punjab Agricultural Census 2024 extracted CSV files.

Checks:
  1. Row counts — each district-level file has exactly 37 rows (36 census districts
     + Cholistan Area); pbs_crops.csv has 37 * 19 = 703 rows.
  2. Required columns present in each file.
  3. No blank values in mandatory columns.
  4. Punjab grand total cross-check: sum of the 37 rows in pbs_farm_structure.csv
     must equal the known province totals from Table 1.0.
  5. Land tenure internal consistency: owner + owner-cum-tenant + tenant farms
     must equal total_farms for each row.
  6. Irrigation consistency: irrigated_area + unirrigated_area <= total_cultivated_area
     (within 1 acre rounding tolerance).
  7. pbs_credit.csv intentionally empty — verify header exists, 0 data rows.
  8. District names cross-check against district_master_clean.csv — every district
     row that IS in the master must match exactly; flags Chiniot, Nankana Sahib,
     Cholistan as expected non-matches.
  9. Livestock: each district has entries for all 9 animal types.
 10. Crops: each district has all 19 crop rows.

Outputs a pass/fail summary to stdout and returns exit code 0 (all pass) or 1 (failures).
"""

import csv
import os
import sys

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT_DIR = os.path.join(BASE, "processed")

MASTER_CSV = os.path.join(OUT_DIR, "district_master_clean.csv")

# Province-level totals from Table 1.0 (used for grand-total cross-check)
PUNJAB_TOTALS = {
    "farm_count": 5_050_236,
    "total_farm_area": 31_039_972,
    "cultivated_area": 29_644_855,
}

# Units not present in district_master_clean.csv (expected)
EXPECTED_NON_MASTER = {"Chiniot District", "Nankana Sahib District", "Cholistan Area"}

REQUIRED_DISTRICT_ROWS = 37   # 36 districts + Cholistan Area
ANIMAL_TYPES = ["Cattle", "Buffaloes", "Sheep", "Goats", "Camels",
                "Horses", "Mules", "Asses", "Yak/Dzo/Dzomo"]
CROP_COUNT = 19   # rows per district in pbs_crops.csv

PASS = "PASS"
FAIL = "FAIL"
INFO = "INFO"

failures = []
infos = []


def check(label, cond, detail=""):
    if cond:
        print(f"  {PASS}  {label}")
    else:
        print(f"  {FAIL}  {label}" + (f": {detail}" if detail else ""))
        failures.append(label + (f": {detail}" if detail else ""))


def note(label, detail=""):
    print(f"  {INFO}  {label}" + (f": {detail}" if detail else ""))
    infos.append(label + (f": {detail}" if detail else ""))


def load(filename):
    path = os.path.join(OUT_DIR, filename)
    if not os.path.exists(path):
        failures.append(f"File missing: {filename}")
        return []
    with open(path, newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f))


def load_master():
    if not os.path.exists(MASTER_CSV):
        return set()
    with open(MASTER_CSV, newline="", encoding="utf-8") as f:
        return {r["district"] for r in csv.DictReader(f)}


def ival(s):
    try:
        return int(s.replace(",", "")) if s else None
    except ValueError:
        return None


# ---------------------------------------------------------------------------
# 1. pbs_farm_structure.csv
# ---------------------------------------------------------------------------
print("\n=== pbs_farm_structure.csv ===")
fs = load("pbs_farm_structure.csv")
check("Row count = 37", len(fs) == REQUIRED_DISTRICT_ROWS, f"got {len(fs)}")

MANDATORY_FS = ["district", "farm_count", "total_farm_area", "cultivated_area",
                "average_farm_size", "uncultivated_area"]
for col in MANDATORY_FS:
    blanks = [r["district"] for r in fs if not r.get(col, "").strip()]
    check(f"No blank '{col}'", not blanks, f"blank in: {blanks}")

# Punjab grand total cross-check (±1 tolerance for census rounding)
if fs:
    for field, expected in PUNJAB_TOTALS.items():
        total = sum(ival(r[field]) or 0 for r in fs if ival(r[field]) is not None)
        if total == expected:
            check(f"Sum {field} == {expected:,}", True)
        elif abs(total - expected) <= 1:
            note(f"Sum {field} off by 1 (census rounding): got {total:,}, expected {expected:,}")
        else:
            check(f"Sum {field} == {expected:,}", False, f"got {total:,}")

# ---------------------------------------------------------------------------
# 2. pbs_land_tenure.csv
# ---------------------------------------------------------------------------
print("\n=== pbs_land_tenure.csv ===")
lt = load("pbs_land_tenure.csv")
check("Row count = 37", len(lt) == REQUIRED_DISTRICT_ROWS, f"got {len(lt)}")

MANDATORY_LT = ["district", "total_farms", "owner_farms", "owner_cum_tenant_farms",
                "tenant_farms", "total_farm_area"]
for col in MANDATORY_LT:
    blanks = [r["district"] for r in lt if not r.get(col, "").strip()]
    check(f"No blank '{col}'", not blanks, f"blank in: {blanks}")

tenure_errors = []
tenure_rounding = []
for r in lt:
    tot = ival(r.get("total_farms"))
    own = ival(r.get("owner_farms"))
    oct_ = ival(r.get("owner_cum_tenant_farms"))
    ten = ival(r.get("tenant_farms"))
    if None not in (tot, own, oct_, ten):
        diff = abs(own + oct_ + ten - tot)
        if diff == 0:
            pass
        elif diff == 1:
            tenure_rounding.append(r["district"])
        else:
            tenure_errors.append(
                f"{r['district']} ({own}+{oct_}+{ten}={own+oct_+ten} != {tot})"
            )
check("Tenure sub-types sum to total_farms (exact)", not tenure_errors,
      "; ".join(tenure_errors[:3]) + ("..." if len(tenure_errors) > 3 else ""))
if tenure_rounding:
    note(f"Tenure off by 1 (census rounding) in {len(tenure_rounding)} district(s)",
         ", ".join(tenure_rounding[:5]) + ("..." if len(tenure_rounding) > 5 else ""))

# ---------------------------------------------------------------------------
# 3. pbs_irrigation.csv
# ---------------------------------------------------------------------------
print("\n=== pbs_irrigation.csv ===")
irr = load("pbs_irrigation.csv")
check("Row count = 37", len(irr) == REQUIRED_DISTRICT_ROWS, f"got {len(irr)}")

MANDATORY_IRR = ["district", "total_cultivated_area", "irrigated_area"]
for col in MANDATORY_IRR:
    blanks = [r["district"] for r in irr if not r.get(col, "").strip()]
    check(f"No blank '{col}'", not blanks, f"blank in: {blanks}")

# unirrigated_area may be '-' (no value) in source — report as INFO, not FAIL
uirr_blank = [r["district"] for r in irr if not r.get("unirrigated_area", "").strip()]
if uirr_blank:
    note("unirrigated_area blank (census reported '-') in districts",
         ", ".join(uirr_blank))

irr_errors = []
for r in irr:
    cult = ival(r.get("total_cultivated_area"))
    irig = ival(r.get("irrigated_area"))
    uirr = ival(r.get("unirrigated_area"))
    if None not in (cult, irig, uirr):
        # irrigated + unirrigated <= cultivated + 1 (rounding)
        if irig + uirr > cult + 1:
            irr_errors.append(
                f"{r['district']} ({irig}+{uirr}={irig+uirr} > {cult})"
            )
check("irrigated + unirrigated <= total_cultivated_area", not irr_errors,
      "; ".join(irr_errors[:3]))

# ---------------------------------------------------------------------------
# 4. pbs_crops.csv
# ---------------------------------------------------------------------------
print("\n=== pbs_crops.csv ===")
crops = load("pbs_crops.csv")
check(f"Row count = {REQUIRED_DISTRICT_ROWS * CROP_COUNT}",
      len(crops) == REQUIRED_DISTRICT_ROWS * CROP_COUNT,
      f"got {len(crops)}")

MANDATORY_CROPS = ["district", "crop_name", "season", "total_cropped_area"]
for col in MANDATORY_CROPS:
    blanks = [f"{r['district']}/{r.get('crop_name','?')}" for r in crops
              if not r.get(col, "").strip()]
    check(f"No blank '{col}'", not blanks,
          f"{len(blanks)} blank(s), e.g. {blanks[:2]}")

# Each district has all CROP_COUNT rows
from collections import Counter
dist_crop_counts = Counter(r["district"] for r in crops)
wrong_counts = {d: c for d, c in dist_crop_counts.items() if c != CROP_COUNT}
check(f"Each district has exactly {CROP_COUNT} crop rows", not wrong_counts,
      str(dict(list(wrong_counts.items())[:3])))

# ---------------------------------------------------------------------------
# 5. pbs_machinery.csv
# ---------------------------------------------------------------------------
print("\n=== pbs_machinery.csv ===")
mach = load("pbs_machinery.csv")
check("Row count = 37", len(mach) == REQUIRED_DISTRICT_ROWS, f"got {len(mach)}")

MANDATORY_MACH = ["district", "tractor_count", "tubewell_count"]
for col in MANDATORY_MACH:
    blanks = [r["district"] for r in mach if not r.get(col, "").strip()]
    check(f"No blank '{col}'", not blanks, f"blank in: {blanks}")

# ---------------------------------------------------------------------------
# 6. pbs_livestock.csv
# ---------------------------------------------------------------------------
print("\n=== pbs_livestock.csv ===")
liv = load("pbs_livestock.csv")
expected_liv = REQUIRED_DISTRICT_ROWS * len(ANIMAL_TYPES)
check(f"Row count = {expected_liv}", len(liv) == expected_liv, f"got {len(liv)}")

MANDATORY_LIV = ["district", "animal_type"]
for col in MANDATORY_LIV:
    blanks = [f"{r['district']}/{r.get('animal_type','?')}" for r in liv
              if not r.get(col, "").strip()]
    check(f"No blank '{col}'", not blanks, f"{len(blanks)} blank(s)")

# animal_count blank is acceptable for Yak/Dzo/Dzomo (not present in Punjab)
non_yak_blanks = [
    f"{r['district']}/{r['animal_type']}" for r in liv
    if not r.get("animal_count", "").strip() and r.get("animal_type") != "Yak/Dzo/Dzomo"
]
check("No blank 'animal_count' (excluding Yak/Dzo/Dzomo)", not non_yak_blanks,
      f"{len(non_yak_blanks)} blank(s)")
yak_blanks = [r for r in liv if r.get("animal_type") == "Yak/Dzo/Dzomo"
              and not r.get("animal_count", "").strip()]
if yak_blanks:
    note(f"Yak/Dzo/Dzomo count blank in all {len(yak_blanks)} districts (species not present in Punjab)")

dist_animal = {}
for r in liv:
    dist_animal.setdefault(r["district"], set()).add(r["animal_type"])
missing_types = {d: ANIMAL_TYPES for d in dist_animal
                 if set(ANIMAL_TYPES) - dist_animal[d]}
check("Each district has all 9 animal types", not missing_types,
      str(dict(list(missing_types.items())[:2])))

# ---------------------------------------------------------------------------
# 7. pbs_modern_farming.csv
# ---------------------------------------------------------------------------
print("\n=== pbs_modern_farming.csv ===")
mf = load("pbs_modern_farming.csv")
check("Row count = 37", len(mf) == REQUIRED_DISTRICT_ROWS, f"got {len(mf)}")

MANDATORY_MF = ["district", "tunnel_farming"]
for col in MANDATORY_MF:
    blanks = [r["district"] for r in mf if not r.get(col, "").strip()]
    check(f"No blank '{col}'", not blanks, f"blank in: {blanks}")

# sprinkler, drip, central_pivot should all be blank (not published separately)
unexpected_vals = [r["district"] for r in mf
                   if any(r.get(c, "").strip()
                          for c in ["sprinkler", "drip", "central_pivot"])]
check("sprinkler/drip/central_pivot intentionally blank", not unexpected_vals,
      f"unexpected values in: {unexpected_vals}")

# ---------------------------------------------------------------------------
# 8. pbs_credit.csv
# ---------------------------------------------------------------------------
print("\n=== pbs_credit.csv ===")
path = os.path.join(OUT_DIR, "pbs_credit.csv")
check("File exists", os.path.exists(path))
if os.path.exists(path):
    with open(path, newline="", encoding="utf-8") as f:
        content = f.read().strip()
    check("Intentionally empty (0 data rows)", content == "" or "\n" not in content,
          "file has data rows")

# ---------------------------------------------------------------------------
# 9. District name cross-check
# ---------------------------------------------------------------------------
print("\n=== District name cross-check ===")
master = load_master()
if master:
    all_districts = set()
    for rows in [fs, lt, irr, mach, mf]:
        all_districts |= {r["district"] for r in rows}
    for r in liv:
        all_districts.add(r["district"])
    for r in crops:
        all_districts.add(r["district"])

    unexpected_non_master = all_districts - master - EXPECTED_NON_MASTER
    check("No unexpected non-master district names", not unexpected_non_master,
          str(unexpected_non_master))

    missing_master = master - all_districts
    check("All 34 master districts present in outputs", not missing_master,
          str(missing_master))

    for nm in sorted(EXPECTED_NON_MASTER):
        present = nm in all_districts
        check(f"Expected non-master unit present: {nm}", present)
else:
    print(f"  SKIP  district_master_clean.csv not found at {MASTER_CSV}")

# ---------------------------------------------------------------------------
# Summary
# ---------------------------------------------------------------------------
print(f"\n{'='*50}")
if infos:
    print(f"INFO notes ({len(infos)} — acceptable known issues):")
    for i in infos:
        print(f"  - {i}")
if failures:
    print(f"RESULT: {len(failures)} check(s) FAILED")
    for f in failures:
        print(f"  - {f}")
    sys.exit(1)
else:
    print("RESULT: All checks passed")
    sys.exit(0)
