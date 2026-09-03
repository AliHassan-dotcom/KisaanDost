# Data, Model, and API Lineage

## 1. Pesticide Advisory: Official Report to Mobile Citation

```text
Official Punjab annual report PDF
  -> scripts/07_ingest_pesticide_report.py
  -> data/processed/pesticide_report_chunks.jsonl
  -> data/processed/pesticide_report_facts.csv
  -> data/processed/pesticide_report_review_queue.csv
  -> data/processed/pesticide_report_ingestion_meta.json
  -> app/backend/services/pesticide_service.py
  -> /api/v1/pest-alerts/recent | advisory | sources
  -> mobile_app repositories/providers/models
  -> mobile_app/lib/screens/pest_alerts_screen.dart
```

The fact CSV schema has 22 fields: `fact_id`, category/crop/pest/district/date fields, advisory and pesticide fields, `explicit_dose_text`, safety/quality fields, source title/year/filename/page/section/excerpt, extraction status, confidence, and reviewed status. Allowed categories are `pest_warning`, `crop_disease_warning`, `pesticide_quality_control`, `pesticide_safety`, `inspection`, `laboratory_result`, and `general_agricultural_advisory`.

The service filters unrevised low-confidence facts, returns no more than `pesticide_max_citations` (default 5), and carries fact ID, category, source page, source section, and source excerpt to Flutter. Dose text is displayable only when it is an explicit verbatim substring of the source excerpt; current validated outputs contain no explicit dose text. The UI must preserve the safety notice and source citation rather than infer a pesticide quantity.

## 2. Crop Scan: Image to Uncertainty-Aware Result

```text
Farmer image upload
  -> upload validation (name, extension, claimed MIME type, size, UUID path)
  -> /api/v1/crop-health/scan
  -> app/backend/services/disease_service.py
  -> selected PlantVillage v2 checkpoint + class mapping
  -> prediction, confidence, uncertain flag
  -> Flutter scan repository/provider/screen
```

- Checkpoints: `Kisaan_Dost_Data/models/best_plantvillage_model.pt` (baseline) and `Kisaan_Dost_Data/models/best_plantvillage_model_v2.pt` (selected).
- Architecture: ImageNet-style ResNet-18 backbone with the selected `mlp_256` classification head.
- Preprocessing: resize 256, center crop 224, tensor conversion, ImageNet normalization (mean `0.485,0.456,0.406`; standard deviation `0.229,0.224,0.225`).
- Mapping: `Kisaan_Dost_Data/data/processed/plantvillage_class_mapping.csv`; 15 classes across Pepper bell, Potato, and Tomato.
- Held-out metrics: baseline accuracy 0.8507/macro-F1 0.8281; v2 accuracy 0.8963/macro-F1 0.8825.
- Scope limit: PlantVillage classes only; it is not field-image validated and does not prescribe pesticide use.
- Uncertainty policy: confidence below `0.75` is marked uncertain. The current configured model path is broken (`models/...` instead of the actual `Kisaan_Dost_Data/models/...` location), so production inference remains unavailable until an approved configuration correction.

## 3. Weather and Risk Data: Raw Sources to API Status

```text
NASA POWER daily JSON + ArcGIS boundaries + coordinate table
  -> parse_nasa_power_json.py / validate_punjab_boundaries.py
  -> spatial_join_weather_to_districts.py
  -> aggregate_weather_monthly.py
  -> processed/district_monthly_weather.csv
  -> app/backend/services/weather_service.py
  -> /api/v1/weather/* and dashboard
```

Inputs and outputs remain in `Kisaan_Dost_Data/`: `Historical Data/` for 2022–2025 NASA files, `raw/arcgis/punjab_district_boundaries.geojson`, `processed/district_coordinates.csv`, `processed/weather_join_keys.csv`, and `processed/district_monthly_weather.csv`. Six districts have no mapped grid coverage and are explicitly flagged. Weather service responses distinguish historical/live/mock/unavailable status; fallback values must remain labeled mock.

## 4. Satellite Baseline & Explainable Attention Lineage

```text
Sentinel-2 Surface Reflectance (COPERNICUS/S2_SR_HARMONIZED) + ArcGIS boundaries
  -> 09_extract_gee_monthly_satellite.py / 10_validate_gee_monthly_satellite.py
  -> processed/district_monthly_satellite_v1.csv (1,632 rows)
  -> processed/district_monthly_satellite_coverage_v1.csv
  -> processed/district_monthly_satellite_join_audit_v1.csv
  -> app/backend/services/satellite_service.py (Attention Engine)
  -> /api/v1/satellite/districts | latest | history | coverage & /dashboard
  -> mobile_app SatelliteRepository -> SatelliteProvider -> SatelliteScreen & Dashboard
```

- Schema (20 fields): `year`, `month`, `district`, `normalized_district`, `ndvi_mean`, `ndvi_median`, `ndwi_mean`, `ndwi_median`, `valid_pixel_count`, `observation_count`, `cloud_or_quality_fraction`, `satellite_source`, `product_id`, `spatial_scale_m`, `period_start`, `period_end`, `data_status`, `no_coverage_flag`, `quality_flag`, `source_processing_timestamp`.
- Non-Diagnostic Attention Statuses: `normal_observation`, `vegetation_attention`, `water_attention`, `insufficient_satellite_data`, `boundary_unavailable`.
- 5 missing boundary districts (`Bhakkar`, `Jhang`, `Layyah`, `Muzaffargarh`, `Okara`) emit `null` metrics, `data_status="boundary_unavailable"`, `no_coverage_flag=True`, and `quality_flag="missing_authoritative_arcgis_polygon"`.
- Optical cloud/fog masked months emit `null` metrics, `data_status="satellite_source_unavailable"`, `no_coverage_flag=True`, and `quality_flag="cloud_masked_no_valid_pixels"`.

## 5. API Contract Sources

- Startup/router composition: `app/backend/main.py`
- Request/response Pydantic contracts: `app/backend/schemas.py`
- Security dependencies and JWT roles: `app/security/auth.py`
- Upload constraints: `app/security/upload.py`
- Audit JSONL logging: `app/security/audit.py`
- Mobile API configuration: `mobile_app/lib/config/app_config.dart`
- Mobile source-status model: `mobile_app/lib/models/api_data_status.dart`

The live API prefix is `/api/v1`. Endpoint response envelopes are not fully uniform; mobile repositories parse endpoint-specific shapes. Preserve this fact during integration testing rather than assuming a single envelope.

## 6. Provenance and Safety Invariants

1. Report-derived advisory data is read-only and source-cited.
2. No report source means an unavailable advisory state, never invented facts.
3. No explicit source dose means no displayed dose.
4. Vision predictions are classification outputs, not treatment instructions.
5. Satellite canopy observations provide environmental context and are never labeled as crop disease diagnoses or yield predictions.
6. Mock, historical, live, unavailable, and error states must stay visible to users.
