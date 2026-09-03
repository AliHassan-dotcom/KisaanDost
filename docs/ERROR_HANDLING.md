# Kisaan Dost — Error Handling Design

**Prime directive:** a farmer on 3G with a failing external service must still get a usable screen. Errors degrade a *module*, never the product.

---

## 1. Principles

1. **Fail per-module, not per-app.** Dashboard composes weather + crop health + prices; each renders independently with its own error/stale state.
2. **Human messages, bilingual.** Farmers never see stack traces, HTTP codes, or English technical jargon. Internal detail goes to logs/Sentry only.
3. **Stale beats empty.** If fresh data is unavailable, show the last good value with its date ("6 din purana" badge) instead of an error.
4. **Every error has a code.** Client code branches on `error.code`, never on message strings.
5. **Correlate everything.** `request_id` (API) and `task_id` (workers) flow into logs and client error reports.

---

## 2. API Error Envelope (single contract for all clients)

```json
{
  "success": false,
  "error": {
    "code": "KD-FARM-002",
    "message": "Farm boundary is invalid. Please draw the outline again without crossing lines.",
    "messageUr": "زمین کی سرحد غلط ہے۔ براہِ کرم لکیریں آپس میں ملاتے بغیر دوبارہ بنائیں۔",
    "details": { "field": "polygon", "issue": "self_intersection" },
    "requestId": "req_8f3a..."
  }
}
```

- `code` — stable machine-readable identifier (registry below). **Never change a published code.**
- `message` / `messageUr` — user-safe text (may be shown as-is by clients).
- `details` — optional structured payload (validation fields, retry hints).
- HTTP status carries transport semantics; `code` carries domain semantics.

### HTTP Status Mapping

| Status | Used for |
|---|---|
| 400 | Malformed request body/params |
| 401 | Missing/expired/invalid token |
| 403 | Accessing another user's farm; wrong role |
| 404 | Farm/alert/price not found |
| 409 | Duplicate phone, duplicate farm name |
| 422 | Validation failed (with field-level `details`) |
| 429 | Rate limited (OTP resend, API abuse) — includes `Retry-After` |
| 500 | Unhandled server error (message is always generic) |
| 502 | Upstream external service failed (weather/price) |
| 503 | Degraded mode (e.g., analysis queue down) |

---

## 3. Error Code Registry

Format: `KD-<MODULE>-<NNN>`

| Module | Code | Meaning | Client behavior |
|---|---|---|---|
| AUTH | KD-AUTH-001 | Invalid/expired OTP | Show inline error, offer resend (with countdown) |
| AUTH | KD-AUTH-002 | OTP rate limited | Show "try again in X min" |
| AUTH | KD-AUTH-003 | Token expired | Silent refresh; if refresh fails → logout to login screen |
| AUTH | KD-AUTH-004 | Token invalid | Logout + clear local session |
| FARM | KD-FARM-001 | AOI too small (<0.1 ha) / too large (>2000 ha) | Field error with area guidance |
| FARM | KD-FARM-002 | Invalid polygon (self-intersection / open ring) | Re-draw prompt (see message above) |
| FARM | KD-FARM-003 | Farm not found / not owned | Remove local copy, notify |
| GEE | KD-GEE-001 | Analysis failed after retries | Keep last summary; banner "analysis delayed" |
| GEE | KD-GEE-002 | No clear (cloud-free) scene available | Status "data unavailable due to clouds", retry next cycle |
| WEATHER | KD-WX-001 | Weather provider down | Serve cached forecast + stale badge |
| PRICE | KD-PRICE-001 | Price feed unavailable | Show last rates + "as of" date |
| ALERT | KD-ALERT-001 | Push dispatch failed | In-app alert center still updated; retry queue |
| SYSTEM | KD-SYS-001 | Rate limited (429) | Back off per `Retry-After` |
| SYSTEM | KD-SYS-002 | Server error (500) | Generic bilingual "something went wrong" + retry button |
| SYSTEM | KD-SYS-003 | Network offline (client-side) | Cached screens + offline banner |

New codes are added to this file in the same PR that introduces them.

---

## 4. Backend Implementation Pattern

### Exception hierarchy (FastAPI)

```python
class AppError(Exception):
    status_code = 500
    code = "KD-SYS-002"
    message_en = "Something went wrong. Please try again."
    message_ur = "کچھ غلط ہو گیا۔ دوبارہ کوشش کریں۔"
    details: dict | None = None

class InvalidPolygon(AppError):        # e.g. FARM-002
    status_code = 422
    code = "KD-FARM-002"
    ...

class ExternalServiceError(AppError):  # 502 — weather/price upstream
    status_code = 502
    ...
```

