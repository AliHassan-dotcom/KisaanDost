"""Unit and integration tests for Open-Meteo live weather & forecast API."""

from __future__ import annotations

import httpx
import pytest
from fastapi.testclient import TestClient

from app.backend.main import app
from app.backend.services.weather_service import WeatherService, get_weather_service


@pytest.fixture
def client() -> TestClient:
    return TestClient(app)


@pytest.fixture
def auth_headers(client: TestClient) -> dict[str, str]:
    resp = client.post(
        "/api/v1/auth/register",
        json={"phone": "03007654321", "password": "password123", "name": "Weather Farmer"},
    )
    if resp.status_code == 409:
        resp = client.post(
            "/api/v1/auth/login",
            json={"phone": "03007654321", "password": "password123"},
        )
    token = resp.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}


SAMPLE_OPEN_METEO_CURRENT = {
    "latitude": 31.52,
    "longitude": 74.36,
    "current": {
        "time": "2026-09-01T12:00",
        "temperature_2m": 34.2,
        "relative_humidity_2m": 58,
        "precipitation": 0.0,
        "wind_speed_10m": 11.5,
        "weather_code": 1,
    },
}

SAMPLE_OPEN_METEO_FORECAST = {
    "latitude": 31.52,
    "longitude": 74.36,
    "daily": {
        "time": ["2026-09-01", "2026-09-02", "2026-09-03"],
        "temperature_2m_max": [35.1, 36.0, 34.8],
        "precipitation_sum": [0.0, 2.5, 0.0],
        "precipitation_probability_max": [10, 45, 15],
        "shortwave_radiation_sum": [22.4, 21.0, 23.1],
        "et0_fao_evapotranspiration": [5.2, 4.8, 5.5],
    },
    "hourly": {
        "time": ["2026-09-01T00:00", "2026-09-01T01:00"],
        "temperature_2m": [28.0, 27.5],
        "relative_humidity_2m": [70, 72],
        "dewpoint_2m": [22.1, 22.0],
        "precipitation": [0.0, 0.0],
        "vapour_pressure_deficit": [1.2, 1.1],
        "et0_fao_evapotranspiration": [0.1, 0.1],
        "wind_speed_10m": [8.0, 7.5],
        "wind_gusts_10m": [12.0, 11.0],
        "weather_code": [0, 0],
        "soil_temperature_0cm": [29.0, 28.5],
        "soil_temperature_6cm": [29.5, 29.2],
        "soil_temperature_18cm": [30.0, 29.8],
        "soil_moisture_0_to_1cm": [0.18, 0.18],
        "soil_moisture_1_to_3cm": [0.20, 0.20],
        "soil_moisture_3_to_9cm": [0.22, 0.22],
        "soil_moisture_9_to_27cm": [0.25, 0.25],
        "shortwave_radiation": [0.0, 0.0],
        "direct_normal_irradiance": [0.0, 0.0],
    },
}


class MockHttpClient:
    def __init__(self, sample_resp=SAMPLE_OPEN_METEO_CURRENT, should_fail=False):
        self.sample_resp = sample_resp
        self.should_fail = should_fail
        self.call_count = 0

    def get(self, url: str):
        self.call_count += 1
        if self.should_fail:
            raise httpx.ConnectError("Connection refused by upstream")
        
        # Return mock Response
        req = httpx.Request("GET", url)
        return httpx.Response(status_code=200, json=self.sample_resp, request=req)


def test_weather_districts_list(client: TestClient):
    resp = client.get("/api/v1/weather/districts")
    assert resp.status_code == 200
    districts = resp.json()["districts"]
    assert len(districts) >= 34
    assert "Lahore" in districts
    assert "Faisalabad" in districts
    assert "Multan" in districts


def test_weather_current_mock_upstream(monkeypatch, client: TestClient):
    mock_client = MockHttpClient(sample_resp=SAMPLE_OPEN_METEO_CURRENT)
    test_svc = WeatherService(http_client=mock_client)
    app.dependency_overrides[get_weather_service] = lambda: test_svc

    try:
        resp = client.get("/api/v1/weather/current?district=Lahore")
        assert resp.status_code == 200
        data = resp.json()["data"]
        assert data["district"] == "Lahore"
        assert data["status"] == "live"
        assert data["temperature_c"] == 34.2
        assert data["humidity_percent"] == 58.0
        assert data["precipitation_mm"] == 0.0
        assert data["wind_speed_kmh"] == 11.5
        assert data["weather_code"] == 1
        assert data["weather_description"] == "Mainly clear"
        assert data["cache_status"] == "fresh_live"
        assert "Open-Meteo" in data["source"]
        assert "Open-Meteo.com" in data["attribution"]
        assert data["is_mock"] is False
    finally:
        app.dependency_overrides.pop(get_weather_service, None)


