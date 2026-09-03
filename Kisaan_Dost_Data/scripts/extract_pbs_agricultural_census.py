#!/usr/bin/env python3
"""Extract district-level tables from the PBS Punjab Integrated Agricultural Census 2024 PDF.

Source: District data/IAC-Punjab-Report-25-05-2026-1-1_copy.pdf
        (Agricultural Census 2024 - Punjab Report, PBS, 288 pages, native text layer)

Outputs (processed/):
  pbs_farm_structure.csv, pbs_land_tenure.csv, pbs_irrigation.csv, pbs_crops.csv,
  pbs_machinery.csv, pbs_livestock.csv, pbs_credit.csv, pbs_modern_farming.csv,
  pbs_data_dictionary.csv

Extraction method: pdfplumber text-layer parsing (no OCR). Column headers printed
vertically (rotated 90 degrees) in Tables 4.2 / 6.5 / 8.11 / 8.16 were decoded from
character coordinates during development and are hard-coded here as column names.
The PDF text layer splits some large numbers into two words (e.g. '5' + ',050,236');
adjacent numeric fragments are re-merged before parsing.
"""

import csv
import io
import os
import re
import sys

try:
    import pdfplumber
except ImportError:
    sys.exit("pdfplumber is required: pip install pdfplumber")

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PDF_PATH = os.path.join(BASE, "District data", "IAC-Punjab-Report-25-05-2026-1-1_copy.pdf")
OUT_DIR = os.path.join(BASE, "processed")
MASTER_CSV = os.path.join(OUT_DIR, "district_master_clean.csv")

SOURCE_YEAR = "2024"
STD_FOOTNOTE = 'Report footnote: "0" = value less than 0.5; "-" = no value'

# ---------------------------------------------------------------------------
# Census administrative structure (from Table 1.1 / Table 1.0 column numbering)
# ---------------------------------------------------------------------------

DIVISION_DISTRICTS = [
    ("BAHAWALPUR DIVISION", ["BAHAWALNAGAR", "BAHAWALPUR", "RAHIM YAR KHAN", "CHOLISTAN AREA"]),
    ("DERA GHAZI KHAN DIVISION", ["DERA GHAZI KHAN", "LAYYAH", "MUZAFFARGARH", "RAJANPUR"]),
    ("FAISALABAD DIVISION", ["CHINIOT", "FAISALABAD", "JHANG", "TOBA TEK SINGH"]),
    ("GUJRANWALA DIVISION", ["GUJRANWALA", "GUJRAT", "HAFIZABAD", "MANDI BAHAUDDIN", "NAROWAL", "SIALKOT"]),
    ("LAHORE DIVISION", ["KASUR", "LAHORE", "NANKANA SAHIB", "SHEIKHUPURA"]),
    ("MULTAN DIVISION", ["KHANEWAL", "LODHRAN", "MULTAN", "VEHARI"]),
    ("RAWALPINDI DIVISION", ["ATTOCK", "CHAKWAL", "JHELUM", "RAWALPINDI"]),
    ("SAHIWAL DIVISION", ["OKARA", "PAKPATTAN", "SAHIWAL"]),
    ("SARGODHA DIVISION", ["BHAKKAR", "KHUSHAB", "MIANWALI", "SARGODHA"]),
]

DISTRICT_KEYS = []      # census row keys, e.g. 'BAHAWALNAGAR DISTRICT'
SPECIAL_KEYS = []       # 'CHOLISTAN AREA'
for _div, _dists in DIVISION_DISTRICTS:
    for _d in _dists:
        if _d == "CHOLISTAN AREA":
            SPECIAL_KEYS.append(_d)
        else:
            DISTRICT_KEYS.append(_d + " DISTRICT")
ROW_KEYS = DISTRICT_KEYS + SPECIAL_KEYS   # 37 rows written to CSVs

TABLE_1_0_PAGES = list(range(69, 78))     # PDF page indices 69..77 (pages 70..78)
TABLE_1_0_COL_UNITS = {                    # column number in Table 1.0 -> unit key
    2: "PUNJAB",
    3: "BAHAWALPUR DIVISION", 4: "BAHAWALNAGAR DISTRICT", 5: "BAHAWALPUR DISTRICT",
    6: "RAHIM YAR KHAN DISTRICT", 7: "CHOLISTAN AREA",
    8: "DERA GHAZI KHAN DIVISION", 9: "DERA GHAZI KHAN DISTRICT", 10: "LAYYAH DISTRICT",
    11: "MUZAFFARGARH DISTRICT", 12: "RAJANPUR DISTRICT",
    13: "FAISALABAD DIVISION", 14: "CHINIOT DISTRICT", 15: "FAISALABAD DISTRICT",
    16: "JHANG DISTRICT", 17: "TOBA TEK SINGH DISTRICT",
    18: "GUJRANWALA DIVISION", 19: "GUJRANWALA DISTRICT", 20: "GUJRAT DISTRICT",
    21: "HAFIZABAD DISTRICT", 22: "MANDI BAHAUDDIN DISTRICT", 23: "NAROWAL DISTRICT",
    24: "SIALKOT DISTRICT",
    25: "LAHORE DIVISION", 26: "KASUR DISTRICT", 27: "LAHORE DISTRICT",
    28: "NANKANA SAHIB DISTRICT", 29: "SHEIKHUPURA DISTRICT",
    30: "MULTAN DIVISION", 31: "KHANEWAL DISTRICT", 32: "LODHRAN DISTRICT",
    33: "MULTAN DISTRICT", 34: "VEHARI DISTRICT",
    35: "RAWALPINDI DIVISION", 36: "ATTOCK DISTRICT", 37: "CHAKWAL DISTRICT",
    38: "JHELUM DISTRICT", 39: "RAWALPINDI DISTRICT",
    40: "SAHIWAL DIVISION", 41: "OKARA DISTRICT", 42: "PAKPATTAN DISTRICT",
    43: "SAHIWAL DISTRICT",
    44: "SARGODHA DIVISION", 45: "BHAKKAR DISTRICT", 46: "KHUSHAB DISTRICT",
    47: "MIANWALI DISTRICT", 48: "SARGODHA DISTRICT",
}

