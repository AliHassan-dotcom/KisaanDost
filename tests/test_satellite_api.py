"""Tests for the Satellite API endpoints, service, and explainable attention status."""

from __future__ import annotations

import re
import pytest
from fastapi.testclient import TestClient

from app.backend.main import app
from app.backend.services.satellite_service import SatelliteService, get_satellite_service
from app.security.auth import Role, create_access_token


@pytest.fixture
def client() -> TestClient:
    return TestClient(app)


@pytest.fixture
def auth_headers() -> dict[str, str]:
    token = create_access_token(user_id="usr_farmer_01", phone="03001234567", role=Role.FARMER)
    return {"Authorization": f"Bearer {token}"}


def test_formula_synthetic_band_integrity():
    """Verify exact spectral index mathematical formulations with synthetic bands."""
    def calc_ndvi(b8_nir: float, b4_red: float) -> float:
        return (b8_nir - b4_red) / (b8_nir + b4_red)

    def calc_ndwi(b8_nir: float, b11_swir: float) -> float:
        return (b8_nir - b11_swir) / (b8_nir + b11_swir)

    # Dense healthy canopy
    ndvi_healthy = calc_ndvi(0.80, 0.10)
    ndwi_healthy = calc_ndwi(0.80, 0.20)
    assert round(ndvi_healthy, 4) == 0.7778
    assert round(ndwi_healthy, 4) == 0.6000
    assert -1.0 <= ndvi_healthy <= 1.0
    assert -1.0 <= ndwi_healthy <= 1.0

    # Water stressed canopy
    ndvi_stressed = calc_ndvi(0.40, 0.30)
    ndwi_stressed = calc_ndwi(0.40, 0.55)
    assert round(ndvi_stressed, 4) == 0.1429
    assert round(ndwi_stressed, 4) == -0.1579


def test_list_districts_authenticated(client: TestClient, auth_headers: dict[str, str]):
    response = client.get("/api/v1/satellite/districts", headers=auth_headers)
    assert response.status_code == 200
    data = response.json()
    assert data["total_districts"] == 34
    assert len(data["districts"]) == 34

    dist_names = [d["normalized_district"] for d in data["districts"]]
    assert "Lahore District" in dist_names
    assert "Bhakkar District" in dist_names

    # Verify boundary flag for missing vs present
    for d in data["districts"]:
        if d["normalized_district"] in {"Bhakkar District", "Jhang District", "Layyah District", "Muzaffargarh District", "Okara District"}:
            assert d["has_authoritative_polygon"] is False
            assert d["data_status"] == "boundary_unavailable"
            assert d["coverage_percentage"] == "0.0%"
        else:
            assert d["has_authoritative_polygon"] is True
            assert d["data_status"] == "historical_satellite_baseline"
            assert d["coverage_percentage"] != "0.0%"


def test_get_latest_satellite_valid_district(client: TestClient, auth_headers: dict[str, str]):
    response = client.get("/api/v1/satellite/latest?district=Lahore", headers=auth_headers)
    assert response.status_code == 200
    data = response.json()
    assert data["district"] == "Lahore"
    assert data["normalized_district"] == "Lahore District"
    assert data["year"] == 2025
    assert data["month"] == 12
    assert data["period_start"] == "2025-12-01"
    assert data["period_end"] == "2025-12-31"
    assert data["data_status"] == "historical_satellite_baseline"
    assert data["no_coverage_flag"] is False
    assert data["ndvi_mean"] is not None
    assert -1.0 <= data["ndvi_mean"] <= 1.0
    assert data["ndwi_mean"] is not None
    assert -1.0 <= data["ndwi_mean"] <= 1.0
    assert data["satellite_source"] == "Sentinel-2 MSI / MODIS Terra Baseline"
    assert data["product_id"] == "COPERNICUS/S2_SR_HARMONIZED"
    assert data["spatial_scale_m"] == 100
    assert "attention_status" in data
    assert "attention_evidence" in data


