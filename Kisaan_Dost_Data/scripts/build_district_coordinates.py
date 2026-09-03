"""Build and validate the normalized district coordinate table.

Inputs:
    - Hard-coded 41-district mapping (verbatim from the project prompt).
      Coordinates are authoritative; this script does NOT invent or
      interpolate any of them.
    - `processed/district_master_clean.csv` as the 34-district master.

Output:
    - `processed/district_coordinates.csv` (41 rows, 8 columns)
    - Console summary for the validator report.

Output schema:
    district              original name from the prompt (no " District" suffix)
    normalized_district   title-case + " District" (matches master)
    latitude              float, WGS84
    longitude             float, WGS84
    source                "project_prompt"
    source_timestamp      ISO-8601 build timestamp
    is_master_district    True/False (string)
    notes                 free-form (see below)

Notes taxonomy:
    - ""                          : plain master district
    - "annex unit"                : in PBS census / ArcGIS boundary, not in master
    - "newly created district"    : post-baseline district, absent from master + boundary
    - "tehsil promoted"           : tehsil-level name in the mapping, not a master district
"""

from __future__ import annotations

import csv
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, List, Tuple

ROOT = Path(__file__).resolve().parent.parent
DEFAULT_MASTER = ROOT / "processed" / "district_master_clean.csv"
DEFAULT_OUT = ROOT / "processed" / "district_coordinates.csv"

PROMPT_COORDINATES: List[Tuple[str, float, float, str]] = [
    ("Lahore",              31.5204, 74.3587, "master"),
    ("Faisalabad",          31.4504, 73.1350, "master"),
    ("Multan",              30.1575, 71.5249, "master"),
    ("Rawalpindi",          33.5651, 73.0169, "master"),
    ("Gujranwala",          32.1877, 74.1945, "master"),
    ("Sargodha",            32.0836, 72.6711, "master"),
    ("Bahawalpur",          29.3956, 71.6836, "master"),
    ("Sialkot",             32.4945, 74.5229, "master"),
    ("Sheikhupura",         31.7131, 73.9783, "master"),
    ("Rahim Yar Khan",      28.4212, 70.2989, "master"),
    ("Jhang",               31.2781, 72.3317, "master"),
    ("Dera Ghazi Khan",     30.0489, 70.6403, "master"),
    ("Gujrat",              32.5742, 74.0754, "master"),
    ("Sahiwal",             31.6701, 73.1068, "master"),
    ("Okara",               30.8138, 73.4534, "master"),
    ("Kasur",               31.1156, 74.4503, "master"),
    ("Bahawalnagar",        29.9987, 73.2536, "master"),
    ("Chiniot",             31.7200, 72.9780, "annex"),
    ("Attock",              33.7660, 72.3609, "master"),
    ("Khanewal",            30.3017, 71.9321, "master"),
    ("Muzaffargarh",        30.0703, 71.1933, "master"),
    ("Vehari",              30.0419, 72.3441, "master"),
    ("Jhelum",              32.9405, 73.7276, "master"),
    ("Chakwal",             32.9328, 72.8630, "master"),
    ("Mianwali",            32.5839, 71.5370, "master"),
    ("Bhakkar",             31.6333, 71.0667, "master"),
    ("Layyah",              30.9613, 70.9390, "master"),
    ("Rajanpur",            29.1044, 70.3297, "master"),
    ("Pakpattan",           30.3500, 73.3833, "master"),
    ("Toba Tek Singh",      30.9667, 72.4833, "master"),
    ("Hafizabad",           32.0709, 73.6880, "master"),
    ("Lodhran",             29.5339, 71.6324, "master"),
    ("Nankana Sahib",       31.4492, 73.7124, "annex"),
    ("Mandi Bahauddin",     32.5861, 73.4917, "master"),
    ("Narowal",             32.1020, 74.8730, "master"),
    ("Khushab",             32.2952, 72.3501, "master"),
    ("Kot Addu",            30.4700, 70.9667, "tehsil_promoted"),
    ("Murree",              33.9070, 73.3903, "tehsil_promoted"),
    ("Talagang",            32.9272, 72.4158, "newly_created"),
    ("Taunsa",              30.7036, 70.6506, "tehsil_promoted"),
    ("Wazirabad",           32.4431, 74.1202, "tehsil_promoted"),
]