TABLE_1_0_ITEMS = {
    "Number of Farms": "farm_count",
    "Farm Area": "farm_area",
    "Cultivated Area": "cultivated_area",
    "Average Farm Size": "average_farm_size",
    "Uncultivated Area": "uncultivated_area",
    "Cropped Area": "cropped_area",
    "Kharif Crops Area": "kharif_area",
    "Rabi Crops Area": "rabi_area",
    "Orchard Area": "orchard_area",
    "Wheat Area": "wheat_area",
    "Rice Area": "rice_area",
    "Cotton Area": "cotton_area",
    "Sugarcane Area": "sugarcane_area",
    "Maize Area": "maize_area",
    "Fodder Area": "fodder_area",
}

# Table 6.5 crop share columns (rotated header decoded from character coordinates)
CROP_SHARE_COLS = [
    ("wheat_share", "Wheat"),
    ("rice_share", "Rice/Paddy"),
    ("maize_rabi_share", "Maize (Rabi)"),
    ("maize_kharif_share", "Maize (Kharif)"),
    ("jowar_bajra_gram_share", "Jowar/Bajra/Gram"),
    ("barley_share", "Barley"),
    ("cotton_share", "Cotton"),
    ("sugarcane_share", "Sugarcane"),
    ("tobacco_share", "Tobacco"),
    ("oilseeds_share", "Oilseeds"),
    ("pulses_share", "Pulses"),
    ("fodders_share", "Fodders"),
    ("vegetables_share", "Vegetables"),
    ("orchards_share", "Orchards"),
    ("other_crops_share", "Other Crops"),
]

CROP_SEASON = {
    "Wheat": "Rabi",
    "Rice/Paddy": "Kharif",
    "Maize (Rabi)": "Rabi",
    "Maize (Kharif)": "Kharif",
    "Maize (Total)": "Kharif+Rabi",
    "Jowar/Bajra/Gram": "Kharif+Rabi",
    "Barley": "Rabi",
    "Cotton": "Kharif",
    "Sugarcane": "Kharif+Rabi",
    "Tobacco": "Rabi",
    "Oilseeds": "Kharif+Rabi",
    "Pulses": "Kharif+Rabi",
    "Fodders": "Kharif+Rabi",
    "Vegetables": "Kharif+Rabi",
    "Orchards": "Kharif+Rabi",
    "Other Crops": "Kharif+Rabi",
    "Kharif Crops (Total)": "Kharif",
    "Rabi Crops (Total)": "Rabi",
    "Total Cropped Area": "Kharif+Rabi",
}

# Table 1.0 area item -> crop row name in pbs_crops.csv
CROP_AREA_SOURCE = {
    "Wheat": "wheat_area",
    "Rice/Paddy": "rice_area",
    "Cotton": "cotton_area",
    "Sugarcane": "sugarcane_area",
    "Fodders": "fodder_area",
    "Orchards": "orchard_area",
}

IMPLEMENT_COLS = [   # Table 8.16 (rotated headers decoded from coordinates)
    "cultivator", "front_back_blade", "laser_leveler", "mould_board_plough",
    "disk_plough", "chisel_plough", "sub_soiler", "ridger", "power_tiller",
    "puddler", "rotavator", "disk_harrow", "sugarcane_bud_cutter",
    "sugarcane_stubble_shaver", "rice_straw_baler_shredder",
]

LIVESTOCK_TYPES = [
    ("cattle", "Cattle"), ("buffaloes", "Buffaloes"), ("sheep", "Sheep"),
    ("goats", "Goats"), ("camels", "Camels"), ("horses", "Horses"),
    ("mules", "Mules"), ("asses", "Asses"), ("yak_dzo_dzomo", "Yak/Dzo/Dzomo"),
]

WARNINGS = []


def warn(msg):
    WARNINGS.append(msg)
    print(f"  WARNING: {msg}")


# ---------------------------------------------------------------------------
# Low-level PDF parsing helpers
# ---------------------------------------------------------------------------

def cluster_rows(words, tol=4.0):
    rows = []
    for w in sorted(words, key=lambda w: (w["top"], w["x0"])):
        if rows and abs(w["top"] - rows[-1][0]["top"]) <= tol:
            rows[-1].append(w)
        else:
            rows.append([w])
    return [sorted(r, key=lambda w: w["x0"]) for r in rows]


def is_numeric_token(t):
    return bool(re.fullmatch(r"\d[\d,]*(\.\d+)?", t)) or t == "-"


def merge_number_fragments(row_words, gap=3.5):
    """Re-join numbers the PDF text layer splits into two words ('5' + ',050,236')."""
    out = []
    for w in row_words:
        if out:
            prev = out[-1]
            gap_px = w["x0"] - prev["x1"]
            merged = prev["text"] + w["text"]
            second_is_continuation = re.fullmatch(r"(,\d{3})+", w["text"]) is not None
            if (
                gap_px < gap
                and is_numeric_token(prev["text"])
                and (is_numeric_token(w["text"]) or second_is_continuation)
                and re.fullmatch(r"\d{1,3}(,\d{3})+|\d+\.\d+", merged)
            ):
                merged_w = dict(prev)
                merged_w["text"] = merged
                merged_w["x1"] = w["x1"]
                out[-1] = merged_w
                continue
        out.append(w)
    return out


def clean_unit(tokens):
    s = " ".join(tokens)
    return s.replace("GERA GHAZI KHAN", "DERA GHAZI KHAN").strip()


def unit_kind(unit):
    if unit == "PUNJAB":
        return "province"
    if unit.endswith("DIVISION"):
        return "division"
    if unit == "CHOLISTAN AREA":
        return "special"
    if unit.endswith("DISTRICT"):
        return "district"
    return "other"


def display_name(unit):
    if unit_kind(unit) == "division":
        return unit[: -len(" DIVISION")].title() + " Division"
    if unit == "CHOLISTAN AREA":
        return "Cholistan Area"
    if unit.endswith("DISTRICT"):
        return unit[: -len(" DISTRICT")].title() + " District"
    return unit.title()


