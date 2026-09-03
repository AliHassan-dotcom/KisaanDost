# Antigravity Continuation Plan

Every task below is independent, testable, and must stop at its defined boundary. Do not retrain, download, regenerate source data, or replace an official report without the explicit approval called out in the task.

## Priority 0

### P0.1 Restore and Reproduce the Official Pesticide Report

- **Objective:** Establish portable, verified provenance for the official annual report and reproduce extraction only after approval.
- **Inputs:** Original official 2024-25 report, trusted provenance/checksum, current ingestion metadata and facts.
- **Outputs:** Verified source-location record, regenerated facts/chunks/review/meta only if approved, comparison report.
- **Tests:** `tests/test_07_ingest_pesticide_report.py`, `tests/test_08_validate_pesticide_report.py`, `python scripts/08_validate_pesticide_report.py` after regeneration.
- **Acceptance criteria:** Official title/year/checksum documented; all generated facts cite page/excerpt; validation has zero errors; differences reviewed.
- **Stop condition:** Source cannot be independently verified or regeneration produces unexplained material differences.
- **Safety restrictions:** Never fabricate/substitute/OCR-reconstruct the official PDF; do not overwrite current validated outputs without approval and backup/provenance review.

### P0.2 Verify Android Device and Backend Integration

- **Objective:** Prove the frozen live API/mobile golden path on a physical Android device or emulator.
- **Inputs:** Running backend, device/emulator, API base URL, a test farmer account, current debug APK or approved fresh build.
- **Outputs:** Recorded checklist for login/profile/dashboard/weather/scan unavailable state/pest citations/logout.
- **Tests:** `flutter analyze`, `flutter test`, backend root pytest, manual golden-path check.
- **Acceptance criteria:** Auth token lifecycle, profile, status labels, citations, and logout operate against the backend; known model-path unavailability is shown safely.
- **Stop condition:** Device networking, API configuration, or security behavior diverges from documented flow.
- **Safety restrictions:** Use non-production test data; do not overwrite preserved APK without approval.

### P0.3 Configure HTTPS Release Endpoint and Signing

- **Objective:** Prepare a secure signed release path.
- **Inputs:** Controlled domain/certificate, Android signing credentials in a secret manager, release policy.
- **Outputs:** HTTPS API configuration, signed release artifact, documented signing/recovery process.
- **Tests:** Release build, device install, TLS/API connection test, startup secret validation.
- **Acceptance criteria:** No HTTP release endpoint; signing keys never enter source control; signed release works on device.
- **Stop condition:** Secrets, HTTPS ownership, or signing controls are unavailable.
- **Safety restrictions:** Never commit keystores, private keys, tokens, or production credentials.

## Priority 1

### P1.1 Replace JSON User Store with PostgreSQL

- **Objective:** Remove non-atomic single-process JSON persistence.
- **Inputs:** Current user/profile/scan schema, migration plan, PostgreSQL service, backup policy.
- **Outputs:** Versioned migrations, repository/service integration, migration/runbook.
- **Tests:** Transaction/concurrency tests, migration tests, auth/profile/scan API regression suite.
- **Acceptance criteria:** Concurrent writes are safe; data survives restart; rollback/backup/restore is demonstrated.
- **Stop condition:** Migration mapping or recovery plan is incomplete.
- **Safety restrictions:** Do not delete/overwrite user data; use staged migration and verified backups.

### P1.2 Wire Live Open-Meteo Backend Data

- **Objective:** Add explicitly labeled current-weather retrieval without replacing historical NASA data.
- **Inputs:** Existing URL builder, approved API contract, network/error policy.
- **Outputs:** Backend adapter, cached/error behavior, documented status/provenance.
- **Tests:** URL builder, mocked HTTP boundary tests, API/mobile status tests.
- **Acceptance criteria:** Live, historical, and mock responses are distinguishable; failures are safe and rate-limited.
- **Stop condition:** Provider terms, reliability, or data provenance cannot be validated.
- **Safety restrictions:** Do not present fallback values as live observations.

### P1.3 Add API/Mobile End-to-End Tests

- **Objective:** Test contracts through an actual backend/mobile integration boundary.
- **Inputs:** Stable test backend, seeded test user/data, device/emulator or integration harness.
- **Outputs:** Repeatable integration suite and CI-ready runbook.
- **Tests:** Auth/profile/weather/pest citation/scan-unavailable flows.
- **Acceptance criteria:** Contract changes break tests; source/status labels are asserted.
- **Stop condition:** Tests depend on uncontrolled live data or secrets.
- **Safety restrictions:** Use isolated test accounts and no production data.

### P1.4 Validate the Image Model Against Field Images

