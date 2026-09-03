"""Integration tests for Database Health and Admin Migration Status endpoints."""

from __future__ import annotations

import pytest
from starlette.testclient import TestClient

from app.backend.main import app
from app.security.auth import Role, create_access_token


@pytest.fixture
def client() -> TestClient:
    return TestClient(app)


def test_health_db_endpoint(client: TestClient):
    resp = client.get("/api/v1/health/db")
    assert resp.status_code == 200
    data = resp.json()
    assert "status" in data
    assert "database_connected" in data
    assert data["database_connected"] is True


def test_admin_migration_status_endpoint(client: TestClient):
    admin_token = create_access_token(
        user_id="admin_user_001",
        role=Role.ADMIN,
        phone="+923000000000",
    )
    headers = {"Authorization": f"Bearer {admin_token}"}

    resp = client.get("/api/v1/admin/migration-status", headers=headers)
    assert resp.status_code == 200
    body = resp.json()
    assert body["success"] is True
    assert "database_connected" in body
    assert "migration_metadata" in body
    assert body["migration_metadata"]["status"] == "success"
