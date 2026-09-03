# Phase 10: Notifications (Weather Alerts + Market Movers + Advisory Reminders) Report

- **Project:** Kisaan Dost Agricultural Platform
- **Task:** Phase 10: Notifications (Weather Alerts + Market Movers + Advisory Reminders)
- **Timestamp (UTC):** `2026-09-02T03:41:45+00:00`
- **Status:** **COMPLETE / FULLY VALIDATED**

---

## 1. Executive Summary

Phase 10 implements deterministic, rule-based **Weather Alerts**, **AMIS Market Price Mover Alerts**, and **Agronomic Advisory Reminders** across backend rule evaluation and Flutter mobile UI views.

The backend utilizes structured JSON tables (`user_preferences.json` and `notifications.json`) with thread-safe atomic file replacement. Evaluation runs both on-demand and via asynchronous background jobs (`BackgroundTasks`) to prevent blocking the main request thread.

---

## 2. Structured JSON Tables Architecture

### `data/processed/user_preferences.json`
- **Schema Fields:**
  - `user_id`: Unique identifier (e.g. `default_farmer`).
  - `selected_district`: Primary district (e.g. `Lahore District`).
  - `selected_market`: Primary AMIS mandi (e.g. `Lahore`).
  - `selected_crops`: Allowlisted crop focus list (`["Wheat", "Rice Basmati Super (New)", "Cotton", "Potato Fresh"]`).
  - `alert_types`: Subscribed categories (`["weather", "market", "advisory"]`).
  - `channels`: Selected delivery modes (`["in_app", "local"]`).
  - `heatwave_temp_threshold`: Temperature trigger (default `40.0` °C).
  - `rainfall_threshold_mm`: Precipitation trigger (default `25.0` mm).
  - `frost_temp_threshold`: Low-temperature trigger (default `3.0` °C).
  - `market_mover_threshold_pct`: Rate shift trigger (default `10.0` %).
  - `fcm_token`: Device registration token (or `null`).
  - `fcm_status`: `"not_configured"` (gracefully skips remote push without crashing or requiring fake keys).
  - `updated_at_utc`: ISO8601 timestamp.

### `data/processed/notifications.json`
- **Schema Fields:**
  - `id`: Unique identifier (e.g. `notif_heat_Lahore District_2026-09-01`).
  - `user_id`: Target user.
  - `type`: Category (`weather_alert`, `market_mover`, `advisory_reminder`).
  - `title` / `title_ur`: Localized titles.
  - `message` / `message_ur` / `body`: Localized alert descriptions.
  - `severity`: `info`, `warning`, or `critical`.
  - `created_at_utc`: Alert timestamp.
  - `is_read`: Boolean read status.
  - `source_attribution`: Strict official provenance.
  - `metadata`: Raw evaluation payload values.

---

## 3. Rule Evaluation Engine & Triggers

| Domain | Rule Trigger | Threshold Condition | Primary Action / Message | Official Attribution |
|---|---|---|---|---|
| **Weather** | Heatwave Risk | $T_{\max} \ge 40.0^\circ\text{C}$ (configurable) | Extreme temperature alert; irrigate during evening hours | `Weather data by Open-Meteo.com under CC BY 4.0` |
| **Weather** | Heavy Rainfall | $\text{Rain} \ge 25.0\ \text{mm}$ (configurable) | Suspend spray operations and inspect field drainage | `Weather data by Open-Meteo.com under CC BY 4.0` |
| **Weather** | Frost Risk | $T_{\min} \le 3.0^\circ\text{C}$ (configurable) | Shield sensitive orchards & winter vegetables | `Weather data by Open-Meteo.com under CC BY 4.0` |
| **Market** | Price Mover | $\Delta P \ge 10\%$ week-over-week / day | Wholesale price shift recorded for farmer's crop | `Market data by AMIS Punjab` |
| **Advisory** | Spray Window | $\text{Wind} < 15\ \text{km/h} \land \text{Rain} < 1\ \text{mm}$ | Calm, rain-free conditions for crop protection | `Advisory based on official reports` |

---

## 4. FastAPI Backend Endpoints

| Endpoint | Method | Output Schema | Description |
|---|---|---|---|
| `/api/v1/notifications/preferences` | `GET` | `NotificationPreferencesResponse` | Retrieves farmer notification channels & thresholds |
| `/api/v1/notifications/preferences` | `PUT` | `NotificationPreferencesResponse` | Updates farmer notification channels & thresholds |
| `/api/v1/notifications/history?unread_only=<bool>` | `GET` | `NotificationListResponse` | Retrieves in-app notification inbox history |
| `/api/v1/notifications/unread-count` | `GET` | `NotificationUnreadCountResponse` | Returns live unread notifications count |
| `/api/v1/notifications/mark-read` | `PUT` | `NotificationMarkReadResponse` | Marks multiple notifications (or all) as read |
| `/api/v1/notifications/{notification_id}/read` | `POST` | `{"success": true}` | Marks specific notification item as read |
| `/api/v1/notifications/evaluate?run_async=<bool>` | `POST` | `NotificationEvaluateResponse` | Evaluates active triggers synchronously or in background |

---

## 5. Flutter Mobile Interface (`NotificationsScreen`)

- **Interactive Inbox Features:**
  - Type filter chips: **All**, **Weather Alerts**, **Market Movers**, **Advisories**.
  - Unread count badge and filter toggle.
  - Severity indicators (Warning, Critical, Info) and source provenance attribution.
  - Interactive "Mark as Read" behavior.
- **Preferences Modal Sheet (`_PreferencesModal`):**
  - Delivery channel switches: **In-App Inbox**, **Local Device Notifications**, and **FCM Push** (marked "Optional / Not Configured").
  - Alert trigger toggles: Weather, Market, and Advisory.
  - Sliders for Heatwave (°C) and Rainfall (mm) threshold tuning.
  - Persistence across app sessions.
- **Dual Localization:** Full English and Urdu support.
- **Safety Invariant:** **Zero ML forecasting, no price predictions, and no policy advice.**

---

## 6. Verification Matrix

| Test Suite | Scope | Result |
|---|---|---|
| **Notifications API Tests** | `pytest tests/test_notifications_api.py -v` | **2 / 2 PASS** |
| **Root Backend Test Suite** | `pytest tests -q -rs --tb=short` | **89 / 89 PASS** |
| **Data Pipeline Test Suite** | `pytest Kisaan_Dost_Data/tests -q -rs --tb=short` | **396 / 396 PASS** |
| **Flutter Unit & Widget Tests** | `flutter test` | **76 / 76 PASS** |
| **Flutter Static Analysis** | `flutter analyze` | **0 issues found (CLEAN)** |
| **Handoff Completeness Gate** | `python scripts/check_handoff_completeness.py` | **COMPLETE (0 Active Blockers)** |