def test_weather_current_caching(monkeypatch, client: TestClient):
    mock_client = MockHttpClient(sample_resp=SAMPLE_OPEN_METEO_CURRENT)
    test_svc = WeatherService(http_client=mock_client)
    app.dependency_overrides[get_weather_service] = lambda: test_svc

    try:
        # First call -> fresh_live
        resp1 = client.get("/api/v1/weather/current?district=Lahore")
        assert resp1.status_code == 200
        assert resp1.json()["data"]["cache_status"] == "fresh_live"
        assert mock_client.call_count == 1

        # Second call -> cached_live without additional upstream fetch
        resp2 = client.get("/api/v1/weather/current?district=Lahore")
        assert resp2.status_code == 200
        assert resp2.json()["data"]["cache_status"] == "cached_live"
        assert mock_client.call_count == 1
    finally:
        app.dependency_overrides.pop(get_weather_service, None)


def test_weather_current_stale_fallback(monkeypatch, client: TestClient):
    mock_client = MockHttpClient(sample_resp=SAMPLE_OPEN_METEO_CURRENT)
    test_svc = WeatherService(http_client=mock_client)
    app.dependency_overrides[get_weather_service] = lambda: test_svc

    try:
        # 1. Warm cache
        resp1 = client.get("/api/v1/weather/current?district=Faisalabad")
        assert resp1.status_code == 200
        orig_fetched_at = resp1.json()["data"]["fetched_at"]

        # 2. Expire primary cache and simulate upstream failure
        mock_client.should_fail = True
        test_svc._cache.clear()  # force cache miss to trigger upstream call

        # 3. Call should return stale fallback
        resp2 = client.get("/api/v1/weather/current?district=Faisalabad")
        assert resp2.status_code == 200
        data = resp2.json()["data"]
        assert data["status"] == "stale_live_cache"
        assert data["cache_status"] == "stale_fallback"
        assert data["fetched_at"] == orig_fetched_at
        assert "temporarily unreachable" in data["warning"]
        assert data["temperature_c"] == 34.2
    finally:
        app.dependency_overrides.pop(get_weather_service, None)


def test_weather_current_unavailable_no_cache(monkeypatch, client: TestClient):
    mock_client = MockHttpClient(should_fail=True)
    test_svc = WeatherService(http_client=mock_client)
    app.dependency_overrides[get_weather_service] = lambda: test_svc

    try:
        resp = client.get("/api/v1/weather/current?district=Multan")
        assert resp.status_code == 200
        data = resp.json()["data"]
        assert data["status"] == "unavailable"
        assert data["temperature_c"] is None
        assert data["is_mock"] is False
        assert "unavailable" in data["warning"].lower()
    finally:
        app.dependency_overrides.pop(get_weather_service, None)


def test_weather_forecast_endpoint(monkeypatch, client: TestClient):
    mock_client = MockHttpClient(sample_resp=SAMPLE_OPEN_METEO_FORECAST)
    test_svc = WeatherService(http_client=mock_client)
    app.dependency_overrides[get_weather_service] = lambda: test_svc

    try:
        resp = client.get("/api/v1/weather/forecast?district=Lahore&days=3")
        assert resp.status_code == 200
        data = resp.json()["data"]
        assert data["district"] == "Lahore"
        assert data["status"] == "live"
        assert len(data["daily"]) == 3
        assert len(data["hourly"]) == 2
        assert data["daily"][0]["temperature_2m_max"] == 35.1
        assert data["daily"][0]["precipitation_sum"] == 0.0
        assert data["hourly"][0]["relative_humidity_2m"] == 70.0
        assert "Open-Meteo" in data["source"]
    finally:
        app.dependency_overrides.pop(get_weather_service, None)


def test_weather_rejects_arbitrary_coordinates(client: TestClient):
    resp = client.get("/api/v1/weather/current?district=Lahore&latitude=31.5204&longitude=74.3587")
    assert resp.status_code == 400
    assert "Direct coordinates are disallowed" in resp.json()["detail"]


def test_weather_historical_endpoint(client: TestClient):
    resp = client.get("/api/v1/weather/historical?district=Faisalabad")
    assert resp.status_code == 200
    data = resp.json()["data"]
    assert len(data) >= 40  # 48 months of NASA POWER 2022-2025
    first = data[0]
    assert first["status"] == "historical"
    assert "temperature_c" in first
    assert "humidity_percent" in first
    assert "rainfall_mm" in first
    assert "nasa_power" in first["source"].lower()


def test_dashboard_weather_integration(client: TestClient, auth_headers: dict[str, str]):
    resp = client.get("/api/v1/dashboard", headers=auth_headers)
    assert resp.status_code == 200
    data = resp.json()
    assert "weather" in data
    weather = data["weather"]
    assert "district" in weather
    assert "temperature_c" in weather
    assert "status" in weather
