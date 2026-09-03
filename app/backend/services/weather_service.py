"""Open-Meteo live weather service with in-memory TTL caching and NASA POWER historical baseline.

- Resolves district coordinates strictly from processed/district_coordinates.csv.
- Integrates Open-Meteo forecast API (ECMWF IFS / DWD ICON) with strict parameter ordering.
- Implements thread-safe in-memory caching with 30-min (current) and 60-min (forecast) TTLs.
- Supports stale-live fallback on upstream failures.
- Preserves NASA POWER monthly historical baseline under historical().
"""

from __future__ import annotations

import csv
from datetime import datetime, timedelta, timezone
import logging
from pathlib import Path
import threading
from typing import Any, Dict, List, Optional, Tuple
from urllib.parse import urlencode

import httpx

from app.config import settings

logger = logging.getLogger(__name__)

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
ATTRIBUTION = "Weather data by Open-Meteo.com under CC BY 4.0"
SOURCE_NAME = "Open-Meteo / ECMWF IFS / DWD ICON"

WMO_WEATHER_CODES: Dict[int, str] = {
    0: "Clear sky",
    1: "Mainly clear",
    2: "Partly cloudy",
    3: "Overcast",
    45: "Fog",
    48: "Depositing rime fog",
    51: "Light drizzle",
    53: "Moderate drizzle",
    55: "Dense drizzle",
    56: "Light freezing drizzle",
    57: "Dense freezing drizzle",
    61: "Slight rain",
    62: "Moderate rain",
    63: "Moderate rain",
    65: "Heavy rain",
    66: "Light freezing rain",
    67: "Heavy freezing rain",
    71: "Slight snow fall",
    73: "Moderate snow fall",
    75: "Heavy snow fall",
    77: "Snow grains",
    80: "Slight rain showers",
    81: "Moderate rain showers",
    82: "Violent rain showers",
    85: "Slight snow showers",
    86: "Heavy snow showers",
    95: "Thunderstorm",
    96: "Thunderstorm with slight hail",
    99: "Thunderstorm with heavy hail",
}


def weather_code_to_text(code: Optional[int]) -> str:
    if code is None:
        return "Unknown"
    return WMO_WEATHER_CODES.get(int(code), f"Weather code {code}")


class DistrictNotFoundError(KeyError):
    """Raised when a district name cannot be resolved in district_coordinates.csv."""


