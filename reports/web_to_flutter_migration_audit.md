# Web-to-Flutter Migration Audit

## Scope
This audit covers the MVP foundation produced in Steps 1–3 of the Kisaan Dost web-oriented implementation. It classifies every created file, documents the existing backend API, auth model, database schema, role rules, and flags any unsafe frontend patterns that must not be carried into the Flutter mobile app.

## Executive summary
- A working FastAPI backend already exists and exposes all endpoints the Flutter app needs.
- Auth is JWT (HS256) with role claims and bcrypt password hashing.
- The JSON-backed user store is adequate for the MVP but must be replaced by PostgreSQL before production.
- The web frontend (`app/frontend/`) is deprecated and reference-only; it stores tokens in `localStorage`, which is unacceptable for mobile.
- No backend secrets or API keys are hard-coded in source.

## File inventory and classification

| Path | Classification | Notes |
|------|----------------|-------|
| `app/__init__.py` | reusable_backend | Package marker |
| `app/backend/__init__.py` | reusable_backend | Package marker |
| `app/backend/main.py` | reusable_backend | FastAPI entrypoint, CORS, router wiring, static mount, health checks |
| `app/backend/database.py` | reusable_backend | JSON-backed user/profile/scan store (`UserStore`) |
| `app/backend/schemas.py` | reusable_api_contract | Pydantic request/response models |
| `app/backend/routers/__init__.py` | reusable_backend | Package marker |
| `app/backend/routers/auth.py` | reusable_backend | `/auth/register`, `/auth/login`, `/auth/me` |
| `app/backend/routers/profile.py` | reusable_backend | `/profile` GET/PATCH |
| `app/backend/routers/dashboard.py` | reusable_backend | `/dashboard` consolidated view |
| `app/backend/routers/weather.py` | reusable_backend | `/weather/districts`, `/current`, `/historical` |
| `app/backend/routers/crop_health.py` | reusable_backend | `/crop-health/scan`, `/history` |
| `app/backend/routers/pest_alerts.py` | reusable_backend | `/pest-alerts/recent`, `/advisory` |
| `app/backend/routers/market.py` | reusable_backend | `/market/summary`, `/history` |
| `app/backend/routers/admin.py` | reusable_backend | `/admin/users`, `/audit`, `/stats` (role-protected) |
| `app/backend/services/__init__.py` | reusable_backend | Package marker |
| `app/backend/services/disease_service.py` | reusable_backend | Lazy-loaded PlantVillage v2 ResNet-18 inference |
| `app/backend/services/weather_service.py` | reusable_data_access | Reads `district_monthly_weather.csv` |
| `app/backend/services/market_service.py` | reusable_backend | Mock market rates with explicit `status: mock` |
| `app/backend/services/satellite_service.py` | reusable_backend | Mock satellite summary with explicit `status: mock` |
| `app/backend/services/pesticide_service.py` | reusable_backend | Mock pesticide advisory with explicit `status: mock` |
| `app/config/__init__.py` | reusable_backend | Settings exports |
| `app/config/settings.py` | reusable_backend | Pydantic env-driven configuration |
| `app/security/__init__.py` | reusable_security | Public security exports |
| `app/security/auth.py` | reusable_security | bcrypt, JWT, roles, `get_current_user`, rate limiting |
| `app/security/upload.py` | reusable_security | File validation, path-traversal protection |
| `app/security/audit.py` | reusable_security | JSON-lines audit logging |
| `tests/test_mvp.py` | reusable_test_reference | Smoke tests for the API; reusable as mobile backend contract tests |
| `scripts/run_mvp_smoke_tests.py` | reusable_test_reference | Script that runs `tests/test_mvp.py` |
| `app/frontend/index.html` | web_frontend_deprecated | Dashboard page (localStorage token) |
| `app/frontend/login.html` | web_frontend_deprecated | Login page |
| `app/frontend/register.html` | web_frontend_deprecated | Registration page |
| `app/frontend/profile.html` | web_frontend_deprecated | Profile edit page |
| `app/frontend/scan.html` | web_frontend_deprecated | Crop scan page |
| `app/frontend/weather.html` | web_frontend_deprecated | Weather page |
| `app/frontend/irrigation.html` | web_frontend_deprecated | Irrigation page |
| `app/frontend/pest-alerts.html` | web_frontend_deprecated | Pest alerts page |
| `app/frontend/market.html` | web_frontend_deprecated | Market page |
| `app/frontend/settings.html` | web_frontend_deprecated | Settings page |
| `app/frontend/admin.html` | web_frontend_deprecated | Admin page |
| `app/frontend/static/css/style.css` | web_frontend_deprecated | Stylesheet |
| `app/frontend/static/js/app.js` | web_frontend_deprecated | Shared JS (localStorage token, i18n) |

