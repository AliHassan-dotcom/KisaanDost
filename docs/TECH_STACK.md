# Kisaan Dost — Tech Stack

Guiding rule from the stack document: **"Keep the stack simple. Use only the parts that directly help the farmer make a better decision."**

## Summary Table

| Layer | Choice | Version | Why | Rejected alternative |
|---|---|---|---|---|
| **Mobile app** | Flutter | 3.x stable | Lightweight, Android-first with iOS-ready, first-class RTL/Urdu support, single codebase | React Native (weaker RTL story early), native x2 (double effort) |
| **Web dashboard** | Next.js (App Router) + TypeScript | 14/15 | Admin/advisor panels, SEO-less internal tool, fast to build, React ecosystem | Plain CRA (dead end), Vue (team familiarity) |
| **Backend API** | FastAPI (Python) | 3.12 runtime | Async I/O for external calls, Pydantic validation, OpenAPI docs auto-generated — Python is also required for GEE + scikit-learn in the same language | Flask (weaker async/validation), Django (too heavy for an API-first service) |
| **Satellite engine** | Google Earth Engine (`earthengine-api`) | latest | NDVI/NDWI/anomaly computation at scale; `reduceRegion(s)()` for AOI summaries; free-ish research tier | Self-hosted raster processing (massive cost/complexity) |
| **ML** | scikit-learn (KNN disease risk) | 1.x | Small interpretable model for Phase 2; joblib artifacts in S3; upgrade path XGBoost/time-series | Deep learning (no data volume to justify it yet) |
| **Database** | PostgreSQL + PostGIS | 16 / 3.4 | Farm polygons are queryable first-class data (area, district lookup, spatial batching) | MongoDB (weak geo), MySQL (PostGIS is stronger) |
| **ORM / migrations** | SQLAlchemy 2.0 + Alembic | latest | Typed models, controlled migrations | Django ORM (no Django), raw SQL (maintenance risk) |
| **Cache & queue** | Redis 7 | 7.x | Dashboard/price cache + Celery broker in one dependency | Memcached (no queues) |
| **Background jobs** | Celery + Celery Beat | 5.x | Retries with backoff, scheduled syncs (weather/price), mature ops tooling | RQ (weak scheduling), Dramatiq (smaller ecosystem) |
| **Auth** | Phone OTP → JWT (access + refresh) | — | Farmers have phones, not emails; no third-party lock-in; FCM token binding | Firebase Auth (viable fallback if OTP delivery becomes painful — decision point, not a default) |
| **Push notifications** | Firebase Cloud Messaging | — | Free, reliable on Android, per-device tokens | SMS alerts (cost; keep as High-severity fallback later) |
| **OTP delivery** | SMS gateway (Twilio or local PK aggregator) | — | Local aggregators (Jazz/Telenor bulk SMS) are cheaper in PK; abstracted behind one interface | Email OTP (farmers don't use email) |
| **Object storage** | S3-compatible (MinIO dev / S3 or GCS prod) | — | Report exports, ML artifacts | DB blobs |
| **DevOps** | Docker + docker-compose + GitHub Actions | — | Reproducible envs, simple CI/CD; see architecture/04-deployment.md | Kubernetes (explicitly deferred) |
| **Error tracking** | Sentry | — | Backend + Flutter + web in one place | DIY logging (wastes time) |
| **Logging** | structlog (JSON) | — | `request_id` correlation API → worker → GEE | print / unstructured logs |

## MVP Stack (what Phase 1 actually runs)

```
Flutter  ·  FastAPI  ·  PostgreSQL+PostGIS  ·  Redis  ·  Celery
Google Earth Engine  ·  FCM  ·  SMS OTP  ·  Docker  ·  GitHub Actions
```

The **web dashboard is Phase 2** (advisor portal). Build it after farmer-app validation — but the API is designed so it needs no changes.

## Language & Runtime Matrix

| Runtime | Used by |
|---|---|
| Python 3.12 | Backend API, Celery workers, GEE, scikit-learn, Alembic |
| Dart | Flutter app |
| TypeScript (strict) | Next.js dashboard |

## Data Validation & Serialization

- **Backend boundary:** Pydantic v2 schemas — every request/response validated; never accept raw dicts from external APIs into the domain (normalize first).
- **GeoJSON:** AOI polygons validated with `shapely` (self-intersection, ring closure) *before* PostGIS insert.
- **Mobile:** model classes via `freezed` + `json_serializable` — no manual `Map<String, dynamic>` decoding in UI code.

## External Integrations & Their Abstractions

Each external source sits behind one internal interface so sources can be swapped without touching features:

| Interface | Implementations | Notes |
|---|---|---|
| `WeatherProvider` | Open-Meteo / OpenWeather (pick at build time) | Normalized forecast schema |
| `PriceProvider` | Agri marketing board feed(s), other sources | All rows carry `as_of` source timestamp |
| `SatelliteEngine` | GEE implementation | Only implementation, but interface keeps the pipeline testable with fixtures |
| `SmsSender` | Local PK aggregator (primary), Twilio (backup) | OTP only |
| `PushSender` | FCM | Alert dispatch |

## Future Additions (explicitly *not* MVP)

Push notification rich media · voice alerts (TTS) · advisor portal (web) · farmer group management · yield prediction (XGBoost/time-series) · multilingual expansion (Sindhi, Punjabi, Saraiki).

## Why This Stack (from the source docs)

- Python fits Earth Engine work well — one language for API + satellite + ML.
- PostgreSQL + PostGIS is ideal for farm polygons.
- Redis prevents repeated satellite calls (GEE quota is precious).
- Flutter keeps the app lightweight on low-end Android devices.
- FastAPI is fast and simple for backend services.
