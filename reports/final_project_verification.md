# Final Project Verification

- Generated at (UTC): `2026-09-01T20:39:27.941371+00:00`
- Project root: `D:\KisaanDost`
- Freeze rule: no application logic, dependency, model, dataset, schema, or existing validated artifact was modified.
- Harness rule: ingestion, downloads, training, fine-tuning, comparison, migrations, and dependency installation were not invoked.

## Environment

- Python: `3.14.4 (tags/v3.14.4:23116f9, Apr  7 2026, 14:10:54) [MSC v.1944 64 bit (AMD64)]`
- Pytest: `pytest 9.1.1
`
- Flutter executable: `D:\flutter\bin\flutter.bat`
- Git repository present: `False`

## Command and Artifact Matrix

| Check | Status | Command / inspection | Result metrics | Classification |
|---|---|---|---|---|
| `root_python_tests` | **PASS** | `C:\Users\R Y Z E N\AppData\Local\Python\pythoncore-3.14-64\python.exe -m pytest tests -q -rs --tb=short` | passed=49 | — |
| `data_pipeline_tests` | **PASS** | `C:\Users\R Y Z E N\AppData\Local\Python\pythoncore-3.14-64\python.exe -m pytest Kisaan_Dost_Data/tests -q -rs --tb=short` | passed=376 | — |
| `mvp_smoke_tests` | **PASS** | `C:\Users\R Y Z E N\AppData\Local\Python\pythoncore-3.14-64\python.exe scripts/run_mvp_smoke_tests.py` | — | — |
| `pbs_validation` | **PASS** | `C:\Users\R Y Z E N\AppData\Local\Python\pythoncore-3.14-64\python.exe Kisaan_Dost_Data/scripts/validate_pbs_extracted_tables.py` | — | — |
| `pesticide_artifact_validator` | **PASS** | `validate(data/processed, reports) via scripts/08_validate_pesticide_report.py` | facts=72, chunks=43, review_queue=1, dose_integrity_violations=0 | — |
| `pesticide_artifact_consistency` | **PASS** | `read-only CSV, JSONL, and metadata consistency inspection` | required_files_present=4, facts_csv_rows=72, chunks_jsonl_rows=43, review_queue_rows=1, meta_num_facts=72, meta_num_chunks=43, meta_num_review_queue=1, meta_page_count=43, meta_status=ok, meta_table_warnings=33 | — |
| `pesticide_source_pdf_resolution` | **PASS** | `read-only source-PDF path and checksum inspection` | configured_unresolved_path=D:\KisaanDost\..\Kisaan_Dost_Data\Annual Report 2024-25_copy.pdf | — |
| `configured_data_model_paths` | **PASS** | `read-only Settings path resolution inspection` | — | — |
| `flutter_analyze` | **PASS** | `D:\flutter\bin\flutter.bat analyze` | — | — |
| `flutter_test` | **PASS** | `D:\flutter\bin\flutter.bat test` | — | — |
| `flutter_debug_apk` | **SKIPPED** | `D:\flutter\bin\flutter.bat build apk --debug` | — | freeze_protection |

## Recorded Failures and Skips

- **flutter_debug_apk** — `skipped` / `freeze_protection` / `recorded_skip`: Not executed because a debug APK may be overwritten and the freeze prohibits overwriting validated mobile artifacts. Existing artifact metadata was inspected instead: {"path": "D:\\KisaanDost\\mobile_app\\build\\app\\outputs\\flutter-apk\\app-debug.apk", "exists": true, "size_bytes": 157516411, "modified_at_utc": "2026-09-01T16:12:13.518327+00:00", "sha256": "8649a343f8c1b09179afcf81636cc8e0e5291791684ad60eca6daa6ebe0b9e5b"}

## Interpretation

- The explicit `Kisaan_Dost_Data/tests` command is required because root `pytest.ini` limits default collection to `tests`.
- The pesticide validator was invoked through its read-only function rather than its CLI wrapper because the wrapper rewrites `reports/pesticide_report_extraction_quality.md`, outside the final-freeze write allow-list.
- Flutter analysis and tests are attempted only from `mobile_app/`; `mobile/` is a legacy scaffold referenced by stale Makefile targets.
- The APK build is recorded as a safety skip when its output already exists because the freeze prohibits overwriting validated mobile artifacts.
- Every non-pass outcome is retained above and in `final_project_verification.json`.

## Freeze Status

Repository frozen and ready for Antigravity Pro continuation.
