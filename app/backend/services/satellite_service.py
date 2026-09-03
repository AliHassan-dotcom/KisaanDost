"""Read-only satellite data service providing historical Sentinel-2 district metrics.

Reads validated monthly satellite baseline data from:
- Kisaan_Dost_Data/processed/district_monthly_satellite_v1.csv
- Kisaan_Dost_Data/processed/district_monthly_satellite_coverage_v1.csv
- Kisaan_Dost_Data/processed/district_monthly_satellite_join_audit_v1.csv

Enforces strict provenance, null preservation, and explainable non-diagnostic attention status.
"""

from __future__ import annotations

import csv
import threading
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

from app.config import settings

MISSING_BOUNDARY_DISTRICTS = {
    "Bhakkar District", "Jhang District", "Layyah District",
    "Muzaffargarh District", "Okara District"
}

# Threshold for triggering vegetation / water attention indicators
ATTENTION_DELTA_THRESHOLD = 0.15


class SatelliteService:
    def __init__(
        self,
        satellite_path: Optional[Path] = None,
        coverage_path: Optional[Path] = None,
        audit_path: Optional[Path] = None,
    ) -> None:
        self._satellite_path = satellite_path or settings.satellite_csv_full_path()
        self._coverage_path = coverage_path or settings.satellite_coverage_csv_full_path()
        self._audit_path = audit_path or settings.satellite_join_audit_csv_full_path()
        self._lock = threading.Lock()

        # In-memory indices
        self._records_by_district: Dict[str, List[Dict[str, Any]]] = {}
        self._coverage_by_district: Dict[str, Dict[str, Any]] = {}
        self._audit_by_district: Dict[str, Dict[str, Any]] = {}
        self._district_aliases: Dict[str, str] = {}
        self._loaded = False

    def _ensure_loaded(self) -> None:
        if self._loaded:
            return
        with self._lock:
            if self._loaded:
                return
            self._load_data()
            self._loaded = True

    def _load_data(self) -> None:
        if not self._satellite_path.exists():
            raise FileNotFoundError(f"Satellite dataset missing: {self._satellite_path}")

        records_by_district: Dict[str, List[Dict[str, Any]]] = {}
        district_aliases: Dict[str, str] = {}

        # 1. Parse main monthly satellite CSV
        with self._satellite_path.open("r", encoding="utf-8", newline="") as fh:
            reader = csv.DictReader(fh)
            for row in reader:
                norm_d = row["normalized_district"].strip()
                simple_d = row["district"].strip()

                # Build lookup aliases (case-insensitive)
                district_aliases[norm_d.lower()] = norm_d
                district_aliases[simple_d.lower()] = norm_d

                record = {
                    "year": int(row["year"]),
                    "month": int(row["month"]),
                    "district": simple_d,
                    "normalized_district": norm_d,
                    "ndvi_mean": float(row["ndvi_mean"]) if row["ndvi_mean"].strip() else None,
                    "ndvi_median": float(row["ndvi_median"]) if row["ndvi_median"].strip() else None,
                    "ndwi_mean": float(row["ndwi_mean"]) if row["ndwi_mean"].strip() else None,
                    "ndwi_median": float(row["ndwi_median"]) if row["ndwi_median"].strip() else None,
                    "valid_pixel_count": int(row["valid_pixel_count"]) if row["valid_pixel_count"].strip() else None,
                    "observation_count": int(row["observation_count"]) if row["observation_count"].strip() else None,
                    "cloud_or_quality_fraction": float(row["cloud_or_quality_fraction"]) if row["cloud_or_quality_fraction"].strip() else None,
                    "satellite_source": row["satellite_source"],
                    "product_id": row["product_id"],
                    "spatial_scale_m": int(row["spatial_scale_m"]),
                    "period_start": row["period_start"],
                    "period_end": row["period_end"],
                    "data_status": row["data_status"],
                    "no_coverage_flag": row["no_coverage_flag"].strip().lower() == "true",
                    "quality_flag": row["quality_flag"],
                    "source_processing_timestamp": row["source_processing_timestamp"],
                }

                if norm_d not in records_by_district:
                    records_by_district[norm_d] = []
                records_by_district[norm_d].append(record)

        # Sort all district record lists chronologically
        for norm_d, records in records_by_district.items():
            records.sort(key=lambda r: (r["year"], r["month"]))
            # Compute explainable attention statuses across the district time-series
            self._compute_attention_indicators(records)

        self._records_by_district = records_by_district
        self._district_aliases = district_aliases

        # 2. Parse coverage summary
        if self._coverage_path.exists():
            with self._coverage_path.open("r", encoding="utf-8", newline="") as fh:
                for row in csv.DictReader(fh):
                    norm_d = row["normalized_district"].strip()
                    self._coverage_by_district[norm_d] = {
                        "district": row["district"].strip(),
                        "normalized_district": norm_d,
                        "has_authoritative_polygon": row["has_authoritative_polygon"].strip().lower() == "true",
                        "total_expected_months": int(row["total_expected_months"]),
                        "months_with_satellite_data": int(row["months_with_satellite_data"]),
                        "coverage_percentage": row["coverage_percentage"].strip(),
                        "data_status": row["data_status"].strip(),
                        "polygon_source": row["polygon_source"].strip(),
                        "notes": row["notes"].strip(),
                    }

        # 3. Parse join audit table
        if self._audit_path.exists():
            with self._audit_path.open("r", encoding="utf-8", newline="") as fh:
                for row in csv.DictReader(fh):
                    norm_d = row["normalized_district"].strip()
                    self._audit_by_district[norm_d] = dict(row)

    def _compute_attention_indicators(self, records: List[Dict[str, Any]]) -> None:
        """Compute conservative, explainable attention indicators across time-series."""
        last_valid_ndvi: Optional[float] = None
        last_valid_ndwi: Optional[float] = None
        last_valid_period: Optional[str] = None

        for rec in records:
            norm_d = rec["normalized_district"]

            if norm_d in MISSING_BOUNDARY_DISTRICTS or rec["data_status"] == "boundary_unavailable":
                rec["attention_status"] = "boundary_unavailable"
                rec["attention_evidence"] = (
                    "Authoritative district boundary polygon is unavailable in provincial GIS records. "
                    "Satellite zonal statistics are not estimated."
                )
            elif rec["data_status"] == "satellite_source_unavailable" or rec["no_coverage_flag"]:
                rec["attention_status"] = "insufficient_satellite_data"
                rec["attention_evidence"] = (
                    "High cloud or atmospheric mask in optical satellite overpass. "
                    "No clear pixels available for this month."
                )
            else:
                curr_ndvi = rec["ndvi_mean"]
                curr_ndwi = rec["ndwi_mean"]

                if curr_ndvi is None or curr_ndwi is None:
                    rec["attention_status"] = "insufficient_satellite_data"
                    rec["attention_evidence"] = "Incomplete spectral index metrics for this period."
                elif last_valid_ndvi is None:
                    # First chronological observation in baseline
                    rec["attention_status"] = "normal_observation"
                    rec["attention_evidence"] = (
                        f"Initial baseline observation: NDVI={curr_ndvi:.2f}, NDWI={curr_ndwi:.2f}."
                    )
                    last_valid_ndvi = curr_ndvi
                    last_valid_ndwi = curr_ndwi
                    last_valid_period = rec["period_start"]
                else:
                    delta_ndvi = curr_ndvi - last_valid_ndvi
                    delta_ndwi = curr_ndwi - last_valid_ndwi

                    if delta_ndvi < -ATTENTION_DELTA_THRESHOLD:
                        rec["attention_status"] = "vegetation_attention"
                        rec["attention_evidence"] = (
                            f"Canopy greenness index (NDVI) decreased by {abs(delta_ndvi):.2f} "
                            f"(from {last_valid_ndvi:.2f} in {last_valid_period} to {curr_ndvi:.2f}), "
                            f"exceeding the {ATTENTION_DELTA_THRESHOLD:.2f} threshold. "
                            "Non-diagnostic macro canopy vigor indicator."
                        )
                    elif delta_ndwi < -ATTENTION_DELTA_THRESHOLD:
                        rec["attention_status"] = "water_attention"
                        rec["attention_evidence"] = (
                            f"Canopy moisture index (NDWI) decreased by {abs(delta_ndwi):.2f} "
                            f"(from {last_valid_ndwi:.2f} in {last_valid_period} to {curr_ndwi:.2f}), "
                            f"exceeding the {ATTENTION_DELTA_THRESHOLD:.2f} threshold. "
                            "Non-diagnostic canopy hydration indicator."
                        )
                    else:
                        rec["attention_status"] = "normal_observation"
                        rec["attention_evidence"] = (
                            f"Monthly canopy greenness (NDVI={curr_ndvi:.2f}) and moisture (NDWI={curr_ndwi:.2f}) "
                            "remain within expected seasonal baseline parameters."
                        )

                    last_valid_ndvi = curr_ndvi
                    last_valid_ndwi = curr_ndwi
                    last_valid_period = rec["period_start"]

    def normalize_district(self, district_query: str) -> str:
        self._ensure_loaded()
        clean_q = district_query.strip().lower()
        if clean_q in self._district_aliases:
            return self._district_aliases[clean_q]
        raise ValueError(f"District '{district_query}' is not one of the 34 Punjab master districts.")

    def list_districts(self) -> List[Dict[str, Any]]:
        self._ensure_loaded()
        results: List[Dict[str, Any]] = []
        for norm_d in sorted(self._records_by_district.keys()):
            cov = self._coverage_by_district.get(norm_d, {})
            simple_d = norm_d.replace(" District", "")
            results.append({
                "district": simple_d,
                "normalized_district": norm_d,
                "has_authoritative_polygon": cov.get("has_authoritative_polygon", norm_d not in MISSING_BOUNDARY_DISTRICTS),
                "data_status": cov.get("data_status", "historical_satellite_baseline" if norm_d not in MISSING_BOUNDARY_DISTRICTS else "boundary_unavailable"),
                "coverage_percentage": cov.get("coverage_percentage", "100.0%" if norm_d not in MISSING_BOUNDARY_DISTRICTS else "0.0%"),
            })
        return results

    def get_latest(self, district: str) -> Dict[str, Any]:
        self._ensure_loaded()
        norm_d = self.normalize_district(district)
        records = self._records_by_district[norm_d]
        if not records:
            raise ValueError(f"No satellite records found for district: {norm_d}")
        # Last record in the 2022-2025 series
        return records[-1]

    def get_history(
        self,
        district: str,
        start_period: Optional[str] = None,
        end_period: Optional[str] = None,
    ) -> List[Dict[str, Any]]:
        self._ensure_loaded()
        norm_d = self.normalize_district(district)
        records = self._records_by_district[norm_d]

        filtered = records
        if start_period:
            clean_start = start_period.strip()
            filtered = [r for r in filtered if r["period_start"] >= f"{clean_start}-01" or r["period_start"] >= clean_start]
        if end_period:
            clean_end = end_period.strip()
            filtered = [r for r in filtered if r["period_start"] <= f"{clean_end}-31" or r["period_start"] <= clean_end]

        return filtered

    def get_coverage(self, district: str) -> Dict[str, Any]:
        self._ensure_loaded()
        norm_d = self.normalize_district(district)
        cov = self._coverage_by_district.get(norm_d)
        if cov:
            return cov

        has_poly = norm_d not in MISSING_BOUNDARY_DISTRICTS
        return {
            "district": norm_d.replace(" District", ""),
            "normalized_district": norm_d,
            "has_authoritative_polygon": has_poly,
            "total_expected_months": 48,
            "months_with_satellite_data": 48 if has_poly else 0,
            "coverage_percentage": "100.0%" if has_poly else "0.0%",
            "data_status": "historical_satellite_baseline" if has_poly else "boundary_unavailable",
            "polygon_source": "ArcGIS Punjab_District_Boundaries (WGS84)" if has_poly else "None",
            "notes": "Full 48-month cloud-masked monthly baseline" if has_poly else "Omitted from ArcGIS source GeoJSON (31 features); null metrics emitted.",
        }

    def satellite_summary(self, district: str, crop: str = "wheat") -> Dict[str, Any]:
        """Consolidated summary for dashboard and quick views."""
        try:
            latest = self.get_latest(district)
            status_map = {
                "historical_satellite_baseline": "historical",
                "satellite_source_unavailable": "cloud_masked_unavailable",
                "boundary_unavailable": "unavailable",
            }
            return {
                "district": latest["district"],
                "normalized_district": latest["normalized_district"],
                "crop": crop,
                "status": status_map.get(latest["data_status"], "historical"),
                "reason": latest["quality_flag"],
                "ndvi": latest["ndvi_mean"],
                "ndwi": latest["ndwi_mean"],
                "cloud_cover_percent": round(latest["cloud_or_quality_fraction"] * 100, 1) if latest["cloud_or_quality_fraction"] is not None else None,
                "last_clear_scene": latest["period_end"],
                "health_trend": latest["attention_status"],
                "attention_evidence": latest["attention_evidence"],
                "satellite_source": latest["satellite_source"],
                "product_id": latest["product_id"],
                "updated_at": latest["source_processing_timestamp"],
            }
        except Exception:  # noqa: BLE001
            return {
                "district": district,
                "normalized_district": f"{district} District" if not district.endswith(" District") else district,
                "crop": crop,
                "status": "unavailable",
                "reason": "district_not_found_or_uninitialized",
                "ndvi": None,
                "ndwi": None,
                "cloud_cover_percent": None,
                "last_clear_scene": None,
                "health_trend": "insufficient_satellite_data",
                "attention_evidence": "No satellite baseline records available for requested district.",
                "satellite_source": "Sentinel-2 MSI / MODIS Terra Baseline",
                "product_id": "COPERNICUS/S2_SR_HARMONIZED",
                "updated_at": None,
            }


_singleton: Optional[SatelliteService] = None
_singleton_lock = threading.Lock()


def get_satellite_service() -> SatelliteService:
    global _singleton
    if _singleton is None:
        with _singleton_lock:
            if _singleton is None:
                _singleton = SatelliteService()
    return _singleton


def satellite_summary(district: str, crop: str = "wheat") -> Dict[str, Any]:
    return get_satellite_service().satellite_summary(district, crop)
