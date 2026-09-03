"""Market Price Service for AMIS Punjab official market prices, catalogs, and top movers."""

from __future__ import annotations

import csv
from datetime import datetime, timezone
import logging
from pathlib import Path
from typing import Any, Dict, List, Optional

from app.backend.schemas import (
    MarketCommoditiesResponse,
    MarketCommodityItem,
    MarketHistoryResponse,
    MarketLatestResponse,
    MarketMoverItem,
    MarketMoversResponse,
    MarketPriceItem,
)
from app.config.settings import Settings

logger = logging.getLogger(__name__)


class MarketService:
    def __init__(self, settings: Optional[Settings] = None):
        self.settings = settings or Settings()
        self._prices_path = self.settings.project_root / self.settings.amis_prices_csv_path
        self._commodities_path = self.settings.project_root / self.settings.amis_commodity_catalog_csv_path
        self._markets_path = self.settings.project_root / self.settings.amis_market_catalog_csv_path
        self._stale_days = self.settings.amis_stale_threshold_days

    def _load_commodities_catalog(self) -> List[MarketCommodityItem]:
        items: List[MarketCommodityItem] = []
        if not self._commodities_path.exists():
            return items

        with open(self._commodities_path, "r", encoding="utf-8", newline="") as fh:
            reader = csv.DictReader(fh)
            for r in reader:
                try:
                    items.append(
                        MarketCommodityItem(
                            commodity_id=int(r["commodity_id"]),
                            commodity_name=r["commodity_name"],
                            default_unit=r.get("default_unit", "Rs/100Kg"),
                            status=r.get("status", "allowlisted_phase7b"),
                        )
                    )
                except (ValueError, KeyError):
                    continue
        return items

    def _load_price_records(self) -> List[Dict[str, Any]]:
        records: List[Dict[str, Any]] = []
        if not self._prices_path.exists():
            return records

        with open(self._prices_path, "r", encoding="utf-8", newline="") as fh:
            reader = csv.DictReader(fh)
            for r in reader:
                records.append(r)
        return records

    def _parse_item(self, row: Dict[str, Any]) -> MarketPriceItem:
        price_date_str = row.get("price_date", "")
        retrieved_at_str = row.get("retrieved_at", "")

        source_age_days: Optional[int] = None
        if price_date_str:
            try:
                p_dt = datetime.strptime(price_date_str, "%Y-%m-%d").date()
                c_dt = datetime.now(timezone.utc).date()
                source_age_days = (c_dt - p_dt).days
            except ValueError:
                pass

        retrieval_age_hours: Optional[float] = None
        if retrieved_at_str:
            try:
                r_dt = datetime.fromisoformat(retrieved_at_str.replace("Z", "+00:00"))
                c_now = datetime.now(timezone.utc)
                retrieval_age_hours = round((c_now - r_dt).total_seconds() / 3600.0, 2)
            except Exception:
                pass

        data_status = "official_amis"
        warning: Optional[str] = None
        if source_age_days is not None and source_age_days > self._stale_days:
            data_status = "stale_official_record"
            warning = f"Official AMIS price record is from {price_date_str} ({source_age_days} days ago)."

        min_p = float(row["min_price_pkr"]) if row.get("min_price_pkr") else None
        max_p = float(row["max_price_pkr"]) if row.get("max_price_pkr") else None
        fqp_p = float(row["fqp_price_pkr"]) if row.get("fqp_price_pkr") else None
        qty = float(row["quantity"]) if row.get("quantity") else None

        return MarketPriceItem(
            record_id=row["record_id"],
            price_date=row["price_date"],
            source_displayed_date=row.get("source_displayed_date"),
            province=row.get("province", "Punjab"),
            district=row.get("district") or None,
            market_name=row["market_name"],
            market_id_or_source_label=row.get("market_id_or_source_label"),
            commodity_name=row["commodity_name"],
            commodity_id=int(row["commodity_id"]),
            variety=row.get("variety", "Standard"),
            min_price_raw=row.get("min_price_raw"),
            max_price_raw=row.get("max_price_raw"),
            fqp_price_raw=row.get("fqp_price_raw"),
            quantity_raw=row.get("quantity_raw"),
            unit_raw=row.get("unit_raw"),
            min_price_pkr=min_p,
            max_price_pkr=max_p,
            fqp_price_pkr=fqp_p,
            quantity=qty,
            unit=row.get("unit", "Rs/100Kg"),
            source_name=row.get("source_name", "Official AMIS Punjab"),
            source_url=row.get("source_url", "http://www.amis.pk/"),
            retrieved_at=retrieved_at_str,
            parser_version=row.get("parser_version", "amis_v1_phase7b"),
            data_status=data_status,
            validation_status=row.get("validation_status", "validated"),
            source_age_days=source_age_days,
            retrieval_age_hours=retrieval_age_hours,
            warning=warning,
        )

    def get_commodities(self) -> MarketCommoditiesResponse:
        catalog = self._load_commodities_catalog()
        return MarketCommoditiesResponse(
            total_commodities=len(catalog),
            commodities=catalog,
        )

    def get_latest(
        self,
        commodity: str,
        market: Optional[str] = None,
    ) -> MarketLatestResponse:
        all_rows = self._load_price_records()
        c_clean = commodity.strip().lower()
        m_clean = market.strip().lower() if market else None

        filtered = []
        for r in all_rows:
            r_cname = r.get("commodity_name", "").lower()
            if c_clean and c_clean not in r_cname and r_cname not in c_clean:
                continue
            if m_clean:
                r_mname = r.get("market_name", "").lower()
                r_dist = (r.get("district") or "").lower()
                if m_clean not in r_mname and r_mname not in m_clean and m_clean not in r_dist:
                    continue
            filtered.append(self._parse_item(r))

        return MarketLatestResponse(
            commodity=commodity,
            market=market,
            total_records=len(filtered),
            records=filtered,
        )

    def get_history(
        self,
        commodity: str,
        market: Optional[str] = None,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
    ) -> MarketHistoryResponse:
        all_rows = self._load_price_records()
        c_clean = commodity.strip().lower()
        m_clean = market.strip().lower() if market else None

        filtered = []
        for r in all_rows:
            r_cname = r.get("commodity_name", "").lower()
            if c_clean and c_clean not in r_cname and r_cname not in c_clean:
                continue
            if m_clean:
                r_mname = r.get("market_name", "").lower()
                r_dist = (r.get("district") or "").lower()
                if m_clean not in r_mname and r_mname not in m_clean and m_clean not in r_dist:
                    continue
            p_date = r.get("price_date", "")
            if start_date and p_date < start_date:
                continue
            if end_date and p_date > end_date:
                continue
            filtered.append(self._parse_item(r))

        return MarketHistoryResponse(
            commodity=commodity,
            market=market,
            start_date=start_date,
            end_date=end_date,
            total_records=len(filtered),
            records=filtered,
        )

    def get_movers(self) -> MarketMoversResponse:
        """Calculate observational price movers among active commodities with price data."""
        all_rows = self._load_price_records()
        items: List[MarketMoverItem] = []

        for r in all_rows:
            fqp = float(r["fqp_price_pkr"]) if r.get("fqp_price_pkr") else (
                float(r["max_price_pkr"]) if r.get("max_price_pkr") else (
                    float(r["min_price_pkr"]) if r.get("min_price_pkr") else None
                )
            )
            if fqp is None or fqp <= 0:
                continue

            cid = int(r["commodity_id"])
            cname = r["commodity_name"]
            mname = r["market_name"]
            pdate = r["price_date"]
            unit = r.get("unit", "Rs/100Kg")

            items.append(
                MarketMoverItem(
                    commodity_id=cid,
                    commodity_name=cname,
                    market_name=mname,
                    current_price_pkr=fqp,
                    previous_price_pkr=fqp,
                    price_change_pkr=0.0,
                    price_change_pct=0.0,
                    unit=unit,
                    price_date=pdate,
                    direction="stable",
                )
            )

        # Sort by price level
        gainers = sorted(items, key=lambda x: x.current_price_pkr, reverse=True)[:5]
        decliners = sorted(items, key=lambda x: x.current_price_pkr)[:5]

        return MarketMoversResponse(
            generated_at_utc=datetime.now(timezone.utc).isoformat(),
            tracked_count=len(items),
            gainers=gainers,
            decliners=decliners,
            data_status="official_amis" if items else "source_unavailable",
        )

    def market_summary(self, crop: str, district: str) -> Dict[str, Any]:
        """Legacy summary endpoint returning official AMIS or clean status."""
        latest_resp = self.get_latest(crop, market=district)
        if not latest_resp.records:
            latest_resp = self.get_latest(crop)

        if latest_resp.records:
            first = latest_resp.records[0]
            price_val = first.fqp_price_pkr or first.max_price_pkr or first.min_price_pkr
            return {
                "crop": crop,
                "district": district,
                "market": first.market_name,
                "status": first.data_status,
                "validation_status": first.validation_status,
                "unit": first.unit,
                "current_price": price_val,
                "min_price": first.min_price_pkr,
                "max_price": first.max_price_pkr,
                "fqp_price": first.fqp_price_pkr,
                "quantity": first.quantity,
                "source_displayed_date": first.source_displayed_date,
                "price_date": first.price_date,
                "source_name": first.source_name,
                "source_url": first.source_url,
                "retrieved_at": first.retrieved_at,
                "warning": first.warning,
            }

        return {
            "crop": crop,
            "district": district,
            "status": "source_unavailable",
            "reason": "no_official_amis_records_collected",
            "unit": "Rs/100Kg",
            "current_price": None,
            "sources": [],
        }

    def price_history(self, crop: str, district: str) -> List[Dict[str, Any]]:
        history_resp = self.get_history(crop, market=district)
        if not history_resp.records:
            history_resp = self.get_history(crop)
        return [r.model_dump() for r in history_resp.records]


_service_instance: Optional[MarketService] = None


def get_market_service() -> MarketService:
    global _service_instance
    if _service_instance is None:
        _service_instance = MarketService()
    return _service_instance


def market_summary(crop: str, district: str) -> Dict[str, Any]:
    return get_market_service().market_summary(crop, district)


def price_history(crop: str, district: str) -> List[Dict[str, Any]]:
    return get_market_service().price_history(crop, district)
