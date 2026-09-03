# Kisaan Dost — Architecture Documentation

Diagrams use **Mermaid** — they render natively on GitHub, GitLab, and in VS Code (with the built-in Markdown preview + Mermaid support).

## Document Index

| File | Contents |
|---|---|
| [01-system-architecture.md](01-system-architecture.md) | High-level system & component architecture, layer responsibilities, key architectural decisions |
| [02-data-flow-gee.md](02-data-flow-gee.md) | End-to-end satellite analysis pipeline (AOI → GEE → risk score), caching strategy, sequence diagrams |
| [03-database-erd.md](03-database-erd.md) | PostgreSQL/PostGIS entity-relationship diagram and table definitions |
| [04-deployment.md](04-deployment.md) | Environments, Docker topology, CI/CD pipeline, monitoring |

## Quick Overview (ASCII)

```
┌─────────────┐   ┌──────────────┐
│ Flutter App │   │ Next.js Web  │      CLIENT LAYER
│ (farmers)   │   │ (admin/adv.) │      Android-first + dashboard
└──────┬──────┘   └──────┬───────┘
       │      HTTPS/REST │
       └───────┬─────────┘
        ┌──────▼───────┐
        │   FastAPI    │      API LAYER — auth, validation,
        │  Backend API │      orchestration, risk engine
        └──┬────────┬──┘
   enqueue  │        │ read/write
        ┌───▼───┐ ┌──▼─────────────┐
        │ Redis │ │ PostgreSQL     │      DATA LAYER
        │ cache │ │ + PostGIS      │      farms, AOIs, scores
        │ broker│ └────────────────┘
        └───┬───┘
        ┌───▼────────────┐            EXTERNAL LAYER
        │ Celery Workers │  ┌────────┐  (backend-only access)
        │ GEE│weather│   │→│  GEE   │  Google Earth Engine
        │ price│alerts   │ │ Weather│  Weather provider
        └─────────────────┘ │ Prices │  Mandi price sources
                            │ FCM/SMS│ Push + OTP
                            └────────┘
```

## The 5 Architectural Rules

1. **GEE is never exposed to clients.** All Earth Engine calls go through the backend with a service account.
2. **Satellite analysis is always asynchronous.** API requests enqueue work; farmers read cached results.
3. **Cache-first reads.** Redis fronts PostgreSQL for summaries/prices; workers refresh data in the background.
4. **One module failing must never kill the dashboard.** Weather, prices, and crop health degrade independently.
5. **The risk engine is a pure function** of its inputs (indices, forecast, crop) — testable and replaceable (rules v1 → ML v2) without touching the output contract.