class WeatherService:
    def __init__(
        self,
        coords_path: Optional[Path] = None,
        historical_path: Optional[Path] = None,
        http_client: Optional[httpx.Client] = None,
    ) -> None:
        self.coords_path = coords_path or settings.coordinates_csv_full_path()
        self.historical_path = historical_path or settings.weather_csv_full_path()
        self._custom_client = http_client

        self._lock = threading.Lock()
        self._coords_by_name: Dict[str, Dict[str, Any]] = {}
        self._historical_rows: Optional[List[Dict[str, Any]]] = None

        # In-memory TTL caches: key -> {"data": dict, "expires_at": datetime, "fetched_at": str}
        self._cache: Dict[str, Dict[str, Any]] = {}
        self._stale_cache: Dict[str, Dict[str, Any]] = {}

    def _ensure_coords_loaded(self) -> None:
        if self._coords_by_name:
            return
        with self._lock:
            if self._coords_by_name:
                return
            if not self.coords_path.exists():
                logger.warning(f"District coordinates CSV not found at {self.coords_path}")
                return
            with open(self.coords_path, "r", encoding="utf-8", newline="") as fh:
                reader = csv.DictReader(fh)
                for row in reader:
                    district_name = row["district"].strip()
                    norm_name = row["normalized_district"].strip()
                    entry = {
                        "district": district_name,
                        "normalized_district": norm_name,
                        "latitude": float(row["latitude"]),
                        "longitude": float(row["longitude"]),
                        "is_master_district": row.get("is_master_district", "True").lower() == "true",
                        "notes": row.get("notes", ""),
                    }
                    self._coords_by_name[district_name.lower()] = entry
                    self._coords_by_name[norm_name.lower()] = entry
                    clean_name = district_name.lower().replace(" district", "")
                    self._coords_by_name[clean_name] = entry

    def resolve_district(self, name: str) -> Dict[str, Any]:
        self._ensure_coords_loaded()
        cleaned = name.strip().lower()
        if cleaned.endswith(" district"):
            cleaned = cleaned[:-len(" district")].strip()
        if cleaned in self._coords_by_name:
            return self._coords_by_name[cleaned]
        if name.strip().lower() in self._coords_by_name:
            return self._coords_by_name[name.strip().lower()]
        available = sorted({v["district"] for v in self._coords_by_name.values()})
        raise DistrictNotFoundError(
            f"District '{name}' not found in coordinates table. Available: {available}"
        )

    def districts(self) -> List[str]:
        self._ensure_coords_loaded()
        if self._coords_by_name:
            unique = {v["district"] for v in self._coords_by_name.values()}
            return sorted(unique, key=str.lower)
        # Fallback to historical CSV if coords not yet loaded
        rows = self._load_historical()
        names = {str(r["district"]).strip() for r in rows if r.get("district")}
        return sorted(names, key=str.lower)

    def _build_url(self, lat: float, lon: float, forecast_days: int = 7) -> str:
        params = [
            ("latitude", f"{lat:.4f}"),
            ("longitude", f"{lon:.4f}"),
            ("current", ",".join(CURRENT_VARS)),
            ("hourly", ",".join(HOURLY_VARS)),
            ("daily", ",".join(DAILY_VARS)),
            ("models", ",".join(MODELS)),
            ("timezone", TIMEZONE),
            ("forecast_days", str(min(max(forecast_days, 1), 10))),
        ]
        return f"{OPEN_METEO_BASE}?{urlencode(params, safe=',')}"

    def _fetch_upstream(self, url: str) -> Dict[str, Any]:
        timeout = settings.open_meteo_timeout_seconds
        if self._custom_client:
            resp = self._custom_client.get(url)
            resp.raise_for_status()
            return resp.json()

        with httpx.Client(timeout=timeout) as client:
            resp = client.get(url)
            resp.raise_for_status()
            return resp.json()

    def current(self, district: str) -> Dict[str, Any]:
        try:
            info = self.resolve_district(district)
        except DistrictNotFoundError:
            return self._mock(district, reason="district_not_in_coordinate_table")

        lat = info["latitude"]
        lon = info["longitude"]
        norm_name = info["normalized_district"]
        cache_key = f"current:{norm_name.lower()}"
        now = datetime.now(timezone.utc)

        with self._lock:
            cached = self._cache.get(cache_key)
            if cached and cached["expires_at"] > now:
                entry = dict(cached["data"])
                entry["cache_status"] = "cached_live"
                return entry

        # Attempt fresh upstream fetch
        url = self._build_url(lat, lon, forecast_days=1)
        try:
            raw = self._fetch_upstream(url)
            current_raw = raw.get("current") or {}

            temp_c = current_raw.get("temperature_2m")
            rh = current_raw.get("relative_humidity_2m")
            precip = current_raw.get("precipitation")
            wind_spd = current_raw.get("wind_speed_10m")
            wcode = current_raw.get("weather_code")

            fetched_at_str = now.isoformat()
            expires_at = now + timedelta(seconds=settings.open_meteo_current_ttl_seconds)

            data: Dict[str, Any] = {
                "district": info["district"],
                "normalized_district": norm_name,
                "latitude": lat,
                "longitude": lon,
                "status": "live",
                "temperature_c": float(temp_c) if temp_c is not None else None,
                "humidity_percent": float(rh) if rh is not None else None,
                "rainfall_mm": float(precip) if precip is not None else 0.0,
                "precipitation_mm": float(precip) if precip is not None else 0.0,
                "wind_speed_kmh": float(wind_spd) if wind_spd is not None else None,
                "weather_code": int(wcode) if wcode is not None else None,
                "weather_description": weather_code_to_text(wcode),
                "fetched_at": fetched_at_str,
                "expires_at": expires_at.isoformat(),
                "cache_status": "fresh_live",
                "source": SOURCE_NAME,
                "attribution": ATTRIBUTION,
                "is_mock": False,
                "warning": None,
            }

            with self._lock:
                self._cache[cache_key] = {"data": data, "expires_at": expires_at, "fetched_at": fetched_at_str}
                self._stale_cache[cache_key] = dict(data)

            return data

        except Exception as exc:
            logger.warning(f"Open-Meteo current weather fetch failed for {district}: {exc}")
            with self._lock:
                if cache_key in self._stale_cache:
                    stale = dict(self._stale_cache[cache_key])
                    stale["status"] = "stale_live_cache"
                    stale["cache_status"] = "stale_fallback"
                    stale["warning"] = f"Upstream weather provider temporarily unreachable. Showing cached observation from {stale.get('fetched_at')}."
                    return stale

            return {
                "district": info["district"],
                "normalized_district": norm_name,
                "latitude": lat,
                "longitude": lon,
                "status": "unavailable",
                "temperature_c": None,
                "humidity_percent": None,
                "rainfall_mm": 0.0,
                "precipitation_mm": None,
                "wind_speed_kmh": None,
                "weather_code": None,
                "weather_description": "Unavailable",
                "fetched_at": now.isoformat(),
                "expires_at": None,
                "cache_status": "upstream_error",
                "source": SOURCE_NAME,
                "attribution": ATTRIBUTION,
                "is_mock": False,
                "warning": "Live weather data is currently unavailable from upstream provider.",
            }

    def forecast(self, district: str, days: int = 7) -> Dict[str, Any]:
        days = min(max(days, 1), 10)
        try:
            info = self.resolve_district(district)
        except DistrictNotFoundError:
            return {
                "district": district,
                "normalized_district": f"{district} District",
                "latitude": 0.0,
                "longitude": 0.0,
                "status": "unavailable",
                "forecast_days": days,
                "daily": [],
                "hourly": [],
                "source": SOURCE_NAME,
                "attribution": ATTRIBUTION,
                "warning": f"District '{district}' not recognized.",
            }

        lat = info["latitude"]
        lon = info["longitude"]
        norm_name = info["normalized_district"]
        cache_key = f"forecast:{norm_name.lower()}:{days}"
        now = datetime.now(timezone.utc)

        with self._lock:
            cached = self._cache.get(cache_key)
            if cached and cached["expires_at"] > now:
                entry = dict(cached["data"])
                entry["cache_status"] = "cached_live"
                return entry

        url = self._build_url(lat, lon, forecast_days=days)
        try:
            raw = self._fetch_upstream(url)
            daily_raw = raw.get("daily") or {}
            hourly_raw = raw.get("hourly") or {}

            # Parse daily series
            daily_items: List[Dict[str, Any]] = []
            dates = daily_raw.get("time") or []
            t_max = daily_raw.get("temperature_2m_max") or []
            precip_sum = daily_raw.get("precipitation_sum") or []
            precip_prob = daily_raw.get("precipitation_probability_max") or []
            rad_sum = daily_raw.get("shortwave_radiation_sum") or []
            et0 = daily_raw.get("et0_fao_evapotranspiration") or []

            for i, d in enumerate(dates):
                daily_items.append({
                    "date": d,
                    "temperature_2m_max": float(t_max[i]) if i < len(t_max) and t_max[i] is not None else None,
                    "temperature_2m_min": None,
                    "precipitation_sum": float(precip_sum[i]) if i < len(precip_sum) and precip_sum[i] is not None else None,
                    "precipitation_probability_max": float(precip_prob[i]) if i < len(precip_prob) and precip_prob[i] is not None else None,
                    "shortwave_radiation_sum": float(rad_sum[i]) if i < len(rad_sum) and rad_sum[i] is not None else None,
                    "et0_fao_evapotranspiration": float(et0[i]) if i < len(et0) and et0[i] is not None else None,
                })

            # Parse hourly series
            hourly_items: List[Dict[str, Any]] = []
            h_times = hourly_raw.get("time") or []
            h_temp = hourly_raw.get("temperature_2m") or []
            h_rh = hourly_raw.get("relative_humidity_2m") or []
            h_dew = hourly_raw.get("dewpoint_2m") or []
            h_precip = hourly_raw.get("precipitation") or []
            h_vpd = hourly_raw.get("vapour_pressure_deficit") or []
            h_et0 = hourly_raw.get("et0_fao_evapotranspiration") or []
            h_wind = hourly_raw.get("wind_speed_10m") or []
            h_gust = hourly_raw.get("wind_gusts_10m") or []
            h_wcode = hourly_raw.get("weather_code") or []
            h_soil_t0 = hourly_raw.get("soil_temperature_0cm") or []
            h_soil_t6 = hourly_raw.get("soil_temperature_6cm") or []
            h_soil_t18 = hourly_raw.get("soil_temperature_18cm") or []
            h_soil_m0 = hourly_raw.get("soil_moisture_0_to_1cm") or []
            h_soil_m1 = hourly_raw.get("soil_moisture_1_to_3cm") or []
            h_soil_m3 = hourly_raw.get("soil_moisture_3_to_9cm") or []
            h_soil_m9 = hourly_raw.get("soil_moisture_9_to_27cm") or []
            h_rad = hourly_raw.get("shortwave_radiation") or []
            h_dni = hourly_raw.get("direct_normal_irradiance") or []

            for i, t in enumerate(h_times):
                hourly_items.append({
                    "time": t,
                    "temperature_2m": float(h_temp[i]) if i < len(h_temp) and h_temp[i] is not None else None,
                    "relative_humidity_2m": float(h_rh[i]) if i < len(h_rh) and h_rh[i] is not None else None,
                    "dewpoint_2m": float(h_dew[i]) if i < len(h_dew) and h_dew[i] is not None else None,
                    "precipitation": float(h_precip[i]) if i < len(h_precip) and h_precip[i] is not None else None,
                    "vapour_pressure_deficit": float(h_vpd[i]) if i < len(h_vpd) and h_vpd[i] is not None else None,
                    "et0_fao_evapotranspiration": float(h_et0[i]) if i < len(h_et0) and h_et0[i] is not None else None,
                    "wind_speed_10m": float(h_wind[i]) if i < len(h_wind) and h_wind[i] is not None else None,
                    "wind_gusts_10m": float(h_gust[i]) if i < len(h_gust) and h_gust[i] is not None else None,
                    "weather_code": int(h_wcode[i]) if i < len(h_wcode) and h_wcode[i] is not None else None,
                    "soil_temperature_0cm": float(h_soil_t0[i]) if i < len(h_soil_t0) and h_soil_t0[i] is not None else None,
                    "soil_temperature_6cm": float(h_soil_t6[i]) if i < len(h_soil_t6) and h_soil_t6[i] is not None else None,
                    "soil_temperature_18cm": float(h_soil_t18[i]) if i < len(h_soil_t18) and h_soil_t18[i] is not None else None,
                    "soil_moisture_0_to_1cm": float(h_soil_m0[i]) if i < len(h_soil_m0) and h_soil_m0[i] is not None else None,
                    "soil_moisture_1_to_3cm": float(h_soil_m1[i]) if i < len(h_soil_m1) and h_soil_m1[i] is not None else None,
                    "soil_moisture_3_to_9cm": float(h_soil_m3[i]) if i < len(h_soil_m3) and h_soil_m3[i] is not None else None,
                    "soil_moisture_9_to_27cm": float(h_soil_m9[i]) if i < len(h_soil_m9) and h_soil_m9[i] is not None else None,
                    "shortwave_radiation": float(h_rad[i]) if i < len(h_rad) and h_rad[i] is not None else None,
                    "direct_normal_irradiance": float(h_dni[i]) if i < len(h_dni) and h_dni[i] is not None else None,
                })

            fetched_at_str = now.isoformat()
            expires_at = now + timedelta(seconds=settings.open_meteo_forecast_ttl_seconds)

            data: Dict[str, Any] = {
                "district": info["district"],
                "normalized_district": norm_name,
                "latitude": lat,
                "longitude": lon,
                "status": "live",
                "forecast_days": days,
                "fetched_at": fetched_at_str,
                "expires_at": expires_at.isoformat(),
                "cache_status": "fresh_live",
                "daily": daily_items,
                "hourly": hourly_items,
                "source": SOURCE_NAME,
                "attribution": ATTRIBUTION,
                "warning": None,
            }

            with self._lock:
                self._cache[cache_key] = {"data": data, "expires_at": expires_at, "fetched_at": fetched_at_str}
                self._stale_cache[cache_key] = dict(data)

            return data

        except Exception as exc:
            logger.warning(f"Open-Meteo forecast fetch failed for {district}: {exc}")
            with self._lock:
                if cache_key in self._stale_cache:
                    stale = dict(self._stale_cache[cache_key])
                    stale["status"] = "stale_live_cache"
                    stale["cache_status"] = "stale_fallback"
                    stale["warning"] = f"Upstream forecast provider temporarily unreachable. Showing cached forecast from {stale.get('fetched_at')}."
                    return stale

            return {
                "district": info["district"],
                "normalized_district": norm_name,
                "latitude": lat,
                "longitude": lon,
                "status": "unavailable",
                "forecast_days": days,
                "fetched_at": now.isoformat(),
                "expires_at": None,
                "cache_status": "upstream_error",
                "daily": [],
                "hourly": [],
                "source": SOURCE_NAME,
                "attribution": ATTRIBUTION,
                "warning": "Forecast data is currently unavailable from upstream provider.",
            }

    def _load_historical(self) -> List[Dict[str, Any]]:
        if self._historical_rows is not None:
            return self._historical_rows
        rows: List[Dict[str, Any]] = []
        if not self.historical_path.exists():
            self._historical_rows = rows
            return rows
        with open(self.historical_path, "r", encoding="utf-8", newline="") as fh:
            for row in csv.DictReader(fh):
                rows.append(dict(row))
        self._historical_rows = rows
        return rows

    def historical(self, district: str) -> List[Dict[str, Any]]:
        rows = self._load_historical()
        target = district.strip().lower()
        if target.endswith(" district"):
            target = target[:-len(" district")].strip()

        matched = [
            r for r in rows
            if str(r.get("district") or "").strip().lower() == target
            or str(r.get("normalized_district") or "").strip().lower() == target
            or str(r.get("normalized_district") or "").strip().lower() == f"{target} district"
        ]

        return [
            {
                "district": r.get("district", district),
                "normalized_district": r.get("normalized_district", f"{district} District"),
                "year": int(r["year"]),
                "month": int(r["month"]),
                "temperature_c": float(r["t2m_mean_c"]),
                "humidity_percent": float(r["rh2m_mean_percent"]),
                "rainfall_mm": float(r["precip_total_mm"]),
                "status": "historical",
                "source": r.get("source_provider", "NASA POWER Monthly Agroclimatology"),
                "source_files": r.get("source_files_covered"),
            }
            for r in matched
        ]

    def _mock(self, district: str, reason: str) -> Dict[str, Any]:
        return {
            "district": district,
            "normalized_district": f"{district} District",
            "latitude": 31.5204,
            "longitude": 74.3587,
            "status": "mock",
            "reason": reason,
            "temperature_c": 28.0,
            "humidity_percent": 55.0,
            "rainfall_mm": 0.0,
            "precipitation_mm": 0.0,
            "wind_speed_kmh": 12.0,
            "weather_code": 1,
            "weather_description": "Mainly clear",
            "fetched_at": datetime.now(timezone.utc).isoformat(),
            "expires_at": None,
            "cache_status": "mock",
            "source": "Mock Weather Baseline",
            "attribution": ATTRIBUTION,
            "is_mock": True,
            "warning": "Mock weather data for offline/testing mode.",
        }


_weather_service: Optional[WeatherService] = None
_weather_service_lock = threading.Lock()


def get_weather_service() -> WeatherService:
    global _weather_service
    if _weather_service is None:
        with _weather_service_lock:
            if _weather_service is None:
                _weather_service = WeatherService()
    return _weather_service
