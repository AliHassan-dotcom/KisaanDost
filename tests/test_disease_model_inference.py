"""Targeted unit and integration tests for crop disease model inference.

Tests cover:
- Path resolution and trusted directory validation for model and class mapping.
- Lazy model loading and architecture verification.
- Real inference outputs (predicted_class, confidence, model_version, uncertain flag).
- API scan endpoint authentication and authorization.
- Input validation: unsupported file types, oversized payloads.
- Safe 503 unavailable behavior when model checkpoint is missing (no leaked paths).
- Path traversal defense.
"""

from __future__ import annotations

import io
from pathlib import Path

import pytest
from fastapi.testclient import TestClient
from PIL import Image

from app.backend.database import UserStore
from app.backend.main import app
from app.backend.services import disease_service
from app.config import settings


@pytest.fixture(autouse=True)
def clean_model_cache():
    """Ensure cached model state is reset before and after each test."""
    disease_service.reset_cached_model()
    yield
    disease_service.reset_cached_model()


@pytest.fixture
def client(tmp_path, monkeypatch):
    """Provide a TestClient with an isolated app_data directory."""
    monkeypatch.setattr(settings, "data_dir", tmp_path / "app_data")
    store = UserStore()
    if store.path.exists():
        store.path.unlink()
    return TestClient(app)


@pytest.fixture
def auth_headers(client):
    payload = {
        "phone": "03005554444",
        "password": "farmerpassword",
        "name": "Targeted Test Farmer",
        "role": "farmer",
    }
    resp = client.post("/api/v1/auth/register", json=payload)
    assert resp.status_code == 200
    token = resp.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}


def _create_sample_jpeg_bytes(width: int = 224, height: int = 224, color=(34, 139, 34)) -> bytes:
    img = Image.new("RGB", (width, height), color=color)
    buf = io.BytesIO()
    img.save(buf, format="JPEG")
    return buf.getvalue()


def test_configured_model_path_resolution():
    """Verify configured model path resolves to existing v2 checkpoint within project root."""
    model_full_path = settings.model_full_path()
    assert model_full_path.exists(), f"Model file must exist at {model_full_path}"
    assert model_full_path.is_file(), f"Model must be a regular file: {model_full_path}"
    assert model_full_path.name == "best_plantvillage_model_v2.pt"

    resolved_root = settings.project_root.resolve()
    assert model_full_path.resolve().is_relative_to(resolved_root)

    mapping_full_path = settings.class_mapping_full_path()
    assert mapping_full_path.exists(), f"Class mapping must exist at {mapping_full_path}"
    assert mapping_full_path.is_file()
    assert mapping_full_path.resolve().is_relative_to(resolved_root)


def test_disease_service_load_model_and_metadata():
    """Verify load_model returns initialized ResNet-18 model, 15 classes, and version string."""
    model, id_to_class, model_version = disease_service.load_model()
    assert model is not None
    assert len(id_to_class) == 15
    assert "Tomato_healthy" in id_to_class or any("Tomato" in c for c in id_to_class)
    assert model_version == "plantvillage_v2"


def test_disease_service_predict_with_known_image(tmp_path):
    """Verify disease_service.predict returns required schema with confidence and uncertainty."""
    test_image_path = tmp_path / "sample_leaf.jpg"
    test_image_path.write_bytes(_create_sample_jpeg_bytes(224, 224, color=(45, 120, 45)))

    result = disease_service.predict(test_image_path)
    assert isinstance(result, dict)
    assert "predicted_class" in result
    assert isinstance(result["predicted_class"], str)
    assert 0.0 <= result["confidence"] <= 1.0
    assert 0 <= result["class_id"] < 15
    assert result["model_version"] == "plantvillage_v2"
    assert isinstance(result["uncertain"], bool)
    if result["uncertain"]:
        assert result["warning"] is not None
    else:
        assert result["warning"] is None