def norm_value(raw):
    """'-' -> '' (no value); strip thousands separators otherwise."""
    if raw is None:
        return ""
    raw = raw.strip()
    if raw == "-" or raw == "":
        return ""
    return raw.replace(",", "")


def find_number_row(rows):
    for r in rows:
        toks = [w["text"] for w in r]
        if len(toks) >= 3 and all(re.fullmatch(r"\d+", t) for t in toks):
            return r
    return None


def parse_standard_table(pdf, page_idx, n_cols, label):
    """Parse a page where each unit row is 'UNIT NAME v1 v2 ... v{n_cols-1}'.

    Returns {unit_key: [value strings in column order]}.
    """
    page = pdf.pages[page_idx]
    rows = cluster_rows(page.extract_words())
    numrow = find_number_row(rows)
    if numrow is None:
        raise RuntimeError(f"{label}: column-number row not found on PDF page {page_idx + 1}")
    ncol = len(numrow)
    if ncol != n_cols:
        raise RuntimeError(
            f"{label}: expected {n_cols} columns, found {ncol} on PDF page {page_idx + 1}"
        )
    centers = [(w["x0"] + w["x1"]) / 2.0 for w in numrow]

    data = {}
    for r in rows:
        if r is numrow:
            continue
        rw = merge_number_fragments(r)
        name_toks, vals = [], []
        for w in rw:
            t = w["text"]
            if not vals and re.fullmatch(r"[A-Z()\\/&.,'\-]+", t) and not re.fullmatch(r"\d+", t):
                name_toks.append(t)
            else:
                vals.append(w)
        if not name_toks or not vals:
            continue
        unit = clean_unit(name_toks)
        kind = unit_kind(unit)
        if kind not in ("province", "division", "district", "special"):
            continue
        texts = [w["text"] for w in vals]
        if len(texts) == n_cols - 1:
            values = texts                       # sequential: x-order == column order
        else:
            # fall back to nearest-column-centre assignment
            bycol = {}
            for w in vals:
                c = (w["x0"] + w["x1"]) / 2.0
                ci = min(range(1, n_cols), key=lambda i: abs(c - centers[i]))
                bycol.setdefault(ci, []).append(w["text"])
            values = ["".join(bycol.get(i, [""])) for i in range(1, n_cols)]
            warn(
                f"{label}: row '{unit}' has {len(texts)} value tokens "
                f"(expected {n_cols - 1}); assigned by x-position"
            )
        if unit in data:
            warn(f"{label}: duplicate row for '{unit}'")
        data[unit] = values
    return data


def parse_table_1_0(pdf):
    """Table 1.0 spans 9 division pages; units are columns, census items are rows."""
    data = {u: {} for u in TABLE_1_0_COL_UNITS.values()}
    seen_items = set()
    for page_idx in TABLE_1_0_PAGES:
        page = pdf.pages[page_idx]
        rows = cluster_rows(page.extract_words())
        numrow = find_number_row(rows)
        if numrow is None:
            raise RuntimeError(f"Table 1.0: number row not found on PDF page {page_idx + 1}")
        col_numbers = [int(w["text"]) for w in numrow]
        units = [TABLE_1_0_COL_UNITS[n] for n in col_numbers if n != 1]
        if len(units) != len(col_numbers) - 1:
            raise RuntimeError(f"Table 1.0: unknown column number on page {page_idx + 1}")
        for r in rows:
            if r is numrow:
                continue
            rw = merge_number_fragments(r)
            label_toks, vals = [], []
            for w in rw:
                t = w["text"]
                if not vals and re.fullmatch(r"[A-Za-z()&%'\-]+", t):
                    label_toks.append(t)
                else:
                    vals.append(w)
            item = " ".join(label_toks)
            if item not in TABLE_1_0_ITEMS or not vals:
                continue
            texts = [w["text"] for w in vals]
            if len(texts) != len(units):
                warn(
                    f"Table 1.0 page {page_idx + 1}: item '{item}' has {len(texts)} values, "
                    f"expected {len(units)}"
                )
                continue
            key = TABLE_1_0_ITEMS[item]
            seen_items.add(item)
            for unit, v in zip(units, texts):
                data[unit][key] = v
    missing = [i for i in TABLE_1_0_ITEMS if i not in seen_items]
    if missing:
        warn(f"Table 1.0: items not found: {missing}")
    return data


def parse_table_8_16(pdf):
    """Table 8.16: unit row followed by 'Owned'/'Rented' rows with 15 implement counts."""
    data = {}
    current = None
    for page_idx in (275, 276):
        page = pdf.pages[page_idx]
        rows = cluster_rows(page.extract_words())
        numrow = find_number_row(rows)
        for r in rows:
            if r is numrow:
                continue
            rw = merge_number_fragments(r)
            toks = [w["text"] for w in rw]
            if not toks:
                continue
            if toks[0] in ("Owned", "Rented") and len(toks) == 16:
                if current is None:
                    warn("Table 8.16: Owned/Rented row before any unit row")
                    continue
                kind = toks[0].lower()
                if kind == "owned":
                    data[current] = toks[1:]
                continue
            name_toks, vals = [], []
            for w in rw:
                t = w["text"]
                if not vals and re.fullmatch(r"[A-Z()\\/&.,'\-]+", t) and not re.fullmatch(r"\d+", t):
                    name_toks.append(t)
                else:
                    vals.append(w)
            if name_toks and not vals:
                unit = clean_unit(name_toks)
                if unit_kind(unit) in ("province", "division", "district", "special"):
                    current = unit
    return data


# ---------------------------------------------------------------------------
# CSV writing helpers
# ---------------------------------------------------------------------------

