"""API tests for pest alert and pesticide advisory endpoints."""

from __future__ import annotations

import csv
import json
from pathlib import Path
from typing import Any, Dict, List

import pytest
from fastapi.testclient import TestClient

from app.backend.database import UserStore
from app.backend.main import app
from app.backend.services.pesticide_service import get_pesticide_service
from app.config import settings
from app.security import auth as auth_module


@pytest.fixture
def client(tmp_path, monkeypatch):
    """Provide a TestClient with isolated project root and reset service cache."""
    monkeypatch.setattr(settings, "project_root", tmp_path)
    monkeypatch.setattr(settings, "data_dir", Path("app_data"))
    store = UserStore()
    if store.path.exists():
        store.path.unlink()
    # Reset the module-level service singleton and rate-limit buckets so each test is isolated.
    import app.backend.services.pesticide_service as svc_module

    svc_module._service = None
    auth_module._advisory_buckets.clear()
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


def _auth_headers(token: str) -> Dict[str, str]:
    return {"Authorization": f"Bearer {token}"}


def _write_facts(path: Path, rows: List[Dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fieldnames = [
        "fact_id",
        "category",
        "crop",
        "pest_or_disease",
        "district",
        "date_or_period",
        "advisory_text",
        "pesticide_name",
        "active_ingredient",
        "formulation",
        "explicit_dose_text",
        "safety_text",
        "quality_control_status",
        "source_page",
        "source_section",
        "source_excerpt",
        "confidence",
        "reviewed",
    ]
    with path.open("w", encoding="utf-8", newline="") as fh:
        writer = csv.DictWriter(fh, fieldnames=fieldnames, lineterminator="\n")
        writer.writeheader()
        for row in rows:
            for key in fieldnames:
                if key not in row:
                    row[key] = ""
            writer.writerow(row)


def _write_meta(path: Path, overrides: Dict[str, Any] | None = None) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    meta = {
        "source_title": "Pest Warning and Quality Control of Pesticides Annual Report",
        "source_year": "2024-25",
        "source_filename": "Annual Report 2024-25_copy.pdf",
        "ingestion_timestamp": "2026-09-01T00:00:00+00:00",
        "page_count": 10,
        "num_facts": 2,
        "num_review_queue": 0,
        "num_chunks": 4,
        "status": "ok",
        "readable": True,
    }
    if overrides:
        meta.update(overrides)
    with path.open("w", encoding="utf-8") as fh:
        json.dump(meta, fh)


@pytest.fixture
def official_artifacts(tmp_path, monkeypatch):
    """Create ingestion artifacts so the service reports official_report."""
    processed = tmp_path / "data" / "processed"
    facts_path = processed / "pesticide_report_facts.csv"
    meta_path = processed / "pesticide_report_ingestion_meta.json"

    _write_facts(
        facts_path,
        [
            {
                "fact_id": "f1",
                "category": "advisory",
                "crop": "wheat",
                "pest_or_disease": "aphid",
                "district": "Lahore",
                "advisory_text": "Use imidacloprid 200 SL at 200 ml per acre for aphid control in wheat.",
                "pesticide_name": "imidacloprid 200 SL",
                "explicit_dose_text": "200 ml per acre",
                "safety_text": "Avoid spray during flowering to protect pollinators.",
                "source_page": "7",
                "source_section": "Wheat Pests",
                "source_excerpt": "Use imidacloprid 200 SL at 200 ml per acre for aphid control in wheat.",
                "confidence": "0.92",
                "reviewed": "true",
            },
            {
                "fact_id": "f2",
                "category": "quality_control",
                "crop": "cotton",
                "pest_or_disease": "whitefly",
                "district": "Multan",
                "advisory_text": "Sample XYZ-22 failed active ingredient assay.",
                "quality_control_status": "failed",
                "source_page": "12",
                "source_section": "QC Report",
                "source_excerpt": "Sample XYZ-22 failed active ingredient assay.",
                "confidence": "0.88",
                "reviewed": "true",
            },
        ],
    )
    _write_meta(meta_path)

    # Ensure default relative paths resolve under the temp project root.
    monkeypatch.setattr(
        settings, "pesticide_facts_csv_path", Path("data/processed/pesticide_report_facts.csv")
    )
    monkeypatch.setattr(
        settings, "pesticide_meta_json_path", Path("data/processed/pesticide_report_ingestion_meta.json")
    )
    monkeypatch.setattr(
        settings, "pesticide_chunks_jsonl_path", Path("data/processed/pesticide_report_chunks.jsonl")
    )

    import app.backend.services.pesticide_service as svc_module

    svc_module._service = None


def test_recent_requires_auth(client):
    assert client.get("/api/v1/pest-alerts/recent").status_code == 401


def test_recent_returns_official_alerts(client, registered_user, official_artifacts):
    _, token = registered_user
    resp = client.get(
        "/api/v1/pest-alerts/recent?district=Lahore",
        headers=_auth_headers(token),
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["source_status"] == "official_report"
    assert data["district"] == "Lahore"
    assert len(data["alerts"]) == 1
    assert data["alerts"][0]["fact_id"] == "f1"


def test_recent_filters_by_crop_and_category(client, registered_user, official_artifacts):
    _, token = registered_user
    resp = client.get(
        "/api/v1/pest-alerts/recent?crop=cotton&category=quality_control",
        headers=_auth_headers(token),
    )
    assert resp.status_code == 200
    data = resp.json()
    assert len(data["alerts"]) == 1
    assert data["alerts"][0]["fact_id"] == "f2"


def test_advisory_unavailable_without_ingestion(client, registered_user):
    _, token = registered_user
    resp = client.post(
        "/api/v1/pest-alerts/advisory",
        headers=_auth_headers(token),
        json={"crop": "wheat", "pest": "aphid"},
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["status"] == "unavailable"
    assert data["source_status"] == "unavailable"
    assert data["matched"] is False
    assert data["citations"] == []


def test_advisory_official_match(client, registered_user, official_artifacts):
    _, token = registered_user
    resp = client.post(
        "/api/v1/pest-alerts/advisory",
        headers=_auth_headers(token),
        json={"crop": "wheat", "pest": "aphid", "district": "Lahore"},
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["status"] == "advisory"
    assert data["source_status"] == "official_report"
    assert data["matched"] is True
    assert len(data["citations"]) >= 1
    assert any("200 ml per acre" in data["dose_guidance"] for _ in [None])
    assert data["safety_notice"]


def test_advisory_requires_at_least_one_field(client, registered_user, official_artifacts):
    _, token = registered_user
    resp = client.post(
        "/api/v1/pest-alerts/advisory",
        headers=_auth_headers(token),
        json={},
    )
    assert resp.status_code == 422


def test_advisory_rate_limit(client, registered_user, official_artifacts, monkeypatch):
    _, token = registered_user
    monkeypatch.setattr(settings, "pesticide_advisory_rate_limit_requests", 2)
    monkeypatch.setattr(settings, "pesticide_advisory_rate_limit_window_seconds", 60)
    headers = _auth_headers(token)
    for _ in range(2):
        resp = client.post(
            "/api/v1/pest-alerts/advisory",
            headers=headers,
            json={"crop": "wheat", "pest": "aphid"},
        )
        assert resp.status_code == 200
    resp = client.post(
        "/api/v1/pest-alerts/advisory",
        headers=headers,
        json={"crop": "wheat", "pest": "aphid"},
    )
    assert resp.status_code == 429


def test_sources_returns_meta(client, registered_user, official_artifacts):
    _, token = registered_user
    resp = client.get("/api/v1/pest-alerts/sources", headers=_auth_headers(token))
    assert resp.status_code == 200
    data = resp.json()
    assert len(data["sources"]) == 1
    source = data["sources"][0]
    assert source["status"] == "ok"
    assert source["num_facts"] == 2
    assert source["filename"] == "Annual Report 2024-25_copy.pdf"
