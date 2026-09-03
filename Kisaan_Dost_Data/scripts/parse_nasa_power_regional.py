"""Parse NASA POWER regional API JSON files into normalized records.

The regional endpoint returns the same GeoJSON schema as the point-level
API (see reports/nasa_power_regional_schema_report.md). This parser
handles regional baseline files from `raw/regional/`.

Two APIs:
    - `iter_records(path)` : generator, streaming-safe
    - `parse_file(path)`    : returns the full list (convenience wrapper)

The only difference from the point-level parser is the `source` field:
`"nasa_power_regional_merra2"` instead of `"nasa_power_merra2"`.

Stdlib only.
"""

from __future__ import annotations

import json
from datetime import date
from pathlib import Path
from typing import Any, Dict, Iterator, List, Union

FILL_VALUE = -999
SUPPORTED_PARAMETERS = {"T2M", "RH2M", "PRECTOTCORR"}
SOURCE_TAG = "nasa_power_regional_merra2"


class NasaPowerRegionalParseError(ValueError):
    """Raised when a file violates a hard structural invariant."""


def _validate_structure(doc: Dict[str, Any], path: Path) -> Dict[str, Any]:
    """Validate the top-level GeoJSON + NASA POWER envelope. Returns header."""
    if doc.get("type") != "FeatureCollection":
        raise NasaPowerRegionalParseError(
            f"{path}: expected type='FeatureCollection', got {doc.get('type')!r}"
        )
    if "features" not in doc:
        raise NasaPowerRegionalParseError(f"{path}: missing 'features' array")
    header = doc.get("header") or {}
    if header.get("fill_value") != FILL_VALUE:
        raise NasaPowerRegionalParseError(
            f"{path}: expected fill_value={FILL_VALUE}, got {header.get('fill_value')!r}"
        )

    features = doc["features"]
    if not isinstance(features, list):
        raise NasaPowerRegionalParseError(f"{path}: 'features' is not a list")
    if len(features) != 117:
        raise NasaPowerRegionalParseError(
            f"{path}: expected 117 features, got {len(features)}"
        )

    parameters = doc.get("parameters") or {}
    if len(parameters) != 1:
        raise NasaPowerRegionalParseError(
            f"{path}: expected exactly one entry in 'parameters', got {list(parameters)}"
        )
    declared_param = next(iter(parameters.keys()))
    if declared_param not in SUPPORTED_PARAMETERS:
        raise NasaPowerRegionalParseError(
            f"{path}: unsupported parameter {declared_param!r}"
        )

    return {
        "header": header,
        "parameters": parameters,
        "declared_param": declared_param,
    }


def _parse_date_key(key: str) -> date:
    if not isinstance(key, str) or len(key) != 8 or not key.isdigit():
        raise NasaPowerRegionalParseError(f"invalid date key: {key!r}")
    try:
        return date(int(key[:4]), int(key[4:6]), int(key[6:8]))
    except ValueError as exc:
        raise NasaPowerRegionalParseError(f"invalid date key: {key!r}") from exc


def iter_records(source: Union[str, Path]) -> Iterator[Dict[str, Any]]:
    """Yield normalized records from a single NASA POWER regional JSON file."""
    path = Path(source)
    with path.open("r", encoding="utf-8") as fh:
        doc = json.load(fh)

    meta = _validate_structure(doc, path)
    header = meta["header"]
    parameters = meta["parameters"]
    declared_param = meta["declared_param"]
    units = parameters[declared_param].get("units", "")

    start_key = header.get("start")
    end_key = header.get("end")
    start_d = _parse_date_key(start_key) if start_key else None
    end_d = _parse_date_key(end_key) if end_key else None

    file_path_str = str(path)

    for feat in doc["features"]:
        geom = feat.get("geometry") or {}
        if geom.get("type") != "Point":
            raise NasaPowerRegionalParseError(
                f"{path}: expected geometry.type='Point', got {geom.get('type')!r}"
            )
        coords = geom.get("coordinates") or []
        if len(coords) != 3:
            raise NasaPowerRegionalParseError(
                f"{path}: expected [lon, lat, elevation], got {coords!r}"
            )
        lon, lat, elevation = coords

        props = feat.get("properties") or {}
        param_block = props.get("parameter") or {}
        if set(param_block.keys()) != {declared_param}:
            raise NasaPowerRegionalParseError(
                f"{path}: feature parameter keys {set(param_block.keys())} "
                f"do not match declared {declared_param!r}"
            )
        daily = param_block[declared_param]

        for date_key, value in daily.items():
            d = _parse_date_key(date_key)
            if start_d and d < start_d:
                raise NasaPowerRegionalParseError(
                    f"{path}: date {d.isoformat()} before header.start {start_d.isoformat()}"
                )
            if end_d and d > end_d:
                raise NasaPowerRegionalParseError(
                    f"{path}: date {d.isoformat()} after header.end {end_d.isoformat()}"
                )
            if value == FILL_VALUE:
                continue
            yield {
                "source": SOURCE_TAG,
                "file_path": file_path_str,
                "parameter": declared_param,
                "units": units,
                "year": d.year,
                "month": d.month,
                "day": d.day,
                "date": d.isoformat(),
                "lon": float(lon),
                "lat": float(lat),
                "elevation_m": float(elevation),
                "value": float(value),
            }


def parse_file(source: Union[str, Path]) -> List[Dict[str, Any]]:
    """Convenience wrapper: materialize `iter_records()` into a list."""
    return list(iter_records(source))


def summarize_file(source: Union[str, Path]) -> Dict[str, Any]:
    """Return lightweight metadata + record count without materializing."""
    count = 0
    sample = None
    for rec in iter_records(source):
        count += 1
        if sample is None:
            sample = rec
    return {"file": str(source), "records": count, "sample": sample}


if __name__ == "__main__":
    import sys

    targets = sys.argv[1:]
    if not targets:
        targets = [str(Path(__file__).resolve().parent.parent / "raw" / "regional")]
    for t in targets:
        p = Path(t)
        files = sorted(p.glob("*.json")) if p.is_dir() else [p]
        for f in files:
            info = summarize_file(f)
            print(f"{info['file']}: {info['records']} records")
