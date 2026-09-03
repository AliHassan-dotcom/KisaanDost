"""Spatial join: map NASA POWER grid points to Punjab districts.

For each of the 117 NASA POWER grid points covering Punjab:
  1. Try point-in-polygon against the 29 master-district polygons in
     `raw/arcgis/punjab_district_boundaries.geojson` (ray-casting).
  2. If no polygon matches, fall back to nearest centroid among the
     5 districts missing from the boundary file (Bhakkar, Jhang, Layyah,
     Muzaffargarh, Okara) using Haversine distance.

The grid-point → district mapping is then joined to every record from
the 12 NASA POWER JSON files via `parse_nasa_power_json.iter_records()`.

Output: `processed/weather_join_keys.csv` — one row per
(grid-point, date, parameter) record with 13 columns.

Stdlib only — no shapely / geopandas / pandas.
"""

from __future__ import annotations

import csv
import json
import math
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

# ---------------------------------------------------------------------------
# Paths (relative to project root = parent of scripts/)
# ---------------------------------------------------------------------------
ROOT = Path(__file__).resolve().parent.parent
BOUNDARY_PATH = ROOT / "raw" / "arcgis" / "punjab_district_boundaries.geojson"
COORDS_PATH = ROOT / "processed" / "district_coordinates.csv"
WEATHER_DIR = ROOT / "Historical Data"
OUTPUT_PATH = ROOT / "processed" / "weather_join_keys.csv"

# Ensure parse_nasa_power_json is importable from scripts/
sys.path.insert(0, str(ROOT / "scripts"))
from parse_nasa_power_json import iter_records  # noqa: E402

OUTPUT_COLUMNS = [
    "source_file",
    "source_parameter",
    "source_date",
    "grid_lon",
    "grid_lat",
    "grid_elevation_m",
    "district",
    "normalized_district",
    "method",
    "distance_km",
    "is_fallback",
    "boundary_match_status",
    "source_provider",
]

EARTH_RADIUS_KM = 6371.0


# ---------------------------------------------------------------------------
# Geometry helpers (stdlib only)
# ---------------------------------------------------------------------------

def point_in_polygon(px: float, py: float, ring: List[Tuple[float, float]]) -> bool:
    """Ray-casting point-in-polygon test.

    `ring` is the exterior ring as a list of (lon, lat) tuples.
    Holes are not expected in this dataset (all single-ring polygons).
    """
    n = len(ring)
    inside = False
    j = n - 1
    for i in range(n):
        xi, yi = ring[i]
        xj, yj = ring[j]
        if ((yi > py) != (yj > py)) and (
            px < (xj - xi) * (py - yi) / (yj - yi) + xi
        ):
            inside = not inside
        j = i
    return inside


def point_in_geometry(
    px: float, py: float, geom: Dict[str, Any]
) -> bool:
    """PIP test handling both Polygon and MultiPolygon geometries."""
    gtype = geom.get("type")
    coords = geom.get("coordinates", [])
    if gtype == "Polygon":
        ring = [(c[0], c[1]) for c in coords[0]]
        return point_in_polygon(px, py, ring)
    elif gtype == "MultiPolygon":
        for polygon in coords:
            ring = [(c[0], c[1]) for c in polygon[0]]
            if point_in_polygon(px, py, ring):
                return True
        return False
    return False


def haversine_km(
    lat1: float, lon1: float, lat2: float, lon2: float
) -> float:
    """Great-circle distance in km between two WGS-84 points."""
    phi1, phi2 = math.radians(lat1), math.radians(lat2)
    dphi = math.radians(lat2 - lat1)
    dlam = math.radians(lon2 - lon1)
    a = (
        math.sin(dphi / 2) ** 2
        + math.cos(phi1) * math.cos(phi2) * math.sin(dlam / 2) ** 2
    )
    return EARTH_RADIUS_KM * 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))


# ---------------------------------------------------------------------------
# Data loaders
# ---------------------------------------------------------------------------

def load_polygons(
    geojson_path: Path = BOUNDARY_PATH,
) -> Dict[str, Dict[str, Any]]:
    """Load ArcGIS GeoJSON and return {district_name: geometry} for all features."""
    with geojson_path.open("r", encoding="utf-8") as fh:
        doc = json.load(fh)
    polygons = {}
    for feat in doc.get("features", []):
        name = feat["properties"]["DISTRICT"]
        polygons[name] = feat["geometry"]
    return polygons


