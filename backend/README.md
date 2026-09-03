# Kisaan Dost Backend (FastAPI)

Crop-risk intelligence API: auth (phone OTP), farms & AOI (PostGIS), GEE satellite
pipeline (Celery workers), risk engine, mandi prices, alerts.

**Read before writing code:** [docs/RULES.md](../docs/RULES.md) · [docs/ERROR_HANDLING.md](../docs/ERROR_HANDLING.md)

## Local dev

```bash
# from repo root — start db + redis
docker compose up -d db redis

# from backend/
python -m venv .venv && source .venv/bin/activate   # Windows: .venv\Scripts\activate
pip install -r requirements.txt
cp ../.env.example .env                              # fill values
alembic upgrade head
uvicorn app.main:app --reload                        # http://localhost:8000/api/docs
```

Workers (separate terminals):

```bash
celery -A app.workers.celery_app.celery_app worker --loglevel=info
celery -A app.workers.celery_app.celery_app beat --loglevel=info
```

## Layout

```
app/
├── main.py              FastAPI app, error handlers, request-id middleware
├── core/                config (env), errors (envelope + codes), logging, security
├── api/v1/endpoints/    routers — no business logic here
├── services/            domain logic + external integrations (risk_engine is pure)
├── models/              SQLAlchemy tables (PostGIS via GeoAlchemy2)
├── schemas/             Pydantic request/response models
├── workers/             Celery app + tasks (GEE, weather, prices, alerts)
├── db/                  engine, session, declarative base
└── ml/                  disease-risk model (Phase 2) + artifacts
alembic/                 migrations — the only way schema changes
tests/                   unit/ + integration/ (pytest)
```
