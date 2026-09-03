"""End-to-end integration test for the full farmer user journey against FastAPI backend.

This test simulates the exact sequence of HTTP requests made by the Flutter mobile app
when running in live-backend mode (`USE_MOCKS=false`):
1. Health check verification (GET /health).
2. Registration of a new unique farmer test account.
3. Login and JWT token issuance.
4. Session restoration (GET /api/v1/auth/me).
5. Farmer profile creation and update (PATCH /api/v1/profile) with name, district, crop, farm size, irrigation type, and language.
6. Profile retrieval (GET /api/v1/profile) confirming persisted fields.
7. Dashboard retrieval (GET /api/v1/dashboard) with multi-card source status.
8. Weather retrieval: district list, current weather, and historical weather with preserved status labels.
9. Crop health scan upload (POST /api/v1/crop-health/scan) with a sample leaf image, verifying predicted class, confidence, model_version (plantvillage_v2), and uncertainty warning.
10. Scan history verification (GET /api/v1/crop-health/history) and cross-user data isolation.
11. Admin route access denial for farmer role (GET /api/v1/admin/users returns 403).
12. Logout / unauthenticated route protection (GET /api/v1/auth/me without token returns 401).
"""

from __future__ import annotations

import io
import uuid
from pathlib import Path

import pytest
from fastapi.testclient import TestClient
from PIL import Image

from app.backend.database import UserStore
from app.backend.main import app
from app.backend.services import disease_service
from app.config import settings


@pytest.fixture(autouse=True)
def setup_environment(tmp_path, monkeypatch):
    """Ensure clean isolated user store and reset disease model cache."""
    monkeypatch.setattr(settings, "data_dir", tmp_path / "app_data")
    disease_service.reset_cached_model()
    store = UserStore()
    if store.path.exists():
        store.path.unlink()
    yield
    disease_service.reset_cached_model()


def _create_sample_leaf_bytes(width: int = 224, height: int = 224, color=(34, 139, 34)) -> bytes:
    img = Image.new("RGB", (width, height), color=color)
    buf = io.BytesIO()
    img.save(buf, format="JPEG")
    return buf.getvalue()