def load_district_centroids(
    coords_path: Path = COORDS_PATH,
) -> Dict[str, Dict[str, Any]]:
    """Load district_coordinates.csv and return {district: row_dict} for master districts."""
    centroids = {}
    with coords_path.open("r", encoding="utf-8", newline="") as fh:
        reader = csv.DictReader(fh)
        for row in reader:
            if row["is_master_district"] == "True":
                centroids[row["district"]] = {
                    "district": row["district"],
                    "normalized_district": row["normalized_district"],
                    "latitude": float(row["latitude"]),
                    "longitude": float(row["longitude"]),
                }
    return centroids


def identify_fallback_districts(
    polygons: Dict[str, Dict[str, Any]],
    centroids: Dict[str, Dict[str, Any]],
) -> List[str]:
    """Return master districts that have no polygon in the boundary file."""
    return sorted(set(centroids.keys()) - set(polygons.keys()))


# ---------------------------------------------------------------------------
# Grid-point → district mapping
# ---------------------------------------------------------------------------

def build_grid_mapping(
    polygons: Dict[str, Dict[str, Any]],
    centroids: Dict[str, Dict[str, Any]],
    fallback_names: List[str],
    grid_points: List[Tuple[float, float, float]],
) -> Dict[Tuple[float, float], Dict[str, Any]]:
    """For each (lon, lat), determine the assigned district.

    Returns {(lon, lat): {district, normalized_district, method,
    distance_km, is_fallback, boundary_match_status}}.
    """
    # Master districts that have polygons (for PIP matching)
    master_with_polygon = set(centroids.keys()) & set(polygons.keys())

    mapping: Dict[Tuple[float, float], Dict[str, Any]] = {}

    for lon, lat, elev in grid_points:
        assigned: Optional[Dict[str, Any]] = None

        # 1. Try point-in-polygon against master-district polygons only
        for district_name in sorted(master_with_polygon):
            geom = polygons[district_name]
            if point_in_geometry(lon, lat, geom):
                assigned = {
                    "district": district_name,
                    "normalized_district": f"{district_name} District",
                    "method": "polygon",
                    "distance_km": 0.0,
                    "is_fallback": "False",
                    "boundary_match_status": "matched",
                }
                break

        # 2. Fallback: nearest centroid among the 5 missing districts
        if assigned is None and fallback_names:
            best_dist = float("inf")
            best_name = None
            for name in fallback_names:
                c = centroids[name]
                d = haversine_km(lat, lon, c["latitude"], c["longitude"])
                if d < best_dist:
                    best_dist = d
                    best_name = name
            if best_name is not None:
                c = centroids[best_name]
                assigned = {
                    "district": best_name,
                    "normalized_district": c["normalized_district"],
                    "method": "nearest_centroid",
                    "distance_km": round(best_dist, 4),
                    "is_fallback": "True",
                    "boundary_match_status": "fallback_nearest_centroid",
                }

        # 3. If still unassigned (should not happen for this dataset)
        if assigned is None:
            assigned = {
                "district": "",
                "normalized_district": "",
                "method": "none",
                "distance_km": -1.0,
                "is_fallback": "False",
                "boundary_match_status": "unassigned",
            }

        mapping[(float(lon), float(lat))] = assigned

    return mapping


def extract_grid_points(weather_dir: Path = WEATHER_DIR) -> List[Tuple[float, float, float]]:
    """Extract the 117 unique grid points from the first available JSON file."""
    json_files = sorted(weather_dir.glob("*.json"))
    if not json_files:
        raise FileNotFoundError(f"no JSON files in {weather_dir}")
    with json_files[0].open("r", encoding="utf-8") as fh:
        doc = json.load(fh)
    points = []
    for feat in doc["features"]:
        coords = feat["geometry"]["coordinates"]
        points.append((float(coords[0]), float(coords[1]), float(coords[2])))
    return points


# ---------------------------------------------------------------------------
# Main join
# ---------------------------------------------------------------------------

