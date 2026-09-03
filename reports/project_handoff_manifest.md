# Project Handoff Manifest

## Freeze Status

Repository frozen and ready for Antigravity Pro continuation.

This is a freeze-only handoff: no product logic, dependency, schema, model, data, or validated artifact was changed. The machine-readable authority is `reports/project_handoff_manifest.json`; executed verification evidence is `reports/final_project_verification.json`.

## Live Components

| Component | Path | Status | Downstream dependencies |
|---|---|---|---|
| FastAPI backend | `app/` | Live; tests pass with a model-runtime configuration blocker. | `data/processed/`, `Kisaan_Dost_Data/processed/`, Python runtime. |
| Flutter app | `mobile_app/` | Live; analysis clean and 44 tests pass. | Flutter SDK, `/api/v1`, Android device/emulator. |
| Legacy backend scaffold | `backend/` | Do not extend. | Superseded by `app/`. |
| Legacy mobile scaffold | `mobile/` | Do not extend. | Superseded by `mobile_app/`. |
| Legacy web | `web/` | Deprecated. | Superseded by Flutter. |

## Mobile Handoff

- **Root/entry:** `mobile_app/`, `mobile_app/lib/main.dart`.
- **Screens:** splash, login, registration, dashboard, profile, scan, weather, irrigation, pest alerts, satellite, market, settings, admin placeholder.
- **Routing/roles:** `mobile_app/lib/routing/app_router.dart`; unauthenticated users redirect to login; `/admin` requires admin role; extension-worker has no distinct UI flow.
- **Data mode:** `--dart-define=USE_MOCKS=true` selects compile-time mock repositories. Live mode uses `API_BASE_URL` and `/api/v1`.
- **Token storage:** `flutter_secure_storage`; no password persistence.
- **Commands:** `flutter run --dart-define=USE_MOCKS=true`; `flutter run --dart-define=API_BASE_URL=http://10.0.2.2:8000`; `flutter analyze`; `flutter test`; `flutter build apk --debug`.
- **APK:** preserved debug artifact: `mobile_app/build/app/outputs/flutter-apk/app-debug.apk`. It was not overwritten during freeze.

## Backend Handoff

- **Run:** `python -m uvicorn app.backend.main:app --host 0.0.0.0 --port 8000`.
- **Prefix/contracts:** `/api/v1`; schemas in `app/backend/schemas.py`.
- **Endpoints:** auth, profile, dashboard, weather, crop-health scan/history, pest alert/recent/advisory/sources, market, and admin routers. Full inventory is in the JSON manifest.
- **Auth/security:** bcrypt, JWT role claims, admin dependencies, in-memory rate limits, upload validation, JSONL audit log.
- **Storage constraint:** `app_data/store/users.json` is MVP-only; it is not transaction-safe or multi-process safe. PostgreSQL is required before production.

## ML Handoff

- **Checkpoints:** baseline `Kisaan_Dost_Data/models/best_plantvillage_model.pt`; selected v2 `Kisaan_Dost_Data/models/best_plantvillage_model_v2.pt`.
- **Architecture/preprocess:** ResNet-18 with selected `mlp_256` head; resize 256, center crop 224, ImageNet normalization.
- **Classes:** mapping at `Kisaan_Dost_Data/data/processed/plantvillage_class_mapping.csv`; 15 Pepper bell/Potato/Tomato PlantVillage classes.
- **Metrics:** baseline test accuracy/macro-F1: 0.8507/0.8281; v2: 0.8963/0.8825.
- **Endpoint/policy:** `POST /api/v1/crop-health/scan`; confidence below 0.75 is uncertain; output never prescribes pesticide use.
- **Blocker:** runtime settings expect `models/best_plantvillage_model_v2.pt`, but v2 is under `Kisaan_Dost_Data/models/`. Documented only; not changed during freeze.

## Data and Provenance

| Domain | Key paths | Status |
|---|---|---|
| NASA/weather | `Kisaan_Dost_Data/Historical Data/`, `raw/arcgis/`, `processed/district_coordinates.csv`, `weather_join_keys.csv`, `district_monthly_weather.csv` | Validated pipeline outputs; coverage caveats remain. |
| PlantVillage | `Kisaan_Dost_Data/data/processed/*manifest*`, `models/`, reports | Validated v2 artifact; source image paths are non-portable local cache references. |
| PBS/context | `Kisaan_Dost_Data/processed/pbs_*.csv`, `kisaan_dost_context_only.csv` | PBS validation passes with documented census caveats. |
| Pesticide report | `data/processed/pesticide_report_*` | 72 facts, 43 chunks, 1 review row, zero validator errors. |
| Official pesticide source | Configured external sibling `D:/Kisaan_Dost_Data/Annual Report 2024-25_copy.pdf` | Present locally but absent from repository; portable reproduction blocked. |

## Safety Invariants

- Advisory data is report-backed and source-cited.
- No pesticide quantity is inferred, and no dose is shown without explicit source text.
- Citation title/page/section/excerpt is retained through the mobile UI.
- Disease vision is a limited classifier, not a treatment prescriber.
- Mock, historical, live, unavailable, and error status must remain visible.

## Product Status Matrix

| Feature | Status |
|---|---|
| Login/profile, dashboard | Ready for demo; backend or mock mode. |
| Crop scanning | Backend required; runtime model-path blocker. |
| Weather, irrigation | Demo-ready with historical/mock status labels. |
| Pesticide advisory | Demo-ready from extracted facts; source regeneration needs external official PDF. |
| Satellite, market | Mock only. |
| GEE, land utilization, water, trade, GDP | Deferred to Phase 2. |
| Admin dashboard | Placeholder only. |
| Notifications | Deferred to Phase 2. |
| Urdu localization | Partial locale support; translation/accessibility work pending. |
| Release signing, production database | Not production-ready. |

## Required Reading

1. `reports/final_project_verification.md`
2. `reports/pesticide_report_source_reproducibility_status.md`
3. `reports/data_model_api_lineage.md`
4. `reports/mobile_mvp_demo_guide.md`
5. `reports/security_status_and_production_backlog.md`
6. `reports/antigravity_continuation_plan.md`
