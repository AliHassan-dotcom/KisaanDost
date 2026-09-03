"""Rule-based notification and alert evaluation engine for Kisaan Dost.

- Uses structured JSON tables (user_preferences.json and notifications.json) with atomic writes.
- Evaluates rule triggers for Weather Alerts (Open-Meteo), Market Movers (AMIS Punjab), and Advisory Reminders.
- Provides strict official attribution and zero ML/forecasting invariants.
"""

from __future__ import annotations

from datetime import datetime, timezone
import json
import logging
from pathlib import Path
import threading
from typing import Any, Dict, List, Optional
import uuid

from app.backend.schemas import (
    NotificationEvaluateResponse,
    NotificationItem,
    NotificationListResponse,
    NotificationMarkReadRequest,
    NotificationMarkReadResponse,
    NotificationPreferences,
    NotificationPreferencesResponse,
    NotificationPreferencesUpdateRequest,
    NotificationUnreadCountResponse,
)
from app.backend.services.market_service import MarketService, get_market_service
from app.backend.services.weather_service import WeatherService, get_weather_service
from app.config.settings import Settings

logger = logging.getLogger(__name__)

ATTR_WEATHER = "Weather data by Open-Meteo.com under CC BY 4.0"
ATTR_MARKET = "Market data by AMIS Punjab"
ATTR_ADVISORY = "Advisory based on official reports"


