"""Tests for Agricultural Statistics & Water Availability FastAPI endpoints (Phase 8)."""

from __future__ import annotations

import pytest
from starlette.testclient import TestClient

from app.backend.main import app


@pytest.fixture
def client() -> TestClient:
    return TestClient(app)


def test_land_utilization_all_districts(client: TestClient):
    resp = client.get("/api/v1/agri/land-utilization")
    assert resp.status_code == 200
    body = resp.json()
    assert body["success"] is True
    data = body["data"]
    assert data["total_districts"] >= 30
    assert len(data["data"]) >= 30

    d0 = data["data"][0]
    assert "district" in d0
    assert d0["total_farm_area_acres"] > 0
    assert d0["cultivated_area_acres"] > 0
    assert d0["wheat_area_acres"] >= 0
    assert d0["source_year"] == 2024
    assert "PBS 2024" in d0["data_source"]


def test_land_utilization_district_filter(client: TestClient):
    resp = client.get("/api/v1/agri/land-utilization?district=Lahore")
    assert resp.status_code == 200
    body = resp.json()
    assert body["success"] is True
    data = body["data"]
    assert data["total_districts"] == 1
    lahore = data["data"][0]
    assert "Lahore" in lahore["district"]
    assert lahore["wheat_area_acres"] > 0
    assert lahore["cultivated_share_pct"] > 0


def test_water_availability_all_districts(client: TestClient):
    resp = client.get("/api/v1/agri/water-availability")
    assert resp.status_code == 200
    body = resp.json()
    assert body["success"] is True
    data = body["data"]
    assert data["total_districts"] >= 30

    d0 = data["data"][0]
    assert "irrigation_coverage_pct" in d0
    assert d0["provincial_annual_canal_withdrawals_maf"] == 53.5
    assert d0["provincial_per_capita_water_m3_year"] == 860.0


def test_water_availability_district_filter(client: TestClient):
    resp = client.get("/api/v1/agri/water-availability?district=Rawalpindi")
    assert resp.status_code == 200
    body = resp.json()
    assert body["success"] is True
    data = body["data"]
    assert data["total_districts"] == 1
    rp = data["data"][0]
    assert "Rawalpindi" in rp["district"]
    assert rp["barani_share_pct"] > 50.0
    assert "Barani" in rp["primary_irrigation_mode"]


def test_agri_gdp_all(client: TestClient):
    resp = client.get("/api/v1/agri/gdp")
    assert resp.status_code == 200
    body = resp.json()
    assert body["success"] is True
    data = body["data"]
    assert data["total_records"] >= 6
    rec = data["data"][0]
    assert "agri_gdp_share_pct" in rec
    assert "crops_subsector_share_pct" in rec
    assert "livestock_subsector_share_pct" in rec


def test_agri_gdp_punjab_filter(client: TestClient):
    resp = client.get("/api/v1/agri/gdp?province=Punjab")
    assert resp.status_code == 200
    body = resp.json()
    assert body["success"] is True
    data = body["data"]
    assert data["total_records"] >= 1
    rec = data["data"][0]
    assert rec["region"] == "Punjab"


def test_agri_exports_endpoint(client: TestClient):
    resp = client.get("/api/v1/agri/exports")
    assert resp.status_code == 200
    body = resp.json()
    assert body["success"] is True
    data = body["data"]
    assert data["trade_type"] == "export"
    assert data["total_records"] >= 5
    assert data["total_value_million_usd"] > 4000.0


def test_agri_exports_commodity_filter(client: TestClient):
    resp = client.get("/api/v1/agri/exports?commodity=Rice")
    assert resp.status_code == 200
    body = resp.json()
    assert body["success"] is True
    data = body["data"]
    assert data["total_records"] >= 2
    for item in data["data"]:
        assert "Rice" in item["commodity_name"]


def test_agri_imports_endpoint(client: TestClient):
    resp = client.get("/api/v1/agri/imports")
    assert resp.status_code == 200
    body = resp.json()
    assert body["success"] is True
    data = body["data"]
    assert data["trade_type"] == "import"
    assert data["total_records"] >= 5
    assert data["total_value_million_usd"] > 6000.0


def test_agri_trade_summary_endpoint(client: TestClient):
    resp = client.get("/api/v1/agri/trade-summary")
    assert resp.status_code == 200
    body = resp.json()
    assert body["success"] is True
    data = body["data"]
    assert data["total_records"] >= 1
    sum_rec = data["data"][0]
    assert sum_rec["total_agri_exports_million_usd"] > 0
    assert sum_rec["total_agri_imports_million_usd"] > 0
    assert sum_rec["agri_trade_balance_million_usd"] < 0

