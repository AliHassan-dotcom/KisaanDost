"""Service for district land utilization, crop acreage, and water availability statistics."""

from __future__ import annotations

import csv
import logging
from pathlib import Path
from typing import Any, Dict, List, Optional

from app.backend.schemas import (
    AgriGdpItem,
    AgriGdpResponse,
    AgriTradeItem,
    AgriTradeResponse,
    AgriTradeSummaryItem,
    AgriTradeSummaryResponse,
    LandUtilizationItem,
    LandUtilizationResponse,
    WaterAvailabilityItem,
    WaterAvailabilityResponse,
)
from app.config.settings import Settings

logger = logging.getLogger(__name__)


def _normalize_district(name: Optional[str]) -> Optional[str]:
    if not name:
        return None
    c = name.strip()
    if not c.lower().endswith("district"):
        return f"{c} District"
    return c


class AgriStatsService:
    def __init__(self, settings: Optional[Settings] = None):
        self.settings = settings or Settings()
        self._land_csv_path = self.settings.project_root / self.settings.land_utilization_csv_path
        self._water_csv_path = self.settings.project_root / self.settings.water_availability_csv_path
        self._gdp_csv_path = self.settings.project_root / self.settings.agri_gdp_csv_path
        self._exports_csv_path = self.settings.project_root / self.settings.agri_exports_csv_path
        self._imports_csv_path = self.settings.project_root / self.settings.agri_imports_csv_path
        self._trade_summary_csv_path = self.settings.project_root / self.settings.agri_trade_summary_csv_path

    def _load_land_records(self) -> List[Dict[str, Any]]:
        records: List[Dict[str, Any]] = []
        if not self._land_csv_path.exists():
            return records

        with open(self._land_csv_path, "r", encoding="utf-8", newline="") as fh:
            reader = csv.DictReader(fh)
            for r in reader:
                records.append(r)
        return records

    def _load_water_records(self) -> List[Dict[str, Any]]:
        records: List[Dict[str, Any]] = []
        if not self._water_csv_path.exists():
            return records

        with open(self._water_csv_path, "r", encoding="utf-8", newline="") as fh:
            reader = csv.DictReader(fh)
            for r in reader:
                records.append(r)
        return records

    def _load_csv_records(self, path: Path) -> List[Dict[str, Any]]:
        records: List[Dict[str, Any]] = []
        if not path.exists():
            return records
        with open(path, "r", encoding="utf-8", newline="") as fh:
            reader = csv.DictReader(fh)
            for r in reader:
                records.append(r)
        return records

    def get_land_utilization(self, district: Optional[str] = None) -> LandUtilizationResponse:
        records = self._load_land_records()
        norm_dist = _normalize_district(district).lower() if district else None

        items: List[LandUtilizationItem] = []
        for r in records:
            d_name = r["district"].strip()
            if norm_dist and norm_dist not in d_name.lower() and d_name.lower() not in norm_dist:
                continue

            items.append(
                LandUtilizationItem(
                    district=d_name,
                    total_farm_area_acres=float(r["total_farm_area_acres"]),
                    cultivated_area_acres=float(r["cultivated_area_acres"]),
                    uncultivated_area_acres=float(r["uncultivated_area_acres"]),
                    total_cropped_area_acres=float(r["total_cropped_area_acres"]),
                    cultivated_share_pct=float(r["cultivated_share_pct"]),
                    cropping_intensity_pct=float(r["cropping_intensity_pct"]),
                    wheat_area_acres=float(r["wheat_area_acres"]),
                    wheat_share_pct=float(r["wheat_share_pct"]),
                    rice_area_acres=float(r["rice_area_acres"]),
                    rice_share_pct=float(r["rice_share_pct"]),
                    cotton_area_acres=float(r["cotton_area_acres"]),
                    cotton_share_pct=float(r["cotton_share_pct"]),
                    sugarcane_area_acres=float(r["sugarcane_area_acres"]),
                    sugarcane_share_pct=float(r["sugarcane_share_pct"]),
                    maize_area_acres=float(r["maize_area_acres"]),
                    maize_share_pct=float(r["maize_share_pct"]),
                    fodder_area_acres=float(r["fodder_area_acres"]),
                    fodder_share_pct=float(r["fodder_share_pct"]),
                    orchard_area_acres=float(r["orchard_area_acres"]),
                    orchard_share_pct=float(r["orchard_share_pct"]),
                    kharif_total_acres=float(r["kharif_total_acres"]),
                    rabi_total_acres=float(r["rabi_total_acres"]),
                    data_source=r.get("data_source", "PBS 2024 Agricultural Census"),
                    source_year=int(r.get("source_year", 2024)),
                )
            )

        return LandUtilizationResponse(total_districts=len(items), data=items)

    def get_water_availability(self, district: Optional[str] = None) -> WaterAvailabilityResponse:
        records = self._load_water_records()
        norm_dist = _normalize_district(district).lower() if district else None

        items: List[WaterAvailabilityItem] = []
        for r in records:
            d_name = r["district"].strip()
            if norm_dist and norm_dist not in d_name.lower() and d_name.lower() not in norm_dist:
                continue

            items.append(
                WaterAvailabilityItem(
                    district=d_name,
                    total_cultivated_area_acres=float(r["total_cultivated_area_acres"]),
                    irrigated_area_acres=float(r["irrigated_area_acres"]),
                    unirrigated_area_acres=float(r["unirrigated_area_acres"]),
                    irrigation_coverage_pct=float(r["irrigation_coverage_pct"]),
                    canal_only_acres=float(r["canal_only_acres"]),
                    canal_only_pct=float(r["canal_only_pct"]),
                    canal_and_tubewell_acres=float(r["canal_and_tubewell_acres"]),
                    canal_and_tubewell_pct=float(r["canal_and_tubewell_pct"]),
                    tubewell_only_acres=float(r["tubewell_only_acres"]),
                    tubewell_only_pct=float(r["tubewell_only_pct"]),
                    barani_rainfed_acres=float(r["barani_rainfed_acres"]),
                    barani_share_pct=float(r["barani_share_pct"]),
                    sailaba_flood_acres=float(r["sailaba_flood_acres"]),
                    groundwater_reliance_pct=float(r["groundwater_reliance_pct"]),
                    canal_surface_reliance_pct=float(r["canal_surface_reliance_pct"]),
                    primary_irrigation_mode=r["primary_irrigation_mode"],
                    water_source_classification=r["water_source_classification"],
                    provincial_annual_canal_withdrawals_maf=float(r["provincial_annual_canal_withdrawals_maf"]),
                    provincial_per_capita_water_m3_year=float(r["provincial_per_capita_water_m3_year"]),
                    falkenmark_stress_category=r["falkenmark_stress_category"],
                    data_source=r.get("data_source", "PBS 2024 Agricultural Census / Economic Survey"),
                    source_year=int(r.get("source_year", 2024)),
                )
            )

        return WaterAvailabilityResponse(total_districts=len(items), data=items)

    def get_gdp(self, province: Optional[str] = None) -> AgriGdpResponse:
        records = self._load_csv_records(self._gdp_csv_path)
        norm_prov = province.strip().lower() if province else None

        items: List[AgriGdpItem] = []
        for r in records:
            reg = r["region"].strip()
            if norm_prov and norm_prov not in reg.lower() and reg.lower() not in norm_prov:
                continue

            items.append(
                AgriGdpItem(
                    fiscal_year=r["fiscal_year"],
                    region=reg,
                    agri_gdp_share_pct=float(r["agri_gdp_share_pct"]),
                    agri_growth_rate_pct=float(r["agri_growth_rate_pct"]),
                    crops_subsector_share_pct=float(r["crops_subsector_share_pct"]),
                    important_crops_share_pct=float(r["important_crops_share_pct"]),
                    other_crops_share_pct=float(r["other_crops_share_pct"]),
                    livestock_subsector_share_pct=float(r["livestock_subsector_share_pct"]),
                    forestry_subsector_share_pct=float(r["forestry_subsector_share_pct"]),
                    fishing_subsector_share_pct=float(r["fishing_subsector_share_pct"]),
                    punjab_agri_value_add_share_pct=float(r["punjab_agri_value_add_share_pct"]),
                    data_source=r.get("data_source", "Pakistan Economic Survey"),
                )
            )
        return AgriGdpResponse(total_records=len(items), data=items)

    def get_exports(self, commodity: Optional[str] = None) -> AgriTradeResponse:
        records = self._load_csv_records(self._exports_csv_path)
        query = commodity.strip().lower() if commodity else None

        items: List[AgriTradeItem] = []
        total_val = 0.0
        for r in records:
            c_name = r["commodity_name"].strip()
            c_group = r["commodity_group"].strip()
            if query and query not in c_name.lower() and query not in c_group.lower():
                continue

            val = float(r["value_million_usd"])
            total_val += val
            items.append(
                AgriTradeItem(
                    commodity_group=c_group,
                    commodity_name=c_name,
                    fiscal_year=r["fiscal_year"],
                    value_million_usd=val,
                    quantity_thousand_mt=float(r["quantity_thousand_mt"]),
                    share_of_trade_pct=float(r["share_of_agri_exports_pct"]),
                    partner_countries=r["primary_destinations"],
                    trade_type="export",
                    data_source=r.get("data_source", "PBS / Pakistan Economic Survey"),
                )
            )
        return AgriTradeResponse(
            trade_type="export",
            total_records=len(items),
            total_value_million_usd=round(total_val, 2),
            data=items,
        )

    def get_imports(self, commodity: Optional[str] = None) -> AgriTradeResponse:
        records = self._load_csv_records(self._imports_csv_path)
        query = commodity.strip().lower() if commodity else None

        items: List[AgriTradeItem] = []
        total_val = 0.0
        for r in records:
            c_name = r["commodity_name"].strip()
            c_group = r["commodity_group"].strip()
            if query and query not in c_name.lower() and query not in c_group.lower():
                continue

            val = float(r["value_million_usd"])
            total_val += val
            items.append(
                AgriTradeItem(
                    commodity_group=c_group,
                    commodity_name=c_name,
                    fiscal_year=r["fiscal_year"],
                    value_million_usd=val,
                    quantity_thousand_mt=float(r["quantity_thousand_mt"]),
                    share_of_trade_pct=float(r["share_of_agri_imports_pct"]),
                    partner_countries=r["primary_origins"],
                    trade_type="import",
                    data_source=r.get("data_source", "PBS / Pakistan Economic Survey"),
                )
            )
        return AgriTradeResponse(
            trade_type="import",
            total_records=len(items),
            total_value_million_usd=round(total_val, 2),
            data=items,
        )

    def get_trade_summary(self) -> AgriTradeSummaryResponse:
        records = self._load_csv_records(self._trade_summary_csv_path)
        items: List[AgriTradeSummaryItem] = []
        for r in records:
            items.append(
                AgriTradeSummaryItem(
                    fiscal_year=r["fiscal_year"],
                    total_agri_exports_million_usd=float(r["total_agri_exports_million_usd"]),
                    total_agri_imports_million_usd=float(r["total_agri_imports_million_usd"]),
                    agri_trade_balance_million_usd=float(r["agri_trade_balance_million_usd"]),
                    agri_share_of_total_national_exports_pct=float(r["agri_share_of_total_national_exports_pct"]),
                    agri_share_of_total_national_imports_pct=float(r["agri_share_of_total_national_imports_pct"]),
                    top_export_commodity=r["top_export_commodity"],
                    top_import_commodity=r["top_import_commodity"],
                    data_source=r.get("data_source", "Pakistan Economic Survey"),
                )
            )
        return AgriTradeSummaryResponse(total_records=len(items), data=items)


_service_instance: Optional[AgriStatsService] = None


def get_agri_stats_service() -> AgriStatsService:
    global _service_instance
    if _service_instance is None:
        _service_instance = AgriStatsService()
    return _service_instance

