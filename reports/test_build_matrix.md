# Test and Build Matrix

Final verification ran on 2026-09-01 using Python 3.14.4, pytest 9.1.1, and `D:\flutter\bin\flutter.bat`. No dependency installation, data extraction, training, or artifact regeneration occurred.

| Area | Command / inspection | Outcome | Evidence | Classification |
|---|---|---|---|---|
| FastAPI, pesticide extraction, API contracts | `python -m pytest tests -q -rs --tb=short` | PASS | 38 passed, 1 skipped; skipped inference test says v2 checkpoint not available. | Verified; runtime model configuration gap recorded separately. |
| NASA POWER, boundaries, coordinates, joins, aggregation, versioned master | `python -m pytest Kisaan_Dost_Data/tests -q -rs --tb=short` | PASS | 376 passed. Explicit path is required because root `pytest.ini` uses `testpaths = tests`. | Verified. |
| PlantVillage ingestion, split, train/evaluate/finetune/comparison test suites | Included in `Kisaan_Dost_Data/tests` command | PASS | 376 data tests include all existing PlantVillage test modules. No training command was rerun. | Verified test logic; models/data frozen. |
| Pesticide artifact tests | Included in root pytest command | PASS | Extraction and validation test modules passed. | Verified. |
| Pesticide artifact validator | Read-only `validate()` from `scripts/08_validate_pesticide_report.py` | PASS | 72 facts, 43 chunks, 1 review row, 0 dose-integrity violations. | Verified. |
| PBS tables | `python Kisaan_Dost_Data/scripts/validate_pbs_extracted_tables.py` | PASS | All checks passed; four documented census rounding/blank-value information notes. | Verified. |
| MVP smoke tests | `python scripts/run_mvp_smoke_tests.py` | PASS | 13 passed, 1 model-dependent skip. | Verified. |
| Flutter static analysis | `D:\flutter\bin\flutter.bat analyze` in `mobile_app/` | PASS | `No issues found!` | Verified. |
| Flutter unit/widget suite | `D:\flutter\bin\flutter.bat test` in `mobile_app/` | PASS | 44 tests passed. | Verified. |
| Android debug build | `D:\flutter\bin\flutter.bat build apk --debug` | SKIPPED | Existing `mobile_app/build/app/outputs/flutter-apk/app-debug.apk` was preserved; SHA-256 `8649a343f8c1b09179afcf81636cc8e0e5291791684ad60eca6daa6ebe0b9e5b`. | Freeze protection, not a code failure. |
| Configured ML runtime path | Read-only `Settings` path inspection | FAIL | Config resolves `models/best_plantvillage_model_v2.pt`, which is absent; actual v2 checkpoint exists at `Kisaan_Dost_Data/models/best_plantvillage_model_v2.pt`. | Code/configuration blocker; not fixed during freeze. |
| Pesticide PDF portability | Read-only path/checksum inspection | PASS with blocker | Nested repository candidate is missing; external configured sibling exists with recorded hash. | Source portability blocker. |

## Commands Not Run

| Command | Reason |
|---|---|
| `python scripts/07_ingest_pesticide_report.py` | Regenerates extraction artifacts; prohibited during freeze. |
| PlantVillage download/train/evaluate/fine-tune/comparison scripts | Download, retrain, or overwrite models/reports; prohibited during freeze. |
| Weather/join/aggregation/build-master scripts | Rewrite validated data outputs; prohibited during freeze. |
| `flutter build apk --debug` | Would risk overwriting the preserved debug APK. |
| `make test-backend`, `make analyze-mobile`, `make test-mobile` | Makefile targets legacy `backend/` and `mobile/` scaffolds, not live `app/` and `mobile_app/`. |

## Artifact Versions

- Pesticide ingestion metadata: 43 pages, 72 facts, 43 chunks, one review row, 33 table-extraction warnings, zero tables extracted.
- PlantVillage selected checkpoint: `Kisaan_Dost_Data/models/best_plantvillage_model_v2.pt`, 44,815,115 bytes.
- Flutter debug APK preserved: 157,516,411 bytes, modified 2026-09-01 UTC.

All raw command outputs and classifications are retained in `reports/final_project_verification.json`.