def build_join_keys(
    weather_dir: Path = WEATHER_DIR,
    output_path: Path = OUTPUT_PATH,
) -> Dict[str, Any]:
    """Run the full spatial join and write the output CSV.

    Returns a summary dict with counts for the report.
    """
    polygons = load_polygons()
    centroids = load_district_centroids()
    fallback_names = identify_fallback_districts(polygons, centroids)
    grid_points = extract_grid_points(weather_dir)
    grid_mapping = build_grid_mapping(polygons, centroids, fallback_names, grid_points)

    json_files = sorted(weather_dir.glob("*.json"))
    total_records = 0
    polygon_matches = 0
    fallback_matches = 0
    unassigned = 0
    district_counts: Dict[str, int] = {}

    with output_path.open("w", encoding="utf-8", newline="") as fh:
        writer = csv.DictWriter(fh, fieldnames=OUTPUT_COLUMNS, lineterminator="\n")
        writer.writeheader()
        for jf in json_files:
            source_file = jf.name
            for rec in iter_records(jf):
                key = (rec["lon"], rec["lat"])
                assign = grid_mapping.get(key)
                if assign is None:
                    assign = {
                        "district": "",
                        "normalized_district": "",
                        "method": "none",
                        "distance_km": -1.0,
                        "is_fallback": "False",
                        "boundary_match_status": "unassigned",
                    }
                    unassigned += 1
                else:
                    if assign["method"] == "polygon":
                        polygon_matches += 1
                    elif assign["method"] == "nearest_centroid":
                        fallback_matches += 1

                d = assign["district"]
                if d:
                    district_counts[d] = district_counts.get(d, 0) + 1

                writer.writerow({
                    "source_file": source_file,
                    "source_parameter": rec["parameter"],
                    "source_date": rec["date"],
                    "grid_lon": rec["lon"],
                    "grid_lat": rec["lat"],
                    "grid_elevation_m": rec["elevation_m"],
                    "district": assign["district"],
                    "normalized_district": assign["normalized_district"],
                    "method": assign["method"],
                    "distance_km": assign["distance_km"],
                    "is_fallback": assign["is_fallback"],
                    "boundary_match_status": assign["boundary_match_status"],
                    "source_provider": "nasa_power_merra2",
                })
                total_records += 1

    return {
        "total_grid_points": len(grid_points),
        "total_records": total_records,
        "polygon_matches": polygon_matches,
        "fallback_matches": fallback_matches,
        "unassigned": unassigned,
        "fallback_districts": fallback_names,
        "district_counts": district_counts,
        "output_path": str(output_path),
        "json_files_processed": len(json_files),
    }


# ---------------------------------------------------------------------------
# Validation helpers (used by tests)
# ---------------------------------------------------------------------------

def validate_join_keys(csv_path: Path = OUTPUT_PATH) -> Dict[str, Any]:
    """Read the output CSV and return validation statistics."""
    rows: List[Dict[str, str]] = []
    with csv_path.open("r", encoding="utf-8", newline="") as fh:
        reader = csv.DictReader(fh)
        rows = list(reader)

    total = len(rows)
    methods = {}
    statuses = {}
    districts = set()
    grid_points = set()
    duplicate_keys = 0
    seen_keys = set()

    for r in rows:
        m = r["method"]
        methods[m] = methods.get(m, 0) + 1
        s = r["boundary_match_status"]
        statuses[s] = statuses.get(s, 0) + 1
        districts.add(r["district"])
        grid_points.add((r["grid_lon"], r["grid_lat"]))

        key = (r["source_file"], r["source_parameter"], r["source_date"],
               r["grid_lon"], r["grid_lat"])
        if key in seen_keys:
            duplicate_keys += 1
        seen_keys.add(key)

    # Districts with no coverage
    centroids = load_district_centroids()
    missing_coverage = sorted(set(centroids.keys()) - districts)

    return {
        "total_rows": total,
        "unique_grid_points": len(grid_points),
        "unique_districts": len(districts),
        "districts": sorted(districts),
        "methods": methods,
        "statuses": statuses,
        "duplicate_keys": duplicate_keys,
        "missing_district_coverage": missing_coverage,
        "columns": list(rows[0].keys()) if rows else [],
    }


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    summary = build_join_keys()
    print(f"Total grid points: {summary['total_grid_points']}")
    print(f"Total join rows:   {summary['total_records']}")
    print(f"Polygon matches:   {summary['polygon_matches']}")
    print(f"Fallback matches:  {summary['fallback_matches']}")
    print(f"Unassigned:        {summary['unassigned']}")
    print(f"Fallback districts: {summary['fallback_districts']}")
    print(f"Output: {summary['output_path']}")

    stats = validate_join_keys()
    print(f"\nValidation:")
    print(f"  Duplicate keys: {stats['duplicate_keys']}")
    print(f"  Missing coverage: {stats['missing_district_coverage']}")
    print(f"  Districts covered: {stats['unique_districts']}")