- **One global exception handler** in `app/main.py` converts `AppError` → envelope; catches `RequestValidationError` → 422 with field details; catches `Exception` → 500 + Sentry capture.
- Services raise domain errors; endpoints never build error responses by hand.
- Never leak exception text into `message` — the generic 500 message is always returned; the traceback goes to Sentry.

### External call policy (per dependency)

| Dependency | Timeout | Retry | On final failure |
|---|---|---|---|
| GEE (`earthengine-api`) | Celery `soft_time_limit=300s` | 3×, exponential backoff (1→5→20 min) | Job → failed state, Sentry alert, farmers keep last summary; **KD-GEE-001 banner** |
| Weather API (httpx) | 10 s | 2× backoff | Serve Redis cache + stale flag; alert evaluation paused until next sync |
| Price sources (httpx) | 15 s | 2× | Source skipped this cycle; rows keep old `as_of`; ops alert if all sources stale > 48 h |
| SMS gateway (OTP) | 8 s | 2× | Return KD-AUTH-005 "delivery failed, try again"; provider fallback if configured |
| FCM | 8 s | 2× | Token marked stale on 4xx (unregistered); in-app alert still written |

### Celery worker rules

- Every task: `acks_late=True`, `max_retries=3`, `retry_backoff=True`, idempotent by nature (upsert on `(farm_id, scene_date)`).
- Final failure → mark row `status=failed`, emit structured log + Sentry, continue queue (poison-pill protection).
- **DLQ:** `task_failure` signal writes to `failed_jobs` table (task, args, error, traceback) — ops dashboard lists failures; DLQ depth > 0 pages alert.

### Validation & security edges

- AOI validation (shapely) runs *before* enqueue — invalid geometry never reaches GEE (quota protection).
- Auth errors are **generic** ("phone or code incorrect") — no user enumeration.
- 429 responses include `Retry-After`; clients must honor it.

---

## 5. Client-Side Handling (Flutter)

### Response pattern

```dart
sealed class ApiResult<T> {}
class ApiSuccess<T> extends ApiResult<T> { final T data; }
class ApiFailure<T> extends ApiResult<T> {
  final String code;        // branch on this, never on message text
  final String? messageUr;
  final String? messageEn;
  final bool retryable;     // 5xx / network / 429
}
```

### Rules

1. **dio interceptor:** catches 401 → attempts token refresh once → replays request; refresh failure → logout. Network errors → `KD-SYS-003`.
2. **Dashboard composes modules independently** — each widget (weather card, health card, price card) handles its own `ApiFailure` and renders its own degraded state. One failing card never blanks the screen.
3. **Retry UX:** failed module card shows short bilingual message + "دوبارہ کوشش کریں / Try again" button. Automatic retry only with exponential backoff (≤ 2 attempts) for `retryable` codes.
4. **Offline:** app opens to the locally cached last dashboard with an offline banner + data dates. No spinner-only screens.
5. **Never show:** raw exception text, English-only technical errors, URLs, or stack traces to users.
6. Unhandled Flutter errors → `FlutterError.onError` → Sentry (with `request_id` when available).

### Web dashboard (Phase 2)
Same envelope, same code branching; TanStack Query `retry: 1` for 5xx, error boundaries per panel, toast messages for admins can be more technical (internal tool) but still code-driven.

---

## 6. Logging & Correlation

- **Every API request:** middleware assigns `request_id` (UUID) → response header `X-Request-ID` + envelope field + structlog bind.
- **Every Celery task:** logs `task_id`, `farm_id`/source id, and the originating `request_id` when a user action triggered it.
- Log levels: `INFO` normal flow · `WARNING` external degradation (stale-cache fallback, retry exhausted) · `ERROR` failed jobs, 5xx · nothing sensitive at any level (no tokens, no phone numbers in full — mask `030••••••`).

## 7. Ops Alerting Thresholds

| Signal | Threshold | Action |
|---|---|---|
| GEE job failure rate | > 10% over 1 h | Page on-call |
| DLQ depth | > 0 | Investigate same day |
| Price feed staleness | All sources > 48 h | Investigate; consider showing regional fallback |
| Weather sync failures | 3 consecutive cycles | Page on-call |
| OTP delivery failure rate | > 5% / hour | Check SMS provider / switch fallback |
| 5xx rate | > 1% requests / 5 min | Page on-call |

---

## 8. Checklist for New Features (error-handling review)

- [ ] Defined/used error codes from the registry (added to §3 if new)
- [ ] User-safe bilingual messages for every failure path
- [ ] Module degrades independently (no whole-screen failure)
- [ ] External calls have timeout + retry + stale fallback
- [ ] Client branches on `code`, not message text
- [ ] Logs carry `request_id` / `task_id`; nothing sensitive logged
