# 03 — Database Design (ERD)

PostgreSQL 16 + PostGIS 3.4. Geometry stored in **SRID 4326** (WGS84).

## Entity-Relationship Diagram

```mermaid
erDiagram
    USERS ||--o{ FARMS : "owns"
    USERS ||--o{ DEVICES : "registers"
    USERS ||--o{ ALERTS : "receives"
    FARMS ||--o{ FARM_CROPS : "grows"
    FARMS ||--o{ AOI_ANALYSES : "is analyzed by"
    FARMS ||--o{ RISK_SCORES : "is scored by"
    CROPS ||--o{ FARM_CROPS : "planted as"
    AOI_ANALYSES ||--o{ RISK_SCORES : "input to"
    DISTRICTS ||--o{ FARMS : "located in"
    DISTRICTS ||--o{ MANDI_PRICES : "reports"
    CROPS ||--o{ MANDI_PRICES : "priced"
    PRICE_SOURCES ||--o{ MANDI_PRICES : "supplied by"
    WEATHER_SNAPSHOTS }o--|| DISTRICTS : "forecast for"
    ADVISORS ||--o{ ADVISOR_CLIENTS : "advise"
    USERS ||--o{ ADVISOR_CLIENTS : "advised by"

    USERS {
        bigint id PK
        varchar phone UK "E.164, unique"
        varchar name
        varchar preferred_lang "ur | en"
        varchar role "farmer | advisor | admin"
        timestamp created_at
        timestamp last_active_at
    }
    DEVICES {
        bigint id PK
        bigint user_id FK
        varchar fcm_token
        varchar platform "android | ios | web"
        timestamp last_seen_at
    }
    FARMS {
        bigint id PK
        bigint user_id FK
        varchar name
        geometry geom "PostGIS MultiPolygon SRID4326"
        numeric area_ha "computed via ST_Area"
        bigint district_id FK
        timestamp created_at
        bool is_active
    }
    FARM_CROPS {
        bigint id PK
        bigint farm_id FK
        bigint crop_id FK
        varchar season "rabi | kharif"
        date sowing_date "optional"
        varchar stage "sowing|growth|flowering|harvest"
        bool is_current
    }
    CROPS {
        bigint id PK
        varchar name_en
        varchar name_ur
        varchar name_sd "sindhi etc later"
    }
    DISTRICTS {
        bigint id PK
        varchar name_en
        varchar name_ur
        geometry boundary "for point-in-polygon lookup"
    }
    AOI_ANALYSES {
        bigint id PK
        bigint farm_id FK
        date scene_date "Sentinel-2 scene date"
        numeric ndvi_mean
        numeric ndwi_mean
        numeric ndvi_anomaly "vs multi-yr baseline"
        int cloud_pct
        varchar status "ok | cloud_covered | failed"
        jsonb raw_stats "full reduceRegion output"
        timestamp computed_at
    }
    RISK_SCORES {
        bigint id PK
        bigint farm_id FK
        bigint analysis_id FK
        varchar level "low | medium | high"
        jsonb reasons "ranked, bilingual"
        varchar action "irrigate|spray|wait|harvest|sell|consult"
        jsonb inputs "snapshot of scoring inputs"
        varchar engine_version "rules-v1 | knn-v1"
        timestamp created_at
    }
    WEATHER_SNAPSHOTS {
        bigint id PK
        bigint district_id FK
        jsonb forecast "provider payload, normalized"
        timestamp fetched_at
    }
    ALERTS {
        bigint id PK
        bigint user_id FK
        bigint farm_id FK "nullable"
        varchar type "weather|risk|price|system"
        varchar severity "info|warning|high"
        jsonb payload "title/body ur+en, action"
        bool is_read
        timestamp created_at
    }
    MANDI_PRICES {
        bigint id PK
        bigint district_id FK
        bigint crop_id FK
        bigint source_id FK
        numeric price_pkr "per unit (maund/kg)"
        varchar unit
        timestamp as_of "source timestamp - always shown to user"
        timestamp fetched_at
    }
    PRICE_SOURCES {
        bigint id PK
        varchar name
        bool is_active
        int trust_rank
    }
    ADVISORS {
        bigint id PK
        bigint user_id FK
        varchar organization
    }
    ADVISOR_CLIENTS {
        bigint id PK
        bigint advisor_id FK
        bigint user_id FK "client farmer"
        timestamp linked_at
    }
```

## Design Notes

1. **`farms.geom` is PostGIS geometry, not GeoJSON text.** Area (`ST_Area(geography(geom))`), district lookup (`ST_Within`), and batching (`ST_Union`) all happen in SQL.
2. **`aoi_analyses` is append-only** — full history is kept, enabling Phase-2 trend charts without migration. One row per (farm, scene_date); unique index on `(farm_id, scene_date)`.
3. **`risk_scores.inputs` snapshots the scoring inputs.** A score must always be explainable even if live data has changed since.
4. **`engine_version` on every score** — rules-v1 and ML-v2 outputs coexist during rollout and A/B comparison.
5. **`mandi_prices.as_of` is the source's own timestamp** and must be surfaced in the UI ("rates as of …"). Stale rows (>48 h) are labeled, never deleted silently.
6. **OTP codes live in Redis** (with TTL + attempt counters), not in PostgreSQL — they are ephemeral.
7. **Auditing:** table above shows the MVP core; `audit_log` (user, action, entity, before/after) is added before first production release.
8. **Migrations via Alembic only** — no manual schema changes.

## Key Indexes (beyond PKs/FKs)

```sql
CREATE UNIQUE INDEX uq_analysis_farm_date ON aoi_analyses (farm_id, scene_date);
CREATE INDEX idx_farms_user ON farms (user_id) WHERE is_active;
CREATE INDEX idx_scores_farm_latest ON risk_scores (farm_id, created_at DESC);
CREATE INDEX idx_prices_lookup ON mandi_prices (district_id, crop_id, as_of DESC);
CREATE INDEX idx_alerts_user_unread ON alerts (user_id) WHERE is_read = false;
CREATE INDEX idx_farms_geom ON farms USING GIST (geom);  -- spatial queries
```
