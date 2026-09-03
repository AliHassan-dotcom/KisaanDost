# Kisaan Dost

**Pakistan's most practical crop-risk assistant.**

An AI-powered crop-risk intelligence platform that turns weather, satellite data
(Google Earth Engine), and mandi prices into one simple answer for farmers:
**risk level + reason + next action** — irrigate, spray, wait, or sell.

> Product principle: **Do not show raw satellite data to farmers. Show decisions.**

## Documentation

| Doc | Contents |
|---|---|
| [docs/PRD.md](docs/PRD.md) | Product requirements: users, personas, feature-to-user matrix, phases, MVP scope |
| [docs/architecture/](docs/architecture/README.md) | System architecture, GEE data flow, database ERD, deployment — Mermaid diagrams |
| [docs/TECH_STACK.md](docs/TECH_STACK.md) | Stack decisions, versions, rationale |
| [docs/RULES.md](docs/RULES.md) | Engineering rules: approved/blocked libraries, conventions, security |
| [docs/ERROR_HANDLING.md](docs/ERROR_HANDLING.md) | Error envelope, code registry, failure policies per external service |

## Repository Layout

```
kisaandost/
├── docs/                  PRD, architecture diagrams, stack, rules, error design
├── backend/               FastAPI API + Celery workers + GEE pipeline (Python 3.12)
├── mobile/                Flutter farmer app (Android-first, Urdu/English)
├── web/                   Next.js admin/advisor dashboard (Phase 2)
├── docker-compose.yml     dev environment: Postgres+PostGIS, Redis, API, workers
├── .env.example           all environment keys (never commit real .env)
└── Makefile               common commands
```

## MVP Scope (Phase 1)

Three farmer-facing capabilities, plus the platform around them:

1. **Weather** — alerts & 48h forecast
2. **Satellite crop health** — NDVI/NDWI per farm AOI → status + risk score + action
3. **Mandi prices** — district/crop rates with as-of timestamps

## Quick Start

```bash
cp .env.example .env            # fill in secrets (GEE account, SMS, FCM…)
docker compose up -d --build    # db, redis, api (:8000), worker, beat
docker compose exec api alembic upgrade head
# API docs: http://localhost:8000/api/docs

# mobile
cd mobile && flutter pub get && flutter run

# web (Phase 2)
cd web && npm install && npm run dev
```

## Stack (short version)

Flutter · FastAPI · PostgreSQL+PostGIS · Redis · Celery · Google Earth Engine ·
scikit-learn (Phase 2) · Docker · GitHub Actions — full rationale in
[docs/TECH_STACK.md](docs/TECH_STACK.md).