## Backend API inventory

Base path: `/api/v1`

| Method | Endpoint | Auth | Description |
|--------|----------|------|-------------|
| POST | `/auth/register` | Public | Register farmer/extension_worker/admin |
| POST | `/auth/login` | Public | Login, returns JWT |
| GET | `/auth/me` | Bearer | Current user identity |
| GET | `/profile` | Bearer | Get farmer profile |
| PATCH | `/profile` | Bearer | Update profile fields |
| GET | `/dashboard` | Bearer | Consolidated dashboard payload |
| GET | `/weather/districts` | Bearer | List districts |
| GET | `/weather/current` | Bearer | Latest weather for district |
| GET | `/weather/historical` | Bearer | Historical weather rows |
| POST | `/crop-health/scan` | Bearer | Upload image, run v2 inference |
| GET | `/crop-health/history` | Bearer | User scan history |
| GET | `/pest-alerts/recent` | Bearer | Recent pest alerts (mock) |
| POST | `/pest-alerts/advisory` | Bearer | Advisory for crop/pest (mock) |
| GET | `/market/summary` | Bearer | Market summary (mock) |
| GET | `/market/history` | Bearer | Price history (mock) |
| GET | `/admin/users` | Bearer + admin | List users |
| GET | `/admin/audit` | Bearer + admin | Audit log entries |
| GET | `/admin/stats` | Bearer + admin | User stats |
| GET | `/health` | Public | Health check |

## Auth model

- Passwords are hashed with bcrypt via `passlib` (`app/security/auth.py`).
- JWT access tokens are HS256 and contain claims: `sub` (user_id), `role`, `phone`, `iat`, `exp`, `type`.
- Token lifetime: `jwt_access_token_minutes` (default 60).
- Roles: `farmer`, `extension_worker`, `admin`.
- `require_role(...)` dependency enforces role guards.
- In-memory rate limiting per IP/path and per login phone.

## Database schema (JSON-backed MVP store)

File: `app_data/store/users.json`

```json
{
  "users": {
    "<phone>": {
      "id": "user_000001",
      "phone": "...",
      "role": "farmer",
      "password_hash": "...",
      "created_at": "..."
    }
  },
  "profiles": {
    "user_000001": {
      "user_id": "...",
      "name": "...",
      "phone": "...",
      "email": null,
      "district": null,
      "crop": null,
      "farm_size_acres": null,
      "irrigation_type": null,
      "language": "en"
    }
  },
  "scans": {
    "user_000001": [
      {
        "scan_id": "scan_000001",
        "user_id": "...",
        "image_path": "...",
        "predicted_class": "...",
        "confidence": 0.95,
        "model_version": "...",
        "uncertain": false,
        "scanned_at": "..."
      }
    ]
  }
}
```

## Reusable components for Flutter

1. **Backend API** – all endpoints above can be consumed directly.
2. **Pydantic schemas** – request/response contracts for Dart model generation.
3. **Security utilities** – token creation/validation stays on backend; mobile only stores and sends tokens.
4. **Data services** – weather CSV reader and mock service implementations remain valid.
5. **Test contracts** – `tests/test_mvp.py` documents the exact behavior the Flutter repositories must mirror.

## Unsafe/deprecated frontend patterns

| Issue | Location | Why it must not move to mobile |
|-------|----------|--------------------------------|
| Token stored in `localStorage` | `app/frontend/static/js/app.js` | localStorage is accessible to XSS and not encrypted. Mobile must use `flutter_secure_storage`. |
| Plaintext API prefix in JS | `app/frontend/static/js/app.js` | Acceptable for reference but mobile should read from environment/config. |
| Passwords handled by browser form | `login.html`, `register.html` | Mobile must send credentials over HTTPS only and never log them. |
| No certificate pinning / HTTPS enforcement | web reference | Mobile release config must enforce HTTPS. |

## Secrets audit

- `app/config/settings.py` uses environment variables and dev-only defaults. No production secrets are committed.
- `app/frontend/` contains no API keys, backend secrets, or passwords.
- Mobile code must continue this policy: base URL in config, token in secure storage, no secrets in source.

## Recommendation

Keep the backend and security modules unchanged. Build the Flutter app as a first-class client of the existing `/api/v1` endpoints. Use repository interfaces so live and mock implementations can be swapped without touching UI code.
