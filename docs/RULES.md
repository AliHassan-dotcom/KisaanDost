# Kisaan Dost — Engineering Rules: What to Use, What to Avoid

These rules are binding for all contributors. They exist to protect the product's core promises: **simple, Urdu-first, low-bandwidth, decision-focused**.

---

## 1. Universal Product Rules

1. **Show decisions, not data.** No raw NDVI/NDWI values as primary UI. Status + reason + action. (PRD principle)
2. **Urdu-first, always bilingual.** Every user-facing string exists in Urdu *and* English — string resources only, **zero hardcoded strings** in any client code.
3. **Low bandwidth is a feature.** Alert payloads < 2 KB; no video in core flows; images lazy-loaded and compressed; paginate everything.
4. **The map is optional.** No flow may require map literacy — pin + radius is a first-class path, not a fallback hack.
5. **Stale data must be visible.** Every number shown carries its date ("as of"). Never present cached data as fresh.
6. **One module failing ≠ app failing.** Weather, prices, crop health degrade independently (see ERROR_HANDLING.md).
7. **Keep the stack simple.** Any new dependency must answer: *which farmer decision does this improve?* If none — rejected.

---

## 2. Libraries — Approved / Avoid

### 2.1 Backend (Python 3.12 / FastAPI)

| ✅ Use | Purpose | ❌ Avoid | Why |
|---|---|---|---|
| FastAPI | API framework | Django, Flask | Django is too heavy for API-first; Flask lacks async + native validation |
| Pydantic v2 | Schemas & validation | marshmallow, manual dict handling | FastAPI-native, fastest validation |
| SQLAlchemy 2.0 + Alembic | ORM + migrations | Peewee, raw SQL | Typed, migration-controlled |
| asyncpg (via SQLAlchemy async) | Postgres driver | psycopg2 in async paths | asyncpg is the async driver |
| GeoAlchemy2 | PostGIS geometry types | hand-built WKT strings | Type-safe spatial columns |
| shapely | AOI polygon validation | — | Self-intersection / closure checks before insert |
| Celery + Redis | Background jobs & scheduling | RQ, Huey, asyncio background tasks | Retries + beat scheduling are required |
| earthengine-api | GEE access — **workers only** | client-side GEE, google-colab patterns | Credentials never leave the server |
| scikit-learn + joblib | Disease risk model (Phase 2) | TensorFlow/PyTorch | KNN-scale problem; no GPU justification |
| httpx | HTTP client for external APIs | requests in async code | httpx supports async + timeouts natively |
| structlog | Structured logging | print, f-string logging | request_id correlation |
| sentry-sdk | Error tracking | — | — |
| pytest + factory-boy | Tests | unittest | Fixtures, parametrize |

**Blocked in backend:** Django, GraphQL (Strawberry/Ariadne) — REST is sufficient; any ORM-bypassing string-built SQL (injection risk); `pickle` for anything crossing a trust boundary; global mutable singletons for state.

### 2.2 Mobile (Flutter)

| ✅ Use | Purpose | ❌ Avoid | Why |
|---|---|---|---|
| Riverpod | State management | setState in feature code, BLoC (team-size call), Redux | Compile-safe, testable, low boilerplate |
| dio (+ interceptors) | HTTP + retries + auth token refresh | http package raw | Interceptor support for JWT/refresh flow |
| freezed + json_serializable | Immutable models | manual `fromJson` maps | Type safety, less drift |
| go_router | Navigation + deep links | Navigator 1.0 push pile | Alert deep-links into farm screens |
| flutter_secure_storage | Tokens | SharedPreferences for secrets | Encrypted storage |
| flutter_localizations + intl | Urdu RTL, formatting | custom bidi hacks | First-class RTL; test with locale `ur` |
| fl_chart | NDVI/price trend charts | syncfusion (license), heavy chart libs | Lightweight, free |
| cached_network_image | Images | Image.network raw | Low-bandwidth friendliness |
| firebase_messaging | Push | — | FCM is the push choice |
| flutter_map + OSM tiles | Optional map screen | **google_maps_flutter** | No API key cost, smaller binary, OSM tiles are free; map is optional anyway |

**Blocked in mobile:** WebView-rendered UI (fragile, heavy, offline-hostile); Google Maps SDK (cost + APK size); Google Sign-In / email auth (farmers use phones); video players in core flows; any analytics SDK > 100 KB that phones home on every frame.

### 2.3 Web Dashboard (Next.js, Phase 2 — rules fixed now)