def write_csv(path, header, rows):
    with io.open(path, "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(header)
        w.writerows(rows)
    print(f"  wrote {os.path.basename(path)} ({len(rows)} rows)")


def master_district_set():
    with io.open(MASTER_CSV, encoding="utf-8-sig") as f:
        return set(r["district"] for r in csv.DictReader(f))


def unit_flags(unit, master):
    """Standard per-row notes flags."""
    name = display_name(unit)
    flags = []
    if unit == "CHOLISTAN AREA":
        flags.append(
            "Cholistan Area is a separate non-district reporting unit within "
            "Bahawalpur Division; not present in district_master_clean.csv"
        )
    elif name not in master:
        flags.append(
            f"{name} is not present in district_master_clean.csv "
            "(remote-sensing master covers 34 districts)"
        )
    return flags


# ---------------------------------------------------------------------------
# Main extraction
# ---------------------------------------------------------------------------

def main():
    os.makedirs(OUT_DIR, exist_ok=True)
    master = master_district_set()
    print(f"Opening {PDF_PATH}")
    pdf = pdfplumber.open(PDF_PATH)

    print("Parsing Table 1.0 (Important Agricultural Census Items, 9 division pages)")
    t10 = parse_table_1_0(pdf)
    print(f"  units parsed: {len([u for u in t10 if t10[u]])}")

    print("Parsing Table 1.1 (Number and Area of Farms)")
    t11 = parse_standard_table(pdf, 78, 8, "Table 1.1")
    print("Parsing Table 1.3 (Tenure Classification of Farms and Farm Area)")
    t13 = parse_standard_table(pdf, 80, 17, "Table 1.3")
    print("Parsing Table 4.2 (Cultivated Area by Mode of Irrigation)")
    t42 = parse_standard_table(pdf, 95, 15, "Table 4.2")
    print("Parsing Table 6.5 (Share of Different Crops Area)")
    t65 = parse_standard_table(pdf, 128, 17, "Table 6.5")
    print("Parsing Table 6.19 (Tunnel Farming)")
    t619 = parse_standard_table(pdf, 144, 11, "Table 6.19")
    print("Parsing Table 7.1 (Livestock Population)")
    t71 = parse_standard_table(pdf, 146, 10, "Table 7.1")
    print("Parsing Table 8.1 (Tractors by Type of Ownership)")
    t81 = parse_standard_table(pdf, 249, 5, "Table 8.1")
    print("Parsing Table 8.11 (Tubewells and Lift Pumps by Operating Power)")
    t811 = parse_standard_table(pdf, 270, 14, "Table 8.11")
    print("Parsing Table 8.16 (Use of Ploughing Implements)")
    t816 = parse_table_8_16(pdf)
    pdf.close()

    # -- completeness of every table across all 47 reporting units -------------
    for name, tbl in [("1.0", t10), ("1.1", t11), ("1.3", t13), ("4.2", t42),
                      ("6.5", t65), ("6.19", t619), ("7.1", t71), ("8.1", t81),
                      ("8.11", t811), ("8.16", t816)]:
        have = set(tbl.keys())
        expected = {"PUNJAB"} | {d for d, _ in DIVISION_DISTRICTS} | set(ROW_KEYS)
        missing = expected - have
        if missing:
            warn(f"Table {name}: missing rows for {sorted(missing)}")

    # -- cross-check Table 1.0 vs Table 1.1 ------------------------------------
    # Table 1.1 column layout: col2=farm_count(idx0), col3=pct(idx1),
    #   col4=farm_area(idx2), col5=pct(idx3), col6=cultivated_area(idx4),
    #   col7=pct(idx5), col8=cultivated_as_pct_farm_area(idx6)
    for unit in ROW_KEYS:
        a, b = t10.get(unit, {}), t11.get(unit, [])
        if len(b) >= 5:
            for key, idx in (("farm_count", 0), ("farm_area", 2), ("cultivated_area", 4)):
                v10, v11 = norm_value(a.get(key, "")), norm_value(b[idx])
                if v10 != v11:
                    warn(f"Table 1.0 vs 1.1 mismatch for {unit} {key}: {v10} vs {v11}")

    # -------------------------------------------------------------------
    # 1. pbs_farm_structure.csv
    # -------------------------------------------------------------------
    header = ["district", "farm_count", "total_farm_area", "cultivated_area",
              "average_farm_size", "uncultivated_area", "source_year",
              "source_table", "notes"]
    rows = []
    for unit in ROW_KEYS:
        d = t10.get(unit, {})
        notes = list(unit_flags(unit, master))
        notes.append("Farms are agricultural holdings, not farmer or household counts")
        notes.append(STD_FOOTNOTE)
        rows.append([
            display_name(unit), norm_value(d.get("farm_count")),
            norm_value(d.get("farm_area")), norm_value(d.get("cultivated_area")),
            norm_value(d.get("average_farm_size")), norm_value(d.get("uncultivated_area")),
            SOURCE_YEAR, "Tables 1.0, 1.1", "; ".join(notes),
        ])
    write_csv(os.path.join(OUT_DIR, "pbs_farm_structure.csv"), header, rows)

    # -------------------------------------------------------------------
    # 2. pbs_land_tenure.csv
    # -------------------------------------------------------------------
    header = ["district", "total_farms", "owner_farms", "owner_cum_tenant_farms",
              "tenant_farms", "owner_farms_percent", "owner_cum_tenant_farms_percent",
              "tenant_farms_percent", "total_farm_area", "owner_farm_area",
              "owner_cum_tenant_farm_area", "tenant_farm_area", "owner_area_percent",
              "owner_cum_tenant_area_percent", "tenant_area_percent",
              "source_year", "source_table", "notes"]
    rows = []
    for unit in ROW_KEYS:
        v = t13.get(unit, [""] * 16)
        notes = list(unit_flags(unit, master))
        notes.append("Percentages are of farms (cols 6-8) and of farm area (cols 14-16), as reported")
        notes.append(STD_FOOTNOTE)
        rows.append([
            display_name(unit),
            norm_value(v[0]), norm_value(v[2]), norm_value(v[4]), norm_value(v[6]),
            norm_value(v[3]), norm_value(v[5]), norm_value(v[7]),
            norm_value(v[8]), norm_value(v[10]), norm_value(v[12]), norm_value(v[14]),
            norm_value(v[11]), norm_value(v[13]), norm_value(v[15]),
            SOURCE_YEAR, "Table 1.3", "; ".join(notes),
        ])
    write_csv(os.path.join(OUT_DIR, "pbs_land_tenure.csv"), header, rows)

    # -------------------------------------------------------------------
    # 3. pbs_irrigation.csv
    # -------------------------------------------------------------------
    header = ["district", "total_cultivated_area", "irrigated_area", "unirrigated_area",
              "canal_area", "canal_and_tubewell_area", "tubewell_area",
              "tank_bandat_area", "spring_rod_kohi_area", "karez_area",
              "sprinkler_drip_pivot_area", "unspecified_irrigation_area",
              "lift_pump_area", "other_irrigation_area", "sailaba_area",
              "barani_area", "irrigable_not_irrigated_area", "irrigation_method_notes",
              "source_year", "source_table", "notes"]
    rows = []
    for unit in ROW_KEYS:
        v = t42.get(unit, [""] * 14)
        vals = [norm_value(x) for x in v]

        def total(*xs):
            nums = [float(x) for x in xs if x != ""]
            return str(int(sum(nums))) if nums else ""

        other = total(vals[5], vals[6], vals[7], vals[9])
        method_notes = (
            "Modes per Table 4.2: canal only; canal and tubewell; tubewell only; "
            "tank/bandat (small dams); spring or hill ravines (rod-kohi); karez; "
            "sprinkler/drip/central pivot (published only as one combined column); "
            "unspecified sources. Unirrigated = sailaba (flood) + barani (rain-fed) "
            "+ area with irrigation facility not irrigated. "
            "lift_pump_area is not reported at area level in the census; the "
            "tubewell_area column covers irrigation by tubewell or pump (census "
            "questionnaire Part-4). other_irrigation_area is derived: sum of "
            "tank/bandat + spring/rod-kohi + karez + unspecified sources."
        )
        notes = list(unit_flags(unit, master))
        notes.append(STD_FOOTNOTE)
        rows.append([
            display_name(unit), vals[0], vals[1], vals[10], vals[2], vals[3], vals[4],
            vals[5], vals[6], vals[7], vals[8], vals[9], "", other, vals[11],
            vals[12], vals[13], method_notes, SOURCE_YEAR, "Table 4.2",
            "; ".join(notes),
        ])
    write_csv(os.path.join(OUT_DIR, "pbs_irrigation.csv"), header, rows)

    # -------------------------------------------------------------------
    # 4. pbs_crops.csv
    # -------------------------------------------------------------------
    header = ["district", "crop_name", "crop_area", "crop_share", "season",
              "total_cropped_area", "source_year", "source_table", "notes"]
    rows = []
    for unit in ROW_KEYS:
        shares = t65.get(unit, [""] * 16)
        d10 = t10.get(unit, {})
        total_cropped = norm_value(shares[0])
        crop_rows = []
        for i, (_, crop_name) in enumerate(CROP_SHARE_COLS):
            crop_rows.append((crop_name, "", norm_value(shares[i + 1])))
        crop_rows.append(("Maize (Total)", norm_value(d10.get("maize_area")), ""))
        crop_rows.append(("Kharif Crops (Total)", norm_value(d10.get("kharif_area")), ""))
        crop_rows.append(("Rabi Crops (Total)", norm_value(d10.get("rabi_area")), ""))
        crop_rows.append(("Total Cropped Area", norm_value(d10.get("cropped_area")), ""))
        for crop_name, area, share in crop_rows:
            if crop_name in CROP_AREA_SOURCE:
                area = norm_value(d10.get(CROP_AREA_SOURCE[crop_name], ""))
            notes = list(unit_flags(unit, master))
            notes.append(
                "crop_share = percent of total cropped area (Table 6.5), rounded to "
                "integer in source; crop_area reported only for major crops (Table 1.0)"
            )
            notes.append(
                "season assigned per standard Punjab crop calendar, not a census-reported field"
            )
            notes.append(STD_FOOTNOTE)
            rows.append([
                display_name(unit), crop_name, area, share, CROP_SEASON[crop_name],
                total_cropped, SOURCE_YEAR, "Tables 6.5, 1.0", "; ".join(notes),
            ])
    write_csv(os.path.join(OUT_DIR, "pbs_crops.csv"), header, rows)

    # -------------------------------------------------------------------
    # 5. pbs_machinery.csv
    # -------------------------------------------------------------------
    header = ["district", "tractor_count", "tubewell_count", "electric_tubewell",
              "diesel_tubewell", "solar_tubewell", "implements_notes",
              "petrol_tubewell", "other_power_tubewell", "lift_pump_count",
              "electric_lift_pump", "solar_lift_pump", "diesel_lift_pump",
              "petrol_lift_pump", "other_power_lift_pump",
              "tubewell_and_lift_pump_total", "tractors_owned_individually",
              "tractors_owned_jointly", "tractors_owned_cooperative",
              "source_year", "source_table", "notes"]
    rows = []
    for unit in ROW_KEYS:
        tr = t81.get(unit, [""] * 4)
        tw = t811.get(unit, [""] * 13)
        imp = t816.get(unit, [""] * 15)
        imp_parts = []
        for name, raw in zip(IMPLEMENT_COLS, imp):
            v = norm_value(raw)
            if v != "":
                imp_parts.append(f"{name}={v}")
        implements_notes = (
            "owned implements (Table 8.16): " + "; ".join(imp_parts)
            if imp_parts else "owned implements (Table 8.16): none reported"
        )
        notes = list(unit_flags(unit, master))
        notes.append(
            "Tubewell counts by operating power do not sum to the tubewell total in "
            "the source (dual-power units); values preserved as reported"
        )
        notes.append(STD_FOOTNOTE)
        rows.append([
            display_name(unit), norm_value(tr[0]),
            norm_value(tw[1]), norm_value(tw[2]), norm_value(tw[4]), norm_value(tw[3]),
            implements_notes,
            norm_value(tw[5]), norm_value(tw[6]), norm_value(tw[7]), norm_value(tw[8]),
            norm_value(tw[9]), norm_value(tw[10]), norm_value(tw[11]), norm_value(tw[12]),
            norm_value(tw[0]), norm_value(tr[1]), norm_value(tr[2]), norm_value(tr[3]),
            SOURCE_YEAR, "Tables 8.1, 8.11, 8.16", "; ".join(notes),
        ])
    write_csv(os.path.join(OUT_DIR, "pbs_machinery.csv"), header, rows)

    # -------------------------------------------------------------------
    # 6. pbs_livestock.csv
    # -------------------------------------------------------------------
    header = ["district", "animal_type", "animal_count", "source_year",
              "source_table", "notes"]
    rows = []
    for unit in ROW_KEYS:
        v = t71.get(unit, [""] * 9)
        for i, (_, animal) in enumerate(LIVESTOCK_TYPES):
            notes = list(unit_flags(unit, master))
            notes.append("Head count of animals on census day")
            if norm_value(v[i]) == "":
                notes.append('"-": no value reported in source')
            notes.append(STD_FOOTNOTE)
            rows.append([
                display_name(unit), animal, norm_value(v[i]), SOURCE_YEAR,
                "Table 7.1", "; ".join(notes),
            ])
    write_csv(os.path.join(OUT_DIR, "pbs_livestock.csv"), header, rows)

    # -------------------------------------------------------------------
    # 7. pbs_credit.csv  (no district-level credit table published)
    # -------------------------------------------------------------------
    header = ["district", "loan_access", "loan_source", "loan_amount_if_available",
              "source_year", "source_table", "notes"]
    write_csv(os.path.join(OUT_DIR, "pbs_credit.csv"), header, [])
    print("  pbs_credit.csv is intentionally empty: the census questionnaire "
          "(Form-2 Part-13) collected agricultural loan data, but the Punjab "
          "report publishes no district-level credit table")

    # -------------------------------------------------------------------
    # 8. pbs_modern_farming.csv
    # -------------------------------------------------------------------
    header = ["district", "tunnel_farming", "sprinkler", "drip", "central_pivot",
              "adoption_notes", "tunnel_farming_area", "tunnel_farming_percent_of_farms",
              "tunnel_area_owner", "tunnel_area_owner_cum_tenant", "tunnel_area_tenant",
              "tunnel_area_owner_percent", "tunnel_area_owner_cum_tenant_percent",
              "tunnel_area_tenant_percent", "sprinkler_drip_pivot_area",
              "source_year", "source_table", "notes"]
    rows = []
    for unit in ROW_KEYS:
        v = t619.get(unit, [""] * 10)
        i42 = t42.get(unit, [""] * 14)
        adoption = (
            "Tunnel farming: farms reporting and area protected by tenure from Table 6.19. "
            "Sprinkler, drip and central pivot adoption is not published as separate "
            "district-level counts; Table 4.2 reports one combined irrigated-area column "
            "(sprinkler/drip/central pivot), carried in sprinkler_drip_pivot_area. "
            "tunnel_area_owner_cum_tenant_percent appears misprinted in the source "
            "(duplicates the owner percent); values preserved as reported."
        )
        notes = list(unit_flags(unit, master))
        notes.append(STD_FOOTNOTE)
        rows.append([
            display_name(unit), norm_value(v[1]), "", "", "", adoption,
            norm_value(v[3]), norm_value(v[2]), norm_value(v[4]), norm_value(v[6]),
            norm_value(v[8]), norm_value(v[5]), norm_value(v[7]), norm_value(v[9]),
            norm_value(i42[8]), SOURCE_YEAR, "Tables 6.19, 4.2", "; ".join(notes),
        ])
    write_csv(os.path.join(OUT_DIR, "pbs_modern_farming.csv"), header, rows)

    # -------------------------------------------------------------------
    # 9. pbs_data_dictionary.csv
    # -------------------------------------------------------------------
    write_data_dictionary()

    print()
    if WARNINGS:
        print(f"Extraction finished with {len(WARNINGS)} warnings:")
        for w in WARNINGS:
            print(f"  - {w}")
    else:
        print("Extraction finished with no warnings.")


def write_data_dictionary():
    path = os.path.join(OUT_DIR, "pbs_data_dictionary.csv")
    src = "Source: PBS Agricultural Census 2024, Punjab Report " \
          "(IAC-Punjab-Report-25-05-2026-1-1_copy.pdf). Sample-based census: mouza/block " \
          "two-stage sample, results representative at district level (15% margin of error, " \
          "95% CI). Enumeration Sep-Nov 2024 (cold areas) and Jan-Feb 2025; source_year 2024 " \
          f"refers to the census reference period. {STD_FOOTNOTE}."
    rows = []

    def add(file, column, description, unit, table=""):
        rows.append([file, column, description, unit, table, src])

    add("pbs_farm_structure.csv", "district", "Census district (36 districts plus Cholistan Area)", "text", "Tables 1.0, 1.1")
    add("pbs_farm_structure.csv", "farm_count", "Number of farms (agricultural holdings); NOT farmer/household counts", "farms", "Tables 1.0, 1.1")
    add("pbs_farm_structure.csv", "total_farm_area", "Total farm area", "acres", "Table 1.0")
    add("pbs_farm_structure.csv", "cultivated_area", "Cultivated area (net sown + current fallow)", "acres", "Table 1.0")
    add("pbs_farm_structure.csv", "average_farm_size", "Average farm size as reported", "acres/farm", "Table 1.0")
    add("pbs_farm_structure.csv", "uncultivated_area", "Uncultivated area", "acres", "Table 1.0")
    add("pbs_farm_structure.csv", "source_year", "Census year", "year", "")
    add("pbs_farm_structure.csv", "source_table", "Source tables in the census report", "text", "")
    add("pbs_farm_structure.csv", "notes", "Row flags and footnotes", "text", "")

    add("pbs_land_tenure.csv", "district", "Census district", "text", "Table 1.3")
    add("pbs_land_tenure.csv", "total_farms", "Total farms", "farms", "Table 1.3")
    add("pbs_land_tenure.csv", "owner_farms", "Farms operated by owners", "farms", "Table 1.3")
    add("pbs_land_tenure.csv", "owner_cum_tenant_farms", "Farms operated by owner-cum-tenant", "farms", "Table 1.3")
    add("pbs_land_tenure.csv", "tenant_farms", "Farms operated by tenants", "farms", "Table 1.3")
    add("pbs_land_tenure.csv", "owner_farms_percent", "Owner farms as percent of total farms (schema field 'tenure_percentages' split into separate columns)", "percent", "Table 1.3")
    add("pbs_land_tenure.csv", "owner_cum_tenant_farms_percent", "Owner-cum-tenant farms as percent of total farms", "percent", "Table 1.3")
    add("pbs_land_tenure.csv", "tenant_farms_percent", "Tenant farms as percent of total farms", "percent", "Table 1.3")
    add("pbs_land_tenure.csv", "total_farm_area", "Total farm area", "acres", "Table 1.3")
    add("pbs_land_tenure.csv", "owner_farm_area", "Farm area operated by owners", "acres", "Table 1.3")
    add("pbs_land_tenure.csv", "owner_cum_tenant_farm_area", "Farm area operated by owner-cum-tenant", "acres", "Table 1.3")
    add("pbs_land_tenure.csv", "tenant_farm_area", "Farm area operated by tenants", "acres", "Table 1.3")
    add("pbs_land_tenure.csv", "owner_area_percent", "Owner-operated area as percent of farm area", "percent", "Table 1.3")
    add("pbs_land_tenure.csv", "owner_cum_tenant_area_percent", "Owner-cum-tenant area as percent of farm area", "percent", "Table 1.3")
    add("pbs_land_tenure.csv", "tenant_area_percent", "Tenant-operated area as percent of farm area", "percent", "Table 1.3")
    add("pbs_land_tenure.csv", "source_year", "Census year", "year", "")
    add("pbs_land_tenure.csv", "source_table", "Source table", "text", "")
    add("pbs_land_tenure.csv", "notes", "Row flags and footnotes", "text", "")

    add("pbs_irrigation.csv", "district", "Census district", "text", "Table 4.2")
    add("pbs_irrigation.csv", "total_cultivated_area", "Total cultivated area", "acres", "Table 4.2")
    add("pbs_irrigation.csv", "irrigated_area", "Cultivated area actually irrigated", "acres", "Table 4.2")
    add("pbs_irrigation.csv", "unirrigated_area", "Cultivated area not irrigated (sailaba + barani + facility-not-irrigated)", "acres", "Table 4.2")
    add("pbs_irrigation.csv", "canal_area", "Area irrigated by canal only", "acres", "Table 4.2")
    add("pbs_irrigation.csv", "canal_and_tubewell_area", "Area irrigated by canal as well as tubewell (mixed)", "acres", "Table 4.2")
    add("pbs_irrigation.csv", "tubewell_area", "Area irrigated by tubewell or pump only", "acres", "Table 4.2")
    add("pbs_irrigation.csv", "tank_bandat_area", "Area irrigated by ponds or small dams (bandat) or rivulet only", "acres", "Table 4.2")
    add("pbs_irrigation.csv", "spring_rod_kohi_area", "Area irrigated by spring or hill ravines (rod-kohi) only", "acres", "Table 4.2")
    add("pbs_irrigation.csv", "karez_area", "Area irrigated by karez only", "acres", "Table 4.2")
    add("pbs_irrigation.csv", "sprinkler_drip_pivot_area", "Area irrigated by sprinkler/drip/central pivot (combined column in source)", "acres", "Table 4.2")
    add("pbs_irrigation.csv", "unspecified_irrigation_area", "Area irrigated by unspecified sources", "acres", "Table 4.2")
    add("pbs_irrigation.csv", "lift_pump_area", "Not reported at area level; left empty (tubewell_area covers tubewell or pump)", "acres", "n/a")
    add("pbs_irrigation.csv", "other_irrigation_area", "DERIVED: sum of tank/bandat + spring/rod-kohi + karez + unspecified", "acres", "derived")
    add("pbs_irrigation.csv", "sailaba_area", "Unirrigated area flooded (sailaba)", "acres", "Table 4.2")
    add("pbs_irrigation.csv", "barani_area", "Unirrigated area rain-fed (barani)", "acres", "Table 4.2")
    add("pbs_irrigation.csv", "irrigable_not_irrigated_area", "Cultivated area with irrigation facility but not irrigated", "acres", "Table 4.2")
    add("pbs_irrigation.csv", "irrigation_method_notes", "Mode definitions and mapping notes", "text", "")
    add("pbs_irrigation.csv", "source_year", "Census year", "year", "")
    add("pbs_irrigation.csv", "source_table", "Source table", "text", "")
    add("pbs_irrigation.csv", "notes", "Row flags and footnotes", "text", "")

    add("pbs_crops.csv", "district", "Census district", "text", "Tables 6.5, 1.0")
    add("pbs_crops.csv", "crop_name", "Crop or crop group (15 share categories from Table 6.5 plus totals from Table 1.0)", "text", "Tables 6.5, 1.0")
    add("pbs_crops.csv", "crop_area", "Reported crop area; available only for wheat, rice, cotton, sugarcane, fodder, orchards, maize and season totals (Table 1.0)", "acres", "Table 1.0")
    add("pbs_crops.csv", "crop_share", "Crop area as percent of total cropped area (Table 6.5), integer-rounded", "percent", "Table 6.5")
    add("pbs_crops.csv", "season", "Season assigned per standard Punjab crop calendar (not census-reported)", "text", "derived")
    add("pbs_crops.csv", "total_cropped_area", "Total cropped area of the district (context)", "acres", "Table 6.5")
    add("pbs_crops.csv", "source_year", "Census year", "year", "")
    add("pbs_crops.csv", "source_table", "Source tables", "text", "")
    add("pbs_crops.csv", "notes", "Row flags and footnotes", "text", "")

    add("pbs_machinery.csv", "district", "Census district", "text", "Tables 8.1, 8.11, 8.16")
    add("pbs_machinery.csv", "tractor_count", "All tractors (owned individually + jointly + by co-operative societies)", "tractors", "Table 8.1")
    add("pbs_machinery.csv", "tubewell_count", "Tubewells (all operating powers)", "tubewells", "Table 8.11")
    add("pbs_machinery.csv", "electric_tubewell", "Tubewells operated by electricity", "tubewells", "Table 8.11")
    add("pbs_machinery.csv", "diesel_tubewell", "Tubewells operated by diesel", "tubewells", "Table 8.11")
    add("pbs_machinery.csv", "solar_tubewell", "Tubewells operated by solar power", "tubewells", "Table 8.11")
    add("pbs_machinery.csv", "implements_notes", "Owned counts of 15 ploughing implements (Table 8.16) as name=value pairs", "text", "Table 8.16")
    add("pbs_machinery.csv", "petrol_tubewell", "Tubewells operated by petrol", "tubewells", "Table 8.11")
    add("pbs_machinery.csv", "other_power_tubewell", "Tubewells operated by other power", "tubewells", "Table 8.11")
    add("pbs_machinery.csv", "lift_pump_count", "Lift pumps (all powers)", "lift pumps", "Table 8.11")
    add("pbs_machinery.csv", "electric_lift_pump", "Lift pumps operated by electricity", "lift pumps", "Table 8.11")
    add("pbs_machinery.csv", "solar_lift_pump", "Lift pumps operated by solar power", "lift pumps", "Table 8.11")
    add("pbs_machinery.csv", "diesel_lift_pump", "Lift pumps operated by diesel", "lift pumps", "Table 8.11")
    add("pbs_machinery.csv", "petrol_lift_pump", "Lift pumps operated by petrol", "lift pumps", "Table 8.11")
    add("pbs_machinery.csv", "other_power_lift_pump", "Lift pumps operated by other power", "lift pumps", "Table 8.11")
    add("pbs_machinery.csv", "tubewell_and_lift_pump_total", "Total tubewells and lift pumps", "units", "Table 8.11")
    add("pbs_machinery.csv", "tractors_owned_individually", "Tractors owned individually", "tractors", "Table 8.1")
    add("pbs_machinery.csv", "tractors_owned_jointly", "Tractors owned jointly", "tractors", "Table 8.1")
    add("pbs_machinery.csv", "tractors_owned_cooperative", "Tractors owned by co-operative societies", "tractors", "Table 8.1")
    add("pbs_machinery.csv", "source_year", "Census year", "year", "")
    add("pbs_machinery.csv", "source_table", "Source tables", "text", "")
    add("pbs_machinery.csv", "notes", "Row flags and footnotes", "text", "")

    add("pbs_livestock.csv", "district", "Census district", "text", "Table 7.1")
    add("pbs_livestock.csv", "animal_type", "Cattle, Buffaloes, Sheep, Goats, Camels, Horses, Mules, Asses, Yak/Dzo/Dzomo", "text", "Table 7.1")
    add("pbs_livestock.csv", "animal_count", "Number of animals (head count)", "animals", "Table 7.1")
    add("pbs_livestock.csv", "source_year", "Census year", "year", "")
    add("pbs_livestock.csv", "source_table", "Source table", "text", "")
    add("pbs_livestock.csv", "notes", "Row flags and footnotes", "text", "")

    add("pbs_credit.csv", "district", "No rows: district-level agricultural credit data not published in this report", "text", "n/a")
    add("pbs_credit.csv", "loan_access", "Not available (questionnaire Form-2 Part-13 collected loan data; no district table published)", "text", "n/a")
    add("pbs_credit.csv", "loan_source", "Not available", "text", "n/a")
    add("pbs_credit.csv", "loan_amount_if_available", "Not available", "text", "n/a")
    add("pbs_credit.csv", "source_year", "Census year", "year", "")
    add("pbs_credit.csv", "source_table", "n/a", "text", "")
    add("pbs_credit.csv", "notes", "n/a", "text", "")

    add("pbs_modern_farming.csv", "district", "Census district", "text", "Tables 6.19, 4.2")
    add("pbs_modern_farming.csv", "tunnel_farming", "Farms reporting use of greenhouse technology (tunnel farming)", "farms", "Table 6.19")
    add("pbs_modern_farming.csv", "sprinkler", "Not published as separate district-level count; left empty", "text", "n/a")
    add("pbs_modern_farming.csv", "drip", "Not published as separate district-level count; left empty", "text", "n/a")
    add("pbs_modern_farming.csv", "central_pivot", "Not published as separate district-level count; left empty", "text", "n/a")
    add("pbs_modern_farming.csv", "adoption_notes", "Notes on tunnel farming and combined sprinkler/drip/pivot availability", "text", "")
    add("pbs_modern_farming.csv", "tunnel_farming_area", "Total area protected by tunnel farming", "acres", "Table 6.19")
    add("pbs_modern_farming.csv", "tunnel_farming_percent_of_farms", "Farms reporting tunnel farming as percent of all farms (integer-rounded)", "percent", "Table 6.19")
    add("pbs_modern_farming.csv", "tunnel_area_owner", "Tunnel-farming area operated by owners", "acres", "Table 6.19")
    add("pbs_modern_farming.csv", "tunnel_area_owner_cum_tenant", "Tunnel-farming area operated by owner-cum-tenant", "acres", "Table 6.19")
    add("pbs_modern_farming.csv", "tunnel_area_tenant", "Tunnel-farming area operated by tenants", "acres", "Table 6.19")
    add("pbs_modern_farming.csv", "tunnel_area_owner_percent", "Owner share of tunnel area (as reported)", "percent", "Table 6.19")
    add("pbs_modern_farming.csv", "tunnel_area_owner_cum_tenant_percent", "Owner-cum-tenant share of tunnel area (as reported; appears misprinted in source)", "percent", "Table 6.19")
    add("pbs_modern_farming.csv", "tunnel_area_tenant_percent", "Tenant share of tunnel area (as reported)", "percent", "Table 6.19")
    add("pbs_modern_farming.csv", "sprinkler_drip_pivot_area", "Irrigated area under sprinkler/drip/central pivot (combined column)", "acres", "Table 4.2")
    add("pbs_modern_farming.csv", "source_year", "Census year", "year", "")
    add("pbs_modern_farming.csv", "source_table", "Source tables", "text", "")
    add("pbs_modern_farming.csv", "notes", "Row flags and footnotes", "text", "")

    with io.open(path, "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["file", "column", "description", "unit", "source_table", "notes"])
        w.writerows(rows)
    print(f"  wrote pbs_data_dictionary.csv ({len(rows)} rows)")


if __name__ == "__main__":
    main()