- **Objective:** Measure the selected model’s real-world limitations before raising product claims.
- **Inputs:** Licensed, consented field-image dataset with class labels and protocol.
- **Outputs:** Held-out field evaluation, calibration assessment, safety recommendation.
- **Tests:** Dataset integrity, no-leak split validation, reproducible evaluation.
- **Acceptance criteria:** Metrics and failure modes are reviewed by domain stakeholders.
- **Stop condition:** Licensing, consent, labels, or disease coverage are inadequate.
- **Safety restrictions:** Do not retrain/deploy until explicit approval; do not imply field validity from PlantVillage metrics.

### P1.5 Expand Urdu Localization and Accessibility

- **Objective:** Turn declared locale support into understandable, accessible product UI.
- **Inputs:** Reviewed Urdu translations, terminology guide, accessibility requirements.
- **Outputs:** Localized strings, semantics/contrast/text scaling review.
- **Tests:** Locale widget tests and manual RTL/accessibility checks.
- **Acceptance criteria:** Core flows are translated and usable under text scaling/screen reader checks.
- **Stop condition:** Translation review is unavailable.
- **Safety restrictions:** Do not machine-translate safety/chemical guidance without qualified review.

## Priority 2

### P2.1 GEE Monthly District Aggregation and Satellite Charts

- **Objective:** Add verified monthly district satellite aggregation and charts.
- **Inputs:** Approved GEE account/project, boundary policy, metric definitions.
- **Outputs:** Versioned exports, provenance, chart API/UI.
- **Tests:** Boundary/date/aggregate validation and chart status tests.
- **Acceptance criteria:** Every series identifies source, period, coverage, and missing-data state.
- **Stop condition:** GEE permissions, terms, or metric validation is incomplete.
- **Safety restrictions:** Do not start GEE work before data-governance approval.

### P2.2 Verified Market and PBS Context Sources

- **Objective:** Add verified market inputs and official land/water/production context.
- **Inputs:** Licensed/official sources and update cadence.
- **Outputs:** Normalized provenance-bearing data products and admin views.
- **Tests:** Source freshness/schema/provenance tests.
- **Acceptance criteria:** No mock values are presented as verified prices or official context.
- **Stop condition:** Source legitimacy or cadence is unknown.
- **Safety restrictions:** Do not add trade/GDP charts until sources and definitions are reviewed.

### P2.3 Admin Dashboards

- **Objective:** Build protected dashboards for land, water, trade, GDP, and operations only after data provenance is ready.
- **Inputs:** Approved data models, role policy, audit requirements.
- **Outputs:** Admin routes/API/UI with role tests and source labels.
- **Tests:** Authorization, audit, data-status, and accessibility tests.
- **Acceptance criteria:** Non-admin access is blocked; every chart includes provenance/caveats.
- **Stop condition:** Inputs are mock/unverified or role policy is unresolved.
- **Safety restrictions:** Never expose farmer PII or unpublished aggregates.

## Priority 3

### P3.1 Licensed Broader Disease Dataset Acquisition

- **Objective:** Resolve licensing/auth before expanding class coverage.
- **Inputs:** Dataset licenses, access approvals, label taxonomy.
- **Outputs:** Source inventory and approved acquisition plan.
- **Tests:** License/provenance and corruption/duplicate checks.
- **Acceptance criteria:** Each source is lawful, accessible, documented, and reproducible.
- **Stop condition:** Access/auth/licensing remains unresolved.
- **Safety restrictions:** Do not download/train on restricted sources without approval.

### P3.2 Calibration and Deployment Strategy

- **Objective:** Establish calibrated confidence and choose TFLite/TorchScript/mobile-server deployment based on measured constraints.
- **Inputs:** Field validation results, latency/memory targets, device matrix.
- **Outputs:** Calibration report and deployment decision record.
- **Tests:** Calibration, conversion parity, latency, memory, and offline/error tests.
- **Acceptance criteria:** Chosen format preserves verified behavior within thresholds.
- **Stop condition:** Conversion changes predictions beyond accepted tolerance.
- **Safety restrictions:** No production deployment without field validation and rollback plan.

### P3.3 Notifications and Advanced Personalization

- **Objective:** Add opt-in notifications and personalized advisory only after consent, data quality, and safety rules are mature.
- **Inputs:** Consent model, notification provider, reviewed advisory rules.
- **Outputs:** Opt-in UX, audit trail, preference controls, safe message templates.
- **Tests:** Consent, delivery, opt-out, rate-limit, and advisory-source tests.
- **Acceptance criteria:** Users can opt out; every advisory has provenance and no inferred dose.
- **Stop condition:** Consent, delivery reliability, or source traceability is incomplete.
- **Safety restrictions:** No unsolicited agricultural/chemical instruction and no source-less recommendation.