class NotificationService:
    def __init__(
        self,
        settings: Optional[Settings] = None,
        weather_service: Optional[WeatherService] = None,
        market_service: Optional[MarketService] = None,
    ):
        self.settings = settings or Settings()
        self.weather_service = weather_service or get_weather_service()
        self.market_service = market_service or get_market_service()
        self._lock = threading.Lock()

        self._storage_dir = self.settings.project_root / "data" / "processed"
        self._storage_dir.mkdir(parents=True, exist_ok=True)
        self._pref_file = self._storage_dir / "user_preferences.json"
        self._history_file = self._storage_dir / "notifications.json"

    def _load_preferences_dict(self) -> Dict[str, Any]:
        with self._lock:
            if not self._pref_file.exists():
                return {}
            try:
                with open(self._pref_file, "r", encoding="utf-8") as fh:
                    return json.load(fh)
            except Exception as e:
                logger.warning(f"Error loading notification preferences: {e}")
                return {}

    def _save_preferences_dict(self, data: Dict[str, Any]) -> None:
        with self._lock:
            temp_file = self._pref_file.with_suffix(".tmp")
            with open(temp_file, "w", encoding="utf-8") as fh:
                json.dump(data, fh, indent=2)
            temp_file.replace(self._pref_file)

    def _load_history_list(self) -> List[Dict[str, Any]]:
        with self._lock:
            if not self._history_file.exists():
                return []
            try:
                with open(self._history_file, "r", encoding="utf-8") as fh:
                    return json.load(fh)
            except Exception as e:
                logger.warning(f"Error loading notification history: {e}")
                return []

    def _save_history_list(self, items: List[Dict[str, Any]]) -> None:
        with self._lock:
            temp_file = self._history_file.with_suffix(".tmp")
            with open(temp_file, "w", encoding="utf-8") as fh:
                json.dump(items, fh, indent=2)
            temp_file.replace(self._history_file)

    def get_preferences(self, user_id: str = "default_farmer") -> NotificationPreferencesResponse:
        prefs_data = self._load_preferences_dict()
        user_pref = prefs_data.get(user_id)
        now_iso = datetime.now(timezone.utc).isoformat()

        if not user_pref:
            pref = NotificationPreferences(
                user_id=user_id,
                selected_district="Lahore District",
                selected_market="Lahore",
                selected_crops=["Wheat", "Rice Basmati Super (New)", "Cotton", "Potato Fresh"],
                alert_types=["weather", "market", "advisory"],
                channels=["in_app", "local"],
                enable_weather_alerts=True,
                enable_market_alerts=True,
                enable_advisory_reminders=True,
                heatwave_temp_threshold=40.0,
                rainfall_threshold_mm=25.0,
                frost_temp_threshold=3.0,
                market_mover_threshold_pct=10.0,
                fcm_token=None,
                fcm_status="not_configured",
                updated_at_utc=now_iso,
            )
            prefs_data[user_id] = pref.model_dump()
            self._save_preferences_dict(prefs_data)
            return NotificationPreferencesResponse(preferences=pref)

        pref = NotificationPreferences.model_validate(user_pref)
        return NotificationPreferencesResponse(preferences=pref)

    def update_preferences(
        self,
        req: NotificationPreferencesUpdateRequest,
        user_id: str = "default_farmer",
    ) -> NotificationPreferencesResponse:
        current_res = self.get_preferences(user_id)
        p = current_res.preferences
        now_iso = datetime.now(timezone.utc).isoformat()

        updated = NotificationPreferences(
            user_id=user_id,
            selected_district=req.selected_district or p.selected_district,
            selected_market=req.selected_market or p.selected_market,
            selected_crops=req.selected_crops if req.selected_crops is not None else p.selected_crops,
            alert_types=req.alert_types if req.alert_types is not None else p.alert_types,
            channels=req.channels if req.channels is not None else p.channels,
            enable_weather_alerts=req.enable_weather_alerts if req.enable_weather_alerts is not None else p.enable_weather_alerts,
            enable_market_alerts=req.enable_market_alerts if req.enable_market_alerts is not None else p.enable_market_alerts,
            enable_advisory_reminders=req.enable_advisory_reminders if req.enable_advisory_reminders is not None else p.enable_advisory_reminders,
            heatwave_temp_threshold=req.heatwave_temp_threshold if req.heatwave_temp_threshold is not None else p.heatwave_temp_threshold,
            rainfall_threshold_mm=req.rainfall_threshold_mm if req.rainfall_threshold_mm is not None else p.rainfall_threshold_mm,
            frost_temp_threshold=req.frost_temp_threshold if req.frost_temp_threshold is not None else p.frost_temp_threshold,
            market_mover_threshold_pct=req.market_mover_threshold_pct if req.market_mover_threshold_pct is not None else p.market_mover_threshold_pct,
            fcm_token=req.fcm_token if req.fcm_token is not None else p.fcm_token,
            fcm_status="configured" if (req.fcm_token or p.fcm_token) else "not_configured",
            updated_at_utc=now_iso,
        )

        prefs_data = self._load_preferences_dict()
        prefs_data[user_id] = updated.model_dump()
        self._save_preferences_dict(prefs_data)
        return NotificationPreferencesResponse(preferences=updated)

    def get_history(self, user_id: str = "default_farmer", unread_only: bool = False) -> NotificationListResponse:
        history = self._load_history_list()
        user_items = [r for r in history if r.get("user_id") == user_id]

        if unread_only:
            user_items = [r for r in user_items if not r.get("is_read", False)]

        items = [NotificationItem.model_validate(r) for r in user_items]
        # Sort descending by created_at
        items.sort(key=lambda x: x.created_at_utc, reverse=True)
        unread = sum(1 for x in items if not x.is_read)

        return NotificationListResponse(
            total_notifications=len(items),
            unread_count=unread,
            notifications=items,
        )

    def get_unread_count(self, user_id: str = "default_farmer") -> NotificationUnreadCountResponse:
        history = self._load_history_list()
        user_items = [r for r in history if r.get("user_id") == user_id]
        unread = sum(1 for r in user_items if not r.get("is_read", False))
        return NotificationUnreadCountResponse(
            unread_count=unread,
            total_notifications=len(user_items),
        )

    def mark_as_read(self, notification_id: str, user_id: str = "default_farmer") -> bool:
        history = self._load_history_list()
        found = False
        for r in history:
            if r.get("id") == notification_id and r.get("user_id") == user_id:
                r["is_read"] = True
                found = True
        if found:
            self._save_history_list(history)
        return found

    def mark_multiple_read(
        self,
        req: NotificationMarkReadRequest,
        user_id: str = "default_farmer",
    ) -> NotificationMarkReadResponse:
        history = self._load_history_list()
        marked = 0
        target_ids = set(req.notification_ids or [])

        for r in history:
            if r.get("user_id") == user_id and not r.get("is_read", False):
                if req.mark_all or r.get("id") in target_ids:
                    r["is_read"] = True
                    marked += 1

        if marked > 0:
            self._save_history_list(history)

        return NotificationMarkReadResponse(marked_count=marked, success=True)

    def evaluate_rules(self, user_id: str = "default_farmer") -> NotificationEvaluateResponse:
        pref = self.get_preferences(user_id).preferences
        now_iso = datetime.now(timezone.utc).isoformat()
        new_alerts: List[NotificationItem] = []

        history = self._load_history_list()
        recent_ids = {r.get("id") for r in history}

        # 1. Weather Rule Evaluation
        if pref.enable_weather_alerts and "weather" in pref.alert_types:
            try:
                w_current = self.weather_service.current(pref.selected_district)
                temp = float(w_current.get("temperature_c") or 25.0)
                precip = float(w_current.get("precipitation_mm") or 0.0)

                # Heatwave Alert
                if temp >= pref.heatwave_temp_threshold:
                    nid = f"notif_heat_{pref.selected_district}_{now_iso[:10]}"
                    if nid not in recent_ids:
                        new_alerts.append(
                            NotificationItem(
                                id=nid,
                                user_id=user_id,
                                type="weather_alert",
                                title=f"Heatwave Alert: {temp:.1f}°C in {pref.selected_district}",
                                title_ur=f"شدید گرمی کی وارننگ: {pref.selected_district} میں درجہ حرارت {temp:.1f}°C",
                                message=f"Extreme temperature recorded ({temp:.1f}°C). Protect sensitive crops and schedule evening irrigation.",
                                message_ur=f"شدید گرمی ({temp:.1f}°C) ریکارڈ کی گئی ہے۔ فصلوں کو دھوپ کے دباؤ سے بچائیں اور شام کو پانی دیں۔",
                                severity="warning" if temp < 43 else "critical",
                                created_at_utc=now_iso,
                                source_attribution=ATTR_WEATHER,
                                metadata={"temperature_c": temp, "district": pref.selected_district},
                            )
                        )
                        recent_ids.add(nid)

                # Heavy Rain Alert
                if precip >= pref.rainfall_threshold_mm:
                    nid = f"notif_rain_{pref.selected_district}_{now_iso[:10]}"
                    if nid not in recent_ids:
                        new_alerts.append(
                            NotificationItem(
                                id=nid,
                                user_id=user_id,
                                type="weather_alert",
                                title=f"Heavy Rain Alert: {precip:.1f}mm in {pref.selected_district}",
                                title_ur=f"تیز بارش کی وارننگ: {pref.selected_district} میں {precip:.1f} ملی میٹر بارش",
                                message=f"Heavy rainfall detected ({precip:.1f}mm). Suspend chemical spraying and check field drainage.",
                                message_ur=f"تیز بارش ({precip:.1f} ملی میٹر) متوقع ہے۔ سپرے روک دیں اور کھیتوں سے نکاسی کا انتظام کریں۔",
                                severity="warning",
                                created_at_utc=now_iso,
                                source_attribution=ATTR_WEATHER,
                                metadata={"precipitation_mm": precip, "district": pref.selected_district},
                            )
                        )
                        recent_ids.add(nid)

                # Frost Risk Alert
                if temp <= pref.frost_temp_threshold:
                    nid = f"notif_frost_{pref.selected_district}_{now_iso[:10]}"
                    if nid not in recent_ids:
                        new_alerts.append(
                            NotificationItem(
                                id=nid,
                                user_id=user_id,
                                type="weather_alert",
                                title=f"Frost Risk Alert: {temp:.1f}°C in {pref.selected_district}",
                                title_ur=f"کورا پڑنے کا خدشہ: {pref.selected_district} میں درجہ حرارت {temp:.1f}°C",
                                message=f"Low temperature detected ({temp:.1f}°C). Apply light irrigation or mulching to shield vegetables/orchards.",
                                message_ur=f"کم ترین درجہ حرارت ({temp:.1f}°C) ریکارڈ۔ سبزیوں اور باغات کو کورے سے بچانے کیلئے ہلکا پانی لگائیں۔",
                                severity="warning",
                                created_at_utc=now_iso,
                                source_attribution=ATTR_WEATHER,
                                metadata={"temperature_c": temp, "district": pref.selected_district},
                            )
                        )
                        recent_ids.add(nid)
            except Exception as e:
                logger.warning(f"Error evaluating weather alerts: {e}")

        # 2. Market Mover Rule Evaluation
        if pref.enable_market_alerts and "market" in pref.alert_types:
            try:
                movers = self.market_service.get_movers()
                for m in movers.gainers + movers.decliners:
                    if m.commodity_name in pref.selected_crops or not pref.selected_crops:
                        pct = abs(m.price_change_pct or 0.0)
                        if pct >= pref.market_mover_threshold_pct or m.current_price_pkr > 0:
                            nid = f"notif_market_{m.commodity_name}_{now_iso[:10]}"
                            if nid not in recent_ids:
                                dir_str = "increased" if m.direction == "up" else ("decreased" if m.direction == "down" else "traded")
                                dir_ur = "اضافہ" if m.direction == "up" else ("کمی" if m.direction == "down" else "مستحکم")
                                new_alerts.append(
                                    NotificationItem(
                                        id=nid,
                                        user_id=user_id,
                                        type="market_mover",
                                        title=f"Market Update: {m.commodity_name} in {m.market_name}",
                                        title_ur=f"مارکیٹ ریٹ: {m.commodity_name} ({m.market_name} منڈی)",
                                        message=f"{m.commodity_name} rate {dir_str} to Rs. {m.current_price_pkr:,.0f}/{m.unit} ({m.price_date}).",
                                        message_ur=f"{m.commodity_name} کی قیمت {m.current_price_pkr:,.0f} روپے فی {m.unit} ریکارڈ ({dir_ur})۔",
                                        severity="info",
                                        created_at_utc=now_iso,
                                        source_attribution=ATTR_MARKET,
                                        metadata={"commodity": m.commodity_name, "price_pkr": m.current_price_pkr, "market": m.market_name},
                                    )
                                )
                                recent_ids.add(nid)
            except Exception as e:
                logger.warning(f"Error evaluating market alerts: {e}")

        # 3. Advisory Reminder Rule Evaluation
        if pref.enable_advisory_reminders and "advisory" in pref.alert_types:
            try:
                w_current = self.weather_service.current(pref.selected_district)
                wind = float(w_current.get("wind_speed_kmh") or 10.0)
                precip = float(w_current.get("precipitation_mm") or 0.0)

                # Spray Window Reminder
                if wind < 15.0 and precip < 1.0:
                    nid = f"notif_spray_{pref.selected_district}_{now_iso[:10]}"
                    if nid not in recent_ids:
                        new_alerts.append(
                            NotificationItem(
                                id=nid,
                                user_id=user_id,
                                type="advisory_reminder",
                                title=f"Optimal Spray Window: {pref.selected_district}",
                                title_ur=f"سپرے کیلئے سازگار موسم: {pref.selected_district}",
                                message=f"Favorable calm weather (Wind: {wind:.1f} km/h, Rain: {precip:.1f}mm). Ideal conditions for crop protection sprays.",
                                message_ur=f"ہوا کی رفتار {wind:.1f} کلومیٹر فی گھنٹہ اور بارش کا امکان نہیں۔ حفاظتی سپرے کیلئے موزوں وقت۔",
                                severity="info",
                                created_at_utc=now_iso,
                                source_attribution=ATTR_ADVISORY,
                                metadata={"wind_kmh": wind, "precipitation_mm": precip},
                            )
                        )
                        recent_ids.add(nid)
            except Exception as e:
                logger.warning(f"Error evaluating advisory reminders: {e}")

        # Save new alerts to history
        if new_alerts:
            for item in new_alerts:
                history.append(item.model_dump())
            self._save_history_list(history)

        return NotificationEvaluateResponse(
            evaluated_at_utc=now_iso,
            new_alerts_count=len(new_alerts),
            new_alerts=new_alerts,
        )


_service_instance: Optional[NotificationService] = None


def get_notification_service() -> NotificationService:
    global _service_instance
    if _service_instance is None:
        _service_instance = NotificationService()
    return _service_instance
