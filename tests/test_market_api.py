"""Tests for FastAPI Market API and AMIS Punjab integration (Phase 7B)."""

from __future__ import annotations

import pytest
from starlette.testclient import TestClient

from app.backend.main import app
from app.backend.services.market_service import MarketService, get_market_service


@pytest.fixture
def client() -> TestClient:
    return TestClient(app)


def test_market_commodities_endpoint(client: TestClient):
    resp = client.get("/api/v1/market/commodities")
    assert resp.status_code == 200
    body = resp.json()
    assert body["success"] is True
    data = body["data"]
    assert data["total_commodities"] >= 10
    names = [c["commodity_name"] for c in data["commodities"]]
    assert "Wheat" in names
    assert "Rice Basmati Super (New)" in names
    assert "Tomato" in names
    assert "Onion" in names


def test_market_latest_endpoint(client: TestClient):
    resp = client.get("/api/v1/market/latest?commodity=Wheat")
    assert resp.status_code == 200
    body = resp.json()
    assert body["success"] is True
    data = body["data"]
    assert data["commodity"] == "Wheat"
    assert data["total_records"] >= 1
    rec = data["records"][0]
    assert rec["commodity_name"] == "Wheat"
    assert rec["unit"] == "Rs/100Kg"
    assert rec["source_name"] == "Official AMIS Punjab"
    assert "http://www.amis.pk/" in rec["source_url"]
    assert rec["district"] == "Lahore District"  # Populated via verified mapping


def test_market_movers_endpoint(client: TestClient):
    resp = client.get("/api/v1/market/movers")
    assert resp.status_code == 200
    body = resp.json()
    assert body["success"] is True
    data = body["data"]
    assert "gainers" in data
    assert "decliners" in data
    assert data["tracked_count"] >= 1
    assert data["data_status"] == "official_amis"
    if data["gainers"]:
        g = data["gainers"][0]
        assert g["current_price_pkr"] > 0
        assert g["unit"] == "Rs/100Kg"


def test_market_history_with_valid_dates(client: TestClient):
    resp = client.get("/api/v1/market/history?commodity=Wheat&start=2026-01-01&end=2026-12-31")
    assert resp.status_code == 200
    body = resp.json()
    assert body["success"] is True
    data = body["data"]
    assert data["commodity"] == "Wheat"
    assert isinstance(data["records"], list)


def test_market_history_rejects_invalid_date(client: TestClient):
    resp = client.get("/api/v1/market/history?commodity=Wheat&start=invalid-date")
    assert resp.status_code == 400
    assert "Invalid date format" in resp.json()["detail"]


def test_market_summary_endpoint(client: TestClient):
    resp = client.get("/api/v1/market/summary?crop=Wheat&district=Lahore")
    assert resp.status_code == 200
    body = resp.json()
    assert body["success"] is True
    data = body["data"]
    assert data["crop"] == "Wheat"
    assert data["unit"] == "Rs/100Kg"


def test_market_unavailable_for_unknown_crop(client: TestClient):
    resp = client.get("/api/v1/market/summary?crop=Dragonfruit&district=Lahore")
    assert resp.status_code == 200
    body = resp.json()
    assert body["success"] is True
    data = body["data"]
    assert data["status"] == "source_unavailable"
    assert data["current_price"] is None
