"""Unit and integration tests for Notifications API, Preferences & Unread Status (Phase 10)."""

from __future__ import annotations

import pytest
from starlette.testclient import TestClient

from app.backend.main import app


@pytest.fixture
def client() -> TestClient:
    return TestClient(app)


def test_get_and_update_notification_preferences(client: TestClient):
    # 1. Get preferences
    resp = client.get("/api/v1/notifications/preferences")
    assert resp.status_code == 200
    body = resp.json()
    assert body["success"] is True
    prefs = body["data"]["preferences"]
    assert "enable_weather_alerts" in prefs
    assert "selected_crops" in prefs
    assert "channels" in prefs
    assert "alert_types" in prefs

    # 2. Update preferences
    update_payload = {
        "selected_district": "Multan District",
        "selected_market": "Multan",
        "selected_crops": ["Cotton", "Wheat"],
        "alert_types": ["weather", "market"],
        "channels": ["in_app", "local"],
        "heatwave_temp_threshold": 42.0,
        "enable_weather_alerts": True,
        "enable_market_alerts": True,
        "enable_advisory_reminders": True,
    }
    put_resp = client.put("/api/v1/notifications/preferences", json=update_payload)
    assert put_resp.status_code == 200
    updated_body = put_resp.json()
    assert updated_body["success"] is True
    updated_prefs = updated_body["data"]["preferences"]
    assert updated_prefs["selected_district"] == "Multan District"
    assert updated_prefs["selected_crops"] == ["Cotton", "Wheat"]
    assert updated_prefs["heatwave_temp_threshold"] == 42.0


def test_evaluate_unread_count_and_mark_read(client: TestClient):
    # 1. Evaluate rules synchronously
    eval_resp = client.post("/api/v1/notifications/evaluate")
    assert eval_resp.status_code == 200
    eval_body = eval_resp.json()
    assert eval_body["success"] is True
    eval_data = eval_body["data"]
    assert "new_alerts_count" in eval_data
    assert "evaluated_at_utc" in eval_data

    # 2. Evaluate in background task
    bg_resp = client.post("/api/v1/notifications/evaluate?run_async=true")
    assert bg_resp.status_code == 200
    assert bg_resp.json()["success"] is True

    # 3. Check unread count
    count_resp = client.get("/api/v1/notifications/unread-count")
    assert count_resp.status_code == 200
    count_body = count_resp.json()
    assert count_body["success"] is True
    assert "unread_count" in count_body["data"]

    # 4. Get history
    hist_resp = client.get("/api/v1/notifications/history")
    assert hist_resp.status_code == 200
    hist_body = hist_resp.json()
    assert hist_body["success"] is True
    hist_data = hist_body["data"]

    if hist_data["notifications"]:
        notif = hist_data["notifications"][0]
        assert "title" in notif
        assert "title_ur" in notif
        assert "source_attribution" in notif
        notif_id = notif["id"]

        # 5. Mark single read via PUT /mark-read
        mark_resp = client.put("/api/v1/notifications/mark-read", json={"notification_ids": [notif_id]})
        assert mark_resp.status_code == 200
        assert mark_resp.json()["success"] is True

        # 6. Mark all read
        mark_all_resp = client.put("/api/v1/notifications/mark-read", json={"mark_all": True})
        assert mark_all_resp.status_code == 200
        assert mark_all_resp.json()["success"] is True