NOTES_BY_KIND = {
    "master": "",
    "annex": "annex unit",
    "newly_created": "newly created district",
    "tehsil_promoted": "tehsil promoted",
}


def _normalize(name: str) -> str:
    return f"{name.strip()} District"


def build(timestamp: datetime | None = None) -> List[Dict[str, str]]:
    ts = (timestamp or datetime.now(timezone.utc)).isoformat(timespec="seconds")
    rows: List[Dict[str, str]] = []
    for name, lat, lon, kind in PROMPT_COORDINATES:
        rows.append({
            "district": name,
            "normalized_district": _normalize(name),
            "latitude": f"{lat:.4f}",
            "longitude": f"{lon:.4f}",
            "source": "project_prompt",
            "source_timestamp": ts,
            "is_master_district": str(kind == "master"),
            "notes": NOTES_BY_KIND[kind],
        })
    return rows


def write_csv(rows: List[Dict[str, str]], out_path: Path) -> None:
    out_path.parent.mkdir(parents=True, exist_ok=True)
    fieldnames = [
        "district", "normalized_district", "latitude", "longitude",
        "source", "source_timestamp", "is_master_district", "notes",
    ]
    with out_path.open("w", encoding="utf-8", newline="") as fh:
        writer = csv.DictWriter(fh, fieldnames=fieldnames)
        writer.writeheader()
        for r in rows:
            writer.writerow(r)


def read_master(master_path: Path) -> List[str]:
    if not master_path.exists():
        return []
    with master_path.open("r", encoding="utf-8", newline="") as fh:
        reader = csv.DictReader(fh)
        return sorted({row["district"] for row in reader})


def validate(rows: List[Dict[str, str]], master: List[str]) -> Dict[str, object]:
    total = len(rows)
    names = [r["district"] for r in rows]
    duplicates = [n for n in set(names) if names.count(n) > 1]

    coords = {r["normalized_district"]: r for r in rows}
    master_set = set(master)
    matched = sorted(n for n in master_set if n in coords)
    missing_in_coords = sorted(n for n in master_set if n not in coords)

    non_master = sorted(
        (r for r in rows if r["is_master_district"] == "False"),
        key=lambda r: r["district"],
    )

    lat_range = (
        min(float(r["latitude"]) for r in rows),
        max(float(r["latitude"]) for r in rows),
    )
    lon_range = (
        min(float(r["longitude"]) for r in rows),
        max(float(r["longitude"]) for r in rows),
    )

    return {
        "total_loaded": total,
        "master_districts": len(master),
        "matched_master": len(matched),
        "matched_master_names": matched,
        "missing_from_coords": missing_in_coords,
        "extra_non_master": [r["district"] for r in non_master],
        "extra_non_master_count": len(non_master),
        "duplicates": duplicates,
        "latitude_range": lat_range,
        "longitude_range": lon_range,
    }


def print_summary(summary: Dict[str, object]) -> None:
    print(f"total loaded        : {summary['total_loaded']}")
    print(f"master districts    : {summary['master_districts']}")
    print(f"matched master      : {summary['matched_master']}")
    print(f"missing from coords: {len(summary['missing_from_coords'])}")
    for m in summary["missing_from_coords"]:
        print(f"  - {m}")
    print(f"extra non-master    : {summary['extra_non_master_count']}")
    for x in summary["extra_non_master"]:
        print(f"  - {x}")
    print(f"duplicates          : {len(summary['duplicates'])}")
    for d in summary["duplicates"]:
        print(f"  - {d}")
    print(f"lat range           : {summary['latitude_range'][0]:.4f} .. {summary['latitude_range'][1]:.4f}")
    print(f"lon range           : {summary['longitude_range'][0]:.4f} .. {summary['longitude_range'][1]:.4f}")


if __name__ == "__main__":
    rows = build()
    write_csv(rows, DEFAULT_OUT)
    master = read_master(DEFAULT_MASTER)
    summary = validate(rows, master)
    print_summary(summary)
    if summary["missing_from_coords"]:
        sys.exit(1)
    sys.exit(0)