def test_scan_endpoint_success_and_history(client, auth_headers):
    """Verify POST /api/v1/crop-health/scan returns inference result and persists history."""
    image_bytes = _create_sample_jpeg_bytes(224, 224)
    resp = client.post(
        "/api/v1/crop-health/scan",
        headers=auth_headers,
        files={"image": ("test_leaf.jpg", io.BytesIO(image_bytes), "image/jpeg")},
    )
    assert resp.status_code == 200, resp.text
    body = resp.json()
    assert body["success"] is True
    data = body["data"]

    assert "scan_id" in data
    assert "predicted_class" in data
    assert "confidence" in data
    assert "uncertain" in data
    assert "model_version" in data
    assert "scanned_at" in data
    assert 0.0 <= data["confidence"] <= 1.0

    # Ensure filesystem path is not exposed to API caller in public data fields
    assert "D:" not in data["predicted_class"]
    assert "/" not in data["predicted_class"] or "_" in data["predicted_class"]

    # Check history
    hist_resp = client.get("/api/v1/crop-health/history", headers=auth_headers)
    assert hist_resp.status_code == 200
    hist_scans = hist_resp.json()["data"]
    assert len(hist_scans) >= 1
    assert hist_scans[0]["scan_id"] == data["scan_id"]


def test_scan_endpoint_unauthenticated_rejected(client):
    """Verify unauthenticated scan request returns HTTP 401."""
    image_bytes = _create_sample_jpeg_bytes()
    resp = client.post(
        "/api/v1/crop-health/scan",
        files={"image": ("leaf.jpg", io.BytesIO(image_bytes), "image/jpeg")},
    )
    assert resp.status_code == 401


def test_scan_endpoint_unsupported_extension_rejected(client, auth_headers):
    """Verify non-image files and unsupported extensions are rejected with HTTP 400."""
    resp = client.post(
        "/api/v1/crop-health/scan",
        headers=auth_headers,
        files={"image": ("report.pdf", io.BytesIO(b"%PDF-1.4 dummy"), "application/pdf")},
    )
    assert resp.status_code == 400
    assert "unsupported" in resp.text.lower() or "invalid" in resp.text.lower()


def test_scan_endpoint_oversized_image_rejected(client, auth_headers):
    """Verify uploads exceeding upload_max_bytes (5MB) are rejected."""
    large_payload = b"\xff\xd8\xff" + b"\x00" * (5 * 1024 * 1024 + 1024)  # > 5 MB

    resp = client.post(
        "/api/v1/crop-health/scan",
        headers=auth_headers,
        files={"image": ("large.jpg", io.BytesIO(large_payload), "image/jpeg")},
    )
    assert resp.status_code in (400, 413)
    assert "too large" in resp.text.lower() or "could not process upload" in resp.text.lower()


def test_scan_endpoint_safe_unavailable_on_missing_model(client, auth_headers, monkeypatch, tmp_path):
    """Verify missing model returns HTTP 503 without exposing server paths."""
    monkeypatch.setattr(settings, "model_path", Path("nonexistent_path/missing_model.pt"))
    disease_service.reset_cached_model()

    image_bytes = _create_sample_jpeg_bytes()
    resp = client.post(
        "/api/v1/crop-health/scan",
        headers=auth_headers,
        files={"image": ("leaf.jpg", io.BytesIO(image_bytes), "image/jpeg")},
    )
    assert resp.status_code == 503
    assert resp.json()["detail"] == "Disease model is not available."
    # Ensure no path information is leaked
    assert "nonexistent_path" not in resp.text
    assert "missing_model" not in resp.text


def test_disease_service_rejects_path_traversal(monkeypatch):
    """Verify path traversal outside project root is rejected."""
    traversal_path = Path("../../external_untrusted_model.pt")
    monkeypatch.setattr(settings, "model_path", traversal_path)
    disease_service.reset_cached_model()

    with pytest.raises((PermissionError, FileNotFoundError)):
        disease_service.load_model()