| ✅ Use | Purpose | ❌ Avoid | Why |
|---|---|---|---|
| Next.js App Router + TypeScript strict | Framework | JavaScript files, CRA | Type safety from day one |
| TanStack Query | Server state | Redux Toolkit Query, SWR-mixing | One server-state pattern |
| Tailwind CSS + shadcn/ui | Styling & components | MUI + Emotion, styled-components | Small bundles, no runtime CSS-in-JS |
| zod | Form/env validation | manual parsing | — |
| Zustand | *Client-only* state (filters, UI) | Redux for server state | Server state ≠ client state |

**Blocked in web:** GraphQL clients (REST only); moment.js (use date-fns); importing backend Python types by hand without generating from OpenAPI.

---

## 3. Backend Layering Rules (enforced in review)

```
endpoint (routers)  →  service (domain logic)  →  repository (SQLAlchemy)  →  models
        ↑ Pydantic schemas at the boundary only
```

1. **No business logic in endpoints.** Endpoints parse → call service → return schema.
2. **Risk engine is a pure module** — no DB access, no I/O; inputs in, output out. (Keeps it unit-testable and swappable to ML.)
3. **GEE / earthengine calls live in `workers/` (or a threadpool) — never in the async request path.** The `earthengine-api` is blocking; calling it in an event loop stalls every request.
4. **Every external call has an explicit timeout** (httpx `timeout=`, Celery `soft_time_limit`). No unbounded network I/O, ever.
5. **Transactions:** one service call = one transaction boundary; workers commit their own.
6. **Schema changes only via Alembic migration.** Manual DDL in any environment = review reject.
7. **Config from environment only** (pydantic-settings). No constants files with environment-specific values.
8. **Cache invalidation:** services write-through — when a worker stores a new analysis/score, it deletes the affected Redis dashboard keys. Never cache forever.

## 4. Mobile Architecture Rules

1. **Feature-first folder structure** (`features/dashboard`, `features/farm`, …) — not layer-first (`screens/`, `blocs/` mega-folders).
2. **Offline-first:** every viewed screen is persisted locally (last-known + timestamp); the app must open usable with zero connectivity.
3. **Errors shown to farmers are bilingual and human** — map any `ApiException` to a friendly message + retry (see ERROR_HANDLING.md). Raw exception text is a bug.
4. **RTL testing is part of done:** every screen is reviewed in `ur` and `en` locales before merge.
5. **APK size budget: < 25 MB**, cold start < 3 s on a 2 GB RAM device. Features that break the budget need explicit approval.

## 5. API Conventions

- REST, versioned prefix: `/api/v1/...`
- JSON only; camelCase in payloads; UTC ISO-8601 timestamps; every response carries `request_id`.
- Success envelope: `{"success": true, "data": ...}` · Error envelope: see ERROR_HANDLING.md §2.
- List endpoints paginate (`?page`, `?page_size` ≤ 50).
- Auth: `Authorization: Bearer <access>`; refresh endpoint rotates refresh tokens.

## 6. Git & Workflow Rules

- Trunk-based: `feat/<short>`, `fix/<short>`, `docs/<short>` branches → PR to `main`.
- Conventional commits (`feat:`, `fix:`, `chore:` …) — PR titles feed changelog.
- PR checks must pass: backend (ruff + mypy + pytest), mobile (dart analyze + flutter test), web (tsc + vitest + eslint).
- No direct pushes to `main`. No force-push to shared branches. No `--no-verify`.

## 7. Security Rules

1. GEE service-account JSON exists **only** in the secret manager and the worker container env — never in git, never in the API image layer, never on any client.
2. OTP: 6-digit, 5-min TTL, max 5 attempts, max 3 sends/hour/number — stored in Redis, not Postgres.
3. Rate-limit auth endpoints per IP *and* per phone number.
4. Validate every AOI polygon server-side (shapely) before any GEE call — malformed geometry wastes quota.
5. Parameterized SQL only (ORM/SQLAlchemy constructs); no f-string SQL.
6. JWT access 30 min / refresh 30 days; refresh rotation + reuse detection.
7. Dependency audit (pip-audit / npm audit / `dart pub outdated`) in CI weekly.

## 8. The "Do Not Build" List (scope guard)

Until the MVP is validated in the field, the following are **banned from the codebase**, even if "easy": marketplace/e-commerce, chat (Phase 3 only), video content, IoT integrations, multi-tenant advisor billing, microservice split, Kubernetes, GraphQL, real-time WebSocket dashboards.
