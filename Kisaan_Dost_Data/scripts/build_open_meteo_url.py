"""Build Open-Meteo forecast URLs from a Punjab district name or raw lat/lng.

Input modes:
    1. District name  → look up lat/lng in `processed/district_coordinates.csv`
    2. Raw lat/lng    → used directly (no lookup)

The URL template is preserved exactly as specified by the project prompt:
no variables dropped, parameter ordering preserved verbatim.

Public API:
    build_url(district=None, latitude=None, longitude=None,
              coords_csv=None) -> str
        Returns the full Open-Meteo URL.

    resolve_district(name, coords_csv=None) -> dict
        Returns {"district", "latitude", "longitude", "is_master_district",
                 "notes"} for the matching row, or raises DistrictNotFoundError.

    all_urls(coords_csv=None) -> list[dict]
        Returns one row per district in the coordinate CSV:
        {"district", "latitude", "longitude", "url", "is_master_district"}.

CLI:
    python scripts/build_open_meteo_url.py Lahore
    python scripts/build_open_meteo_url.py --lat 31.5204 --lon 74.3587
    python scripts/build_open_meteo_url.py --all
"""

from __future__ import annotations

import csv
import sys
from pathlib import Path
from typing import Dict, List, Optional, Union
from urllib.parse import urlencode

ROOT = Path(__file__).resolve().parent.parent
DEFAULT_COORDS = ROOT / "processed" / "district_coordinates.csv"

# ─── Open-Meteo template (verbatim from the project prompt) ───────────────
OPEN_METEO_BASE = "https://api.open-meteo.com/v1/forecast"

CURRENT_VARS = (
    "temperature_2m",
    "relative_humidity_2m",
    "precipitation",
    "wind_speed_10m",
)

HOURLY_VARS = (
    "temperature_2m",
    "relative_humidity_2m",
    "dewpoint_2m",
    "precipitation",
    "vapour_pressure_deficit",
    "et0_fao_evapotranspiration",
    "wind_speed_10m",
    "wind_gusts_10m",
    "weather_code",
    "soil_temperature_0cm",
    "soil_temperature_6cm",
    "soil_temperature_18cm",
    "soil_moisture_0_to_1cm",
    "soil_moisture_1_to_3cm",
    "soil_moisture_3_to_9cm",
    "soil_moisture_9_to_27cm",
    "shortwave_radiation",
    "direct_normal_irradiance",
)

DAILY_VARS = (
    "temperature_2m_max",
    "precipitation_sum",
    "precipitation_probability_max",
    "shortwave_radiation_sum",
    "et0_fao_evapotranspiration",
)

MODELS = ("ecmwf_ifs", "best_match")
TIMEZONE = "auto"


class DistrictNotFoundError(KeyError):
    """Raised when a district name cannot be resolved in the coordinate CSV."""


def _load_coords(coords_csv: Path = DEFAULT_COORDS) -> List[Dict[str, str]]:
    if not coords_csv.exists():
        raise FileNotFoundError(coords_csv)
    with coords_csv.open("r", encoding="utf-8", newline="") as fh:
        return list(csv.DictReader(fh))


def _normalize_query(name: str) -> str:
    """Strip ' District' suffix + whitespace for case-insensitive lookup."""
    n = name.strip()
    if n.lower().endswith(" district"):
        n = n[: -len(" district")]
    return n


def resolve_district(
    name: str, coords_csv: Path = DEFAULT_COORDS
) -> Dict[str, str]:
    """Return the matching row for a Punjab district name.

    Accepts "Lahore", "lahore", or "Lahore District". Matching is
    case-insensitive against both `district` and `normalized_district`.
    """
    rows = _load_coords(coords_csv)
    query = _normalize_query(name).lower()
    for r in rows:
        if (
            r["district"].strip().lower() == query
            or r["normalized_district"].strip().lower() == query
            or r["normalized_district"].strip().lower() == f"{query} district"
        ):
            return r
    available = sorted({r["district"] for r in rows})
    raise DistrictNotFoundError(
        f"district {name!r} not found in {coords_csv.name}. "
        f"Available: {available}"
    )


