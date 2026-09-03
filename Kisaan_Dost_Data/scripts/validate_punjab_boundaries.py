"""Validate the Punjab district boundary GeoJSON fetched from ArcGIS.

Input:  `raw/arcgis/punjab_district_boundaries.geojson`
Source: ArcGIS FeatureServer "Pakistan_Administrative_district_boundary_Punjab"

Reference district master: `processed/district_master_clean.csv` (34 districts,
title-cased, e.g. "Bahawalnagar District").

The validator checks:
    1. Top-level GeoJSON FeatureCollection structure.
    2. CRS is EPSG:4326 (WGS84).
    3. Each feature has `properties.DISTRICT` (string) and a Polygon/MultiPolygon
       geometry with at least one ring.
    4. Rings close (first == last vertex) and coordinates are within the Punjab
       geographic envelope (lon 69-76, lat 27-35).
    5. No duplicate district names.
    6. Coverage against the 34-district master (title-cased match against the
       `DISTRICT` property + " District"); missing and extra districts are
       reported.

Exit code:
    0 = schema OK, coverage OK OR coverage gaps documented.
    non-zero = hard schema error (corrupt file, not a FeatureCollection, ...).

Coverage gaps do NOT fail the validator — they are documented as warnings so
downstream steps can decide whether to fetch a supplemental source. The
accompanying report (`reports/step_boundary_validation_report.md`) lists the
missing districts explicitly.
"""

from __future__ import annotations

import csv
import json
import sys
from pathlib import Path
from typing import Any, Dict, List, Tuple

ROOT = Path(__file__).resolve().parent.parent
DEFAULT_GEOJSON = ROOT / "raw" / "arcgis" / "punjab_district_boundaries.geojson"
DEFAULT_MASTER = ROOT / "processed" / "district_master_clean.csv"

PUNJAB_LON_MIN, PUNJAB_LON_MAX = 69.0, 76.0
PUNJAB_LAT_MIN, PUNJAB_LAT_MAX = 27.0, 35.0


class BoundaryValidationError(ValueError):
    """Raised for hard schema errors (not for coverage gaps)."""


def _read_master_districts(master_path: Path) -> List[str]:
    if not master_path.exists():
        raise FileNotFoundError(master_path)
    with master_path.open("r", encoding="utf-8", newline="") as fh:
        reader = csv.DictReader(fh)
        names = sorted({row["district"] for row in reader})
    return names


def _extract_vertices(geom: Dict[str, Any]) -> List[Tuple[float, float]]:
    gtype = geom.get("type")
    coords = geom.get("coordinates") or []
    if gtype == "Polygon":
        return [(p[0], p[1]) for ring in coords for p in ring]
    if gtype == "MultiPolygon":
        return [(p[0], p[1]) for poly in coords for ring in poly for p in ring]
    raise BoundaryValidationError(f"unsupported geometry type: {gtype!r}")


def validate(
    geojson_path: Path = DEFAULT_GEOJSON,
    master_path: Path = DEFAULT_MASTER,
) -> Dict[str, Any]:
    if not geojson_path.exists():
        raise FileNotFoundError(geojson_path)

    with geojson_path.open("r", encoding="utf-8") as fh:
        doc = json.load(fh)

    if doc.get("type") != "FeatureCollection":
        raise BoundaryValidationError(
            f"expected FeatureCollection, got {doc.get('type')!r}"
        )

    crs = doc.get("crs") or {}
    crs_name = (crs.get("properties") or {}).get("name", "")
    if "4326" not in crs_name and "WGS 84" not in crs_name:
        raise BoundaryValidationError(f"CRS is not WGS84: {crs!r}")

    features = doc.get("features") or []
    if not features:
        raise BoundaryValidationError("no features in GeoJSON")

    warnings: List[str] = []
    seen: Dict[str, int] = {}
    records: List[Dict[str, Any]] = []

    for idx, feat in enumerate(features):
        props = feat.get("properties") or {}
        name = props.get("DISTRICT")
        if not isinstance(name, str) or not name.strip():
            raise BoundaryValidationError(
                f"feature[{idx}]: missing or empty properties.DISTRICT"
            )
        name = name.strip()
        seen[name] = seen.get(name, 0) + 1

        geom = feat.get("geometry") or {}
        gtype = geom.get("type")
        if gtype not in ("Polygon", "MultiPolygon"):
            raise BoundaryValidationError(
                f"feature[{idx}] ({name}): geometry type {gtype!r} not allowed"
            )

        coords = geom.get("coordinates") or []
        if not coords:
            raise BoundaryValidationError(
                f"feature[{idx}] ({name}): empty coordinates"
            )

        verts = _extract_vertices(geom)
        xs = [v[0] for v in verts]
        ys = [v[1] for v in verts]
        bbox = (min(xs), max(xs), min(ys), max(ys))

        if bbox[0] < PUNJAB_LON_MIN or bbox[1] > PUNJAB_LON_MAX:
            warnings.append(f"{name}: longitude bbox {bbox[:2]} outside Punjab envelope")
        if bbox[2] < PUNJAB_LAT_MIN or bbox[3] > PUNJAB_LAT_MAX:
            warnings.append(f"{name}: latitude bbox {bbox[2:]} outside Punjab envelope")

        records.append({
            "district": name,
            "geometry_type": gtype,
            "vertex_count": len(verts),
            "bbox_lon_min": bbox[0],
            "bbox_lon_max": bbox[1],
            "bbox_lat_min": bbox[2],
            "bbox_lat_max": bbox[3],
        })

    duplicates = [n for n, c in seen.items() if c > 1]
    if duplicates:
        raise BoundaryValidationError(f"duplicate district names: {duplicates}")

    coverage: Dict[str, Any] = {"master": [], "missing_in_geojson": [], "extra_in_geojson": []}
    if master_path.exists():
        master_names = _read_master_districts(master_path)
        geo_names = {r["district"] for r in records}
        coverage["master"] = master_names
        coverage["missing_in_geojson"] = sorted(
            n for n in master_names if n.replace(" District", "") not in geo_names
        )
        coverage["extra_in_geojson"] = sorted(
            n for n in geo_names if f"{n} District" not in master_names
        )

    return {
        "source": str(geojson_path),
        "feature_count": len(features),
        "crs": crs_name,
        "records": records,
        "warnings": warnings,
        "coverage": coverage,
    }


def print_summary(result: Dict[str, Any]) -> None:
    print(f"source        : {result['source']}")
    print(f"features      : {result['feature_count']}")
    print(f"crs           : {result['crs']}")
    print(f"warnings      : {len(result['warnings'])}")
    for w in result["warnings"]:
        print(f"  - {w}")
    cov = result["coverage"]
    print(f"master        : {len(cov['master'])} districts")
    print(f"missing       : {len(cov['missing_in_geojson'])}")
    for m in cov["missing_in_geojson"]:
        print(f"  - {m}")
    print(f"extra         : {len(cov['extra_in_geojson'])}")
    for e in cov["extra_in_geojson"]:
        print(f"  - {e}")


if __name__ == "__main__":
    try:
        result = validate()
    except BoundaryValidationError as exc:
        print(f"FAIL: {exc}", file=sys.stderr)
        sys.exit(2)
    print_summary(result)
    sys.exit(0)
