"""MVP backend smoke tests.

These tests exercise the auth, profile, dashboard, weather, crop-health,
pest-alert, market, and admin endpoints. They run against the real v2 model
if present; otherwise inference tests are skipped.
"""

from __future__ import annotations

import io
from pathlib import Path

import pytest
from fastapi.testclient import TestClient
from PIL import Image

from app.backend.database import UserStore
from app.backend.main import app
from app.config import settings
from app.security.auth import Role


@pytest.fixture
def client(tmp_path, monkeypatch):
    """Provide a TestClient with an isolated app_data directory."""
    monkeypatch.setattr(settings, "data_dir", tmp_path / "app_data")
    # Reset cached user store between tests.
    store = UserStore()
    if store.path.exists():
        store.path.unlink()
    return TestClient(app)


@pytest.fixture
def registered_user(client):
    payload = {
        "phone": "03001001000",
        "password": "secret123",
        "name": "Test Farmer",
        "role": "farmer",
    }
    resp = client.post("/api/v1/auth/register", json=payload)
    assert resp.status_code == 200
    return payload, resp.json()["access_token"]


@pytest.fixture
def admin_user(client):
    payload = {
        "phone": "03009998888",
        "password": "adminpass",
        "name": "Test Admin",
        "role": "admin",
    }
    resp = client.post("/api/v1/auth/register", json=payload)
    assert resp.status_code == 200
    return payload, resp.json()["access_token"]


def test_health(client):
    resp = client.get("/health")
    assert resp.status_code == 200
    assert resp.json()["status"] == "ok"


def test_register_and_login(client):
    reg = client.post(
        "/api/v1/auth/register",
        json={
            "phone": "03002002000",
            "password": "farmerpass",
            "name": "Ali",
            "role": "farmer",
        },
    )
    assert reg.status_code == 200
    data = reg.json()
    assert "access_token" in data
    assert data["role"] == "farmer"

    login = client.post(
        "/api/v1/auth/login",
        json={"phone": "03002002000", "password": "farmerpass"},
    )
    assert login.status_code == 200
    assert login.json()["user_id"] == data["user_id"]


def test_login_invalid_password(client, registered_user):
    resp = client.post(
        "/api/v1/auth/login",
        json={"phone": registered_user[0]["phone"], "password": "wrong"},
    )
    assert resp.status_code == 401


def test_me_requires_auth(client):
    assert client.get("/api/v1/auth/me").status_code == 401


def test_me_returns_user(client, registered_user):
    _, token = registered_user
    resp = client.get("/api/v1/auth/me", headers={"Authorization": f"Bearer {token}"})
    assert resp.status_code == 200
    data = resp.json()["data"]
    assert data["role"] == Role.FARMER.value


def test_profile_crud(client, registered_user):
    _, token = registered_user
    headers = {"Authorization": f"Bearer {token}"}

    get_resp = client.get("/api/v1/profile", headers=headers)
    assert get_resp.status_code == 200
    profile = get_resp.json()
    assert profile["name"] == "Test Farmer"

    patch = client.patch(
        "/api/v1/profile",
        headers=headers,
        json={"district": "Lahore", "crop": "wheat", "language": "ur"},
    )
    assert patch.status_code == 200
    updated = patch.json()
    assert updated["district"] == "Lahore"
    assert updated["crop"] == "wheat"
    assert updated["language"] == "ur"


def test_dashboard(client, registered_user):
    _, token = registered_user
    resp = client.get("/api/v1/dashboard", headers={"Authorization": f"Bearer {token}"})
    assert resp.status_code == 200
    data = resp.json()
    assert "weather" in data
    assert "farm_health" in data
    assert "market" in data
    assert "satellite" in data
    assert "quick_actions" in data


def test_weather_districts_and_current(client, registered_user):
    _, token = registered_user
    headers = {"Authorization": f"Bearer {token}"}

    districts = client.get("/api/v1/weather/districts", headers=headers)
    assert districts.status_code == 200
    assert "Lahore" in districts.json()["districts"]

    current = client.get("/api/v1/weather/current?district=Lahore", headers=headers)
    assert current.status_code == 200
    data = current.json()["data"]
    assert data["district"] == "Lahore"
    assert "temperature_c" in data


def test_market_summary(client, registered_user):
    _, token = registered_user
    resp = client.get(
        "/api/v1/market/summary?crop=wheat&district=Lahore",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert resp.status_code == 200
    data = resp.json()["data"]
    assert data["crop"] == "wheat"
    assert data["status"] in {"official_amis", "stale_official_record", "mock"}


def test_pest_advisory(client, registered_user):
    _, token = registered_user
    resp = client.post(
        "/api/v1/pest-alerts/advisory",
        headers={"Authorization": f"Bearer {token}"},
        json={"crop": "wheat", "pest": "aphid"},
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["crop"] == "wheat"
    assert data["source_status"] in ("official_report", "unavailable")
    assert "citations" in data


def _make_jpeg_bytes() -> bytes:
    img = Image.new("RGB", (224, 224), color=(34, 139, 34))
    buf = io.BytesIO()
    img.save(buf, format="JPEG")
    return buf.getvalue()


def test_crop_health_scan(client, registered_user):
    _, token = registered_user
    headers = {"Authorization": f"Bearer {token}"}

    model_path = settings.model_full_path()
    assert model_path.exists(), f"v2 model checkpoint must exist at {model_path}"

    image_bytes = _make_jpeg_bytes()
    resp = client.post(
        "/api/v1/crop-health/scan",
        headers=headers,
        files={"image": ("leaf.jpg", io.BytesIO(image_bytes), "image/jpeg")},
    )
    assert resp.status_code == 200, resp.text
    data = resp.json()["data"]
    assert "scan_id" in data
    assert "predicted_class" in data
    assert 0 <= data["confidence"] <= 1
    assert "model_version" in data
    assert "uncertain" in data

    history = client.get("/api/v1/crop-health/history", headers=headers)
    assert history.status_code == 200
    assert len(history.json()["data"]) == 1


def test_crop_health_rejects_non_image(client, registered_user):
    _, token = registered_user
    headers = {"Authorization": f"Bearer {token}"}
    resp = client.post(
        "/api/v1/crop-health/scan",
        headers=headers,
        files={"image": ("report.txt", io.BytesIO(b"not an image"), "text/plain")},
    )
    assert resp.status_code == 400


def test_admin_endpoints(client, admin_user):
    _, token = admin_user
    headers = {"Authorization": f"Bearer {token}"}

    users = client.get("/api/v1/admin/users", headers=headers)
    assert users.status_code == 200
    assert any(u["phone"] == "03009998888" for u in users.json()["data"])

    audit = client.get("/api/v1/admin/audit", headers=headers)
    assert audit.status_code == 200

    stats = client.get("/api/v1/admin/stats", headers=headers)
    assert stats.status_code == 200
    assert stats.json()["data"]["total_users"] >= 1


def test_admin_forbidden_for_farmer(client, registered_user):
    _, token = registered_user
    resp = client.get("/api/v1/admin/users", headers={"Authorization": f"Bearer {token}"})
    assert resp.status_code == 403