def _format_coord(value: float, digits: int = 4) -> str:
    """Format to 4 decimal places without trailing zeros beyond required precision."""
    return f"{value:.{digits}f}"


def build_url(
    district: Optional[str] = None,
    latitude: Optional[float] = None,
    longitude: Optional[float] = None,
    coords_csv: Path = DEFAULT_COORDS,
) -> str:
    """Build an Open-Meteo forecast URL from a district name OR raw lat/lng.

    Either `district` OR both `latitude`/`longitude` must be supplied.
    Supplying both raises ValueError — the caller must pick one mode.
    """
    has_district = district is not None
    has_coords = latitude is not None and longitude is not None
    partial_coords = (latitude is None) ^ (longitude is None)

    if has_district and has_coords:
        raise ValueError(
            "Provide either `district` OR `latitude`+`longitude`, not both."
        )
    if not has_district and not has_coords:
        raise ValueError(
            "Provide `district` OR both `latitude` and `longitude`."
        )
    if partial_coords:
        raise ValueError(
            "Both `latitude` and `longitude` must be supplied together."
        )

    if has_district:
        row = resolve_district(district, coords_csv)
        lat = float(row["latitude"])
        lon = float(row["longitude"])
    else:
        lat = float(latitude)
        lon = float(longitude)

    if not (-90.0 <= lat <= 90.0):
        raise ValueError(f"latitude {lat} out of range [-90, 90]")
    if not (-180.0 <= lon <= 180.0):
        raise ValueError(f"longitude {lon} out of range [-180, 180]")

    params = [
        ("latitude", _format_coord(lat)),
        ("longitude", _format_coord(lon)),
        ("current", ",".join(CURRENT_VARS)),
        ("hourly", ",".join(HOURLY_VARS)),
        ("daily", ",".join(DAILY_VARS)),
        ("models", ",".join(MODELS)),
        ("timezone", TIMEZONE),
    ]
    # urlencode with doseq=False keeps comma-separated values unsplit;
    # safe="," prevents percent-encoding of the commas inside list values.
    return f"{OPEN_METEO_BASE}?{urlencode(params, safe=',')}"


def all_urls(coords_csv: Path = DEFAULT_COORDS) -> List[Dict[str, object]]:
    """Build a URL for every row in the coordinate CSV (41 entries)."""
    rows = _load_coords(coords_csv)
    out: List[Dict[str, object]] = []
    for r in rows:
        out.append({
            "district": r["district"],
            "latitude": float(r["latitude"]),
            "longitude": float(r["longitude"]),
            "is_master_district": r["is_master_district"],
            "notes": r["notes"],
            "url": build_url(district=r["district"], coords_csv=coords_csv),
        })
    return out


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("district", nargs="?", help="Punjab district name")
    parser.add_argument("--lat", type=float, help="raw latitude (WGS84)")
    parser.add_argument("--lon", type=float, help="raw longitude (WGS84)")
    parser.add_argument(
        "--all", action="store_true", help="emit a URL for every coordinate row"
    )
    parser.add_argument(
        "--json", action="store_true", help="emit JSON (district + url) instead of plain text"
    )
    args = parser.parse_args()

    try:
        if args.all:
            for entry in all_urls():
                print(f"{entry['district']:<25} {entry['url']}")
        elif args.district:
            row = resolve_district(args.district)
            url = build_url(district=args.district)
            print(f"district      : {row['district']}")
            print(f"normalized    : {row['normalized_district']}")
            print(f"latitude      : {row['latitude']}")
            print(f"longitude     : {row['longitude']}")
            print(f"master        : {row['is_master_district']}")
            print(f"notes         : {row['notes']}")
            print(f"url           :\n  {url}")
        elif args.lat is not None and args.lon is not None:
            url = build_url(latitude=args.lat, longitude=args.lon)
            print(f"latitude      : {args.lat}")
            print(f"longitude     : {args.lon}")
            print(f"url           :\n  {url}")
        else:
            parser.error("Provide a district name, --lat/--lon, or --all.")
    except DistrictNotFoundError as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        sys.exit(2)