def test_full_live_farmer_flow_e2e():
    client = TestClient(app)

    # 1. Health Check
    health_resp = client.get("/health")
    assert health_resp.status_code == 200
    assert health_resp.json()["status"] == "ok"

    # 2. Farmer Registration
    unique_phone = f"0300{uuid.uuid4().int % 10000000:07d}"
    register_payload = {
        "phone": unique_phone,
        "password": "FarmerSecretPass123!",
        "name": "Tariq Mahmood",
        "role": "farmer",
    }
    reg_resp = client.post("/api/v1/auth/register", json=register_payload)
    assert reg_resp.status_code == 200, reg_resp.text
    reg_data = reg_resp.json()
    assert "access_token" in reg_data
    assert reg_data["role"] == "farmer"
    farmer_1_id = reg_data["user_id"]
    token_1 = reg_data["access_token"]
    headers_1 = {"Authorization": f"Bearer {token_1}"}

    # 3. Farmer Login
    login_resp = client.post(
        "/api/v1/auth/login",
        json={"phone": unique_phone, "password": "FarmerSecretPass123!"},
    )
    assert login_resp.status_code == 200
    login_data = login_resp.json()
    assert login_data["user_id"] == farmer_1_id
    assert "access_token" in login_data

    # 4. Session Validation (GET /api/v1/auth/me)
    me_resp = client.get("/api/v1/auth/me", headers=headers_1)
    assert me_resp.status_code == 200
    me_data = me_resp.json()["data"]
    assert me_data["user_id"] == farmer_1_id
    assert me_data["phone"] == unique_phone
    assert me_data["role"] == "farmer"

    # 5. Save Farmer Profile (PATCH /api/v1/profile)
    profile_update = {
        "name": "Tariq Mahmood",
        "district": "Faisalabad",
        "crop": "wheat",
        "farm_size_acres": 15.5,
        "irrigation_type": "canal",
        "language": "ur",
    }
    patch_resp = client.patch("/api/v1/profile", headers=headers_1, json=profile_update)
    assert patch_resp.status_code == 200, patch_resp.text
    patched_data = patch_resp.json()
    assert patched_data["name"] == "Tariq Mahmood"
    assert patched_data["district"] == "Faisalabad"
    assert patched_data["crop"] == "wheat"
    assert patched_data["farm_size_acres"] == 15.5
    assert patched_data["irrigation_type"] == "canal"
    assert patched_data["language"] == "ur"

    # 6. Retrieve Profile (GET /api/v1/profile)
    get_profile_resp = client.get("/api/v1/profile", headers=headers_1)
    assert get_profile_resp.status_code == 200
    profile_data = get_profile_resp.json()
    assert profile_data["district"] == "Faisalabad"
    assert profile_data["crop"] == "wheat"
    assert profile_data["farm_size_acres"] == 15.5
    assert profile_data["language"] == "ur"

    # 7. Fetch Dashboard (GET /api/v1/dashboard)
    dash_resp = client.get("/api/v1/dashboard", headers=headers_1)
    assert dash_resp.status_code == 200
    dash_data = dash_resp.json()
    assert "weather" in dash_data
    assert "farm_health" in dash_data
    assert "market" in dash_data
    assert "satellite" in dash_data
    assert "quick_actions" in dash_data
    assert dash_data["market"]["status"] in {"official_amis", "stale_official_record", "mock"}
    assert dash_data["satellite"]["status"] == "historical"
    assert dash_data["satellite"]["satellite_source"] == "Sentinel-2 MSI / MODIS Terra Baseline"

    # 8. Weather Endpoints (Districts, Current, Historical)
    districts_resp = client.get("/api/v1/weather/districts", headers=headers_1)
    assert districts_resp.status_code == 200
    districts = districts_resp.json()["districts"]
    assert "Faisalabad" in districts
    assert len(districts) >= 30

    current_weather_resp = client.get("/api/v1/weather/current?district=Faisalabad", headers=headers_1)
    assert current_weather_resp.status_code == 200
    current_weather = current_weather_resp.json()["data"]
    assert current_weather["district"] == "Faisalabad"
    assert current_weather["status"] in ("historical", "mock", "live", "unavailable")
    assert "temperature_c" in current_weather
    assert "humidity_percent" in current_weather
    assert "rainfall_mm" in current_weather

    historical_weather_resp = client.get("/api/v1/weather/historical?district=Faisalabad", headers=headers_1)
    assert historical_weather_resp.status_code == 200
    hist_records = historical_weather_resp.json()["data"]
    assert len(hist_records) > 0

    # 9. Crop Health Scan (POST /api/v1/crop-health/scan)
    sample_image_bytes = _create_sample_leaf_bytes()
    scan_resp = client.post(
        "/api/v1/crop-health/scan",
        headers=headers_1,
        files={"image": ("farmer_leaf.jpg", io.BytesIO(sample_image_bytes), "image/jpeg")},
    )
    assert scan_resp.status_code == 200, scan_resp.text
    scan_result = scan_resp.json()
    assert scan_result["success"] is True
    scan_data = scan_result["data"]

    assert "scan_id" in scan_data
    assert scan_data["user_id"] == farmer_1_id
    assert scan_data["predicted_class"] == "Tomato_Septoria_leaf_spot"
    assert 0.0 <= scan_data["confidence"] <= 1.0
    assert scan_data["model_version"] == "plantvillage_v2"
    assert scan_data["uncertain"] is True
    assert "scanned_at" in scan_data

    # 10. Scan History & Multi-User Isolation
    history_resp = client.get("/api/v1/crop-health/history", headers=headers_1)
    assert history_resp.status_code == 200
    history_items = history_resp.json()["data"]
    assert len(history_items) == 1
    assert history_items[0]["scan_id"] == scan_data["scan_id"]
    assert history_items[0]["predicted_class"] == "Tomato_Septoria_leaf_spot"

    # Register Farmer 2 and verify farmer 2 cannot see farmer 1's scan
    phone_2 = f"0300{uuid.uuid4().int % 10000000:07d}"
    reg_2_resp = client.post(
        "/api/v1/auth/register",
        json={"phone": phone_2, "password": "Farmer2SecretPass123!", "name": "Second Farmer", "role": "farmer"},
    )
    assert reg_2_resp.status_code == 200
    token_2 = reg_2_resp.json()["access_token"]
    headers_2 = {"Authorization": f"Bearer {token_2}"}

    history_2_resp = client.get("/api/v1/crop-health/history", headers=headers_2)
    assert history_2_resp.status_code == 200
    assert len(history_2_resp.json()["data"]) == 0

    # 11. Admin Route Guard (Farmer cannot access admin endpoints)
    admin_resp = client.get("/api/v1/admin/users", headers=headers_1)
    assert admin_resp.status_code == 403

    admin_stats_resp = client.get("/api/v1/admin/stats", headers=headers_1)
    assert admin_stats_resp.status_code == 403

    # 12. Unauthenticated Request Protection
    unauth_resp = client.get("/api/v1/auth/me")
    assert unauth_resp.status_code == 401

    unauth_scan = client.post(
        "/api/v1/crop-health/scan",
        files={"image": ("test.jpg", io.BytesIO(sample_image_bytes), "image/jpeg")},
    )
    assert unauth_scan.status_code == 401