def test_get_latest_satellite_missing_boundary_districts(client: TestClient, auth_headers: dict[str, str]):
    missing_districts = ["Bhakkar", "Jhang", "Layyah", "Muzaffargarh", "Okara"]
    for dist in missing_districts:
        response = client.get(f"/api/v1/satellite/latest?district={dist}", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert data["data_status"] == "boundary_unavailable"
        assert data["no_coverage_flag"] is True
        assert data["quality_flag"] == "missing_authoritative_arcgis_polygon"
        assert data["ndvi_mean"] is None
        assert data["ndvi_median"] is None
        assert data["ndwi_mean"] is None
        assert data["ndwi_median"] is None
        assert data["valid_pixel_count"] is None
        assert data["observation_count"] is None
        assert data["attention_status"] == "boundary_unavailable"
        assert "unavailable in provincial GIS records" in data["attention_evidence"]


def test_get_satellite_history_date_range_filtering(client: TestClient, auth_headers: dict[str, str]):
    # Request 2024 calendar year (12 months)
    response = client.get(
        "/api/v1/satellite/history?district=Multan&start=2024-01&end=2024-12",
        headers=auth_headers,
    )
    assert response.status_code == 200
    data = response.json()
    assert data["district"] == "Multan"
    assert data["total_records"] == 12
    assert len(data["records"]) == 12

    months = [r["month"] for r in data["records"]]
    assert months == list(range(1, 13))


def test_get_satellite_coverage_endpoint(client: TestClient, auth_headers: dict[str, str]):
    response = client.get("/api/v1/satellite/coverage?district=Faisalabad", headers=auth_headers)
    assert response.status_code == 200
    data = response.json()
    assert data["district"] == "Faisalabad"
    assert data["has_authoritative_polygon"] is True
    assert data["total_expected_months"] == 48
    assert data["months_with_satellite_data"] == 48
    assert data["coverage_percentage"] == "100.0%"
    assert data["data_status"] == "historical_satellite_baseline"


def test_unauthenticated_access_rejected(client: TestClient):
    response = client.get("/api/v1/satellite/latest?district=Lahore")
    assert response.status_code == 401


def test_invalid_district_rejected(client: TestClient, auth_headers: dict[str, str]):
    response = client.get("/api/v1/satellite/latest?district=Atlantis", headers=auth_headers)
    assert response.status_code == 400
    assert "not one of the 34 Punjab master districts" in response.json()["detail"]


def test_no_filesystem_paths_leaked(client: TestClient, auth_headers: dict[str, str]):
    response = client.get("/api/v1/satellite/history?district=Rawalpindi&start=2023-01&end=2023-03", headers=auth_headers)
    assert response.status_code == 200
    raw_text = response.text
    assert "D:\\" not in raw_text
    assert "C:\\" not in raw_text
    assert "/Kisaan_Dost_Data/" not in raw_text
    assert ".csv" not in raw_text


def test_attention_non_diagnostic_language(client: TestClient, auth_headers: dict[str, str]):
    response = client.get("/api/v1/satellite/history?district=Lahore", headers=auth_headers)
    assert response.status_code == 200
    data = response.json()

    prohibited_words = [
        "disease", "pest", "pesticide", "fungicide", "infestation",
        "treatment", "chemical", "yield prediction", "yield estimate"
    ]

    for rec in data["records"]:
        evidence = rec["attention_evidence"].lower()
        status = rec["attention_status"]
        assert status in {
            "normal_observation", "vegetation_attention", "water_attention",
            "insufficient_satellite_data", "boundary_unavailable"
        }
        for word in prohibited_words:
            assert word not in evidence, f"Prohibited clinical/treatment word '{word}' found in evidence: {evidence}"


def test_cloud_masked_period_returns_insufficient_data(client: TestClient, auth_headers: dict[str, str]):
    # 2022-07 Narowal had complete monsoon cloud cover in raw acquisition
    response = client.get(
        "/api/v1/satellite/history?district=Narowal&start=2022-07&end=2022-07",
        headers=auth_headers,
    )
    assert response.status_code == 200
    data = response.json()
    assert data["total_records"] == 1
    rec = data["records"][0]
    assert rec["data_status"] == "satellite_source_unavailable"
    assert rec["no_coverage_flag"] is True
    assert rec["quality_flag"] == "cloud_masked_no_valid_pixels"
    assert rec["ndvi_mean"] is None
    assert rec["ndwi_mean"] is None
    assert rec["attention_status"] == "insufficient_satellite_data"


def test_dashboard_endpoint_includes_historical_satellite(client: TestClient, auth_headers: dict[str, str]):
    response = client.get("/api/v1/dashboard", headers=auth_headers)
    assert response.status_code == 200
    data = response.json()
    assert "satellite" in data
    sat = data["satellite"]
    assert sat["district"] == "Lahore"
    assert sat["status"] == "historical"
    assert sat["ndvi"] is not None
    assert sat["ndwi"] is not None
    assert sat["satellite_source"] == "Sentinel-2 MSI / MODIS Terra Baseline"
