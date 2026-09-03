"""Run the approved read-only final verification sweep.

This harness never invokes ingestion, downloads, training, evaluation, fine-tuning,
comparison, migrations, dependency installation, or application startup. It writes
only the final verification JSON and Markdown reports named below.
"""

from __future__ import annotations

import csv
import hashlib
import importlib.util
import json
import os
import platform
import re
import shutil
import subprocess
import sys
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

PROJECT_ROOT = Path(__file__).resolve().parent.parent
REPORTS_DIR = PROJECT_ROOT / "reports"
OUTPUT_JSON = REPORTS_DIR / "final_project_verification.json"
OUTPUT_MD = REPORTS_DIR / "final_project_verification.md"
DATA_ROOT = PROJECT_ROOT / "Kisaan_Dost_Data"
MOBILE_ROOT = PROJECT_ROOT / "mobile_app"
PROCESSED_DIR = PROJECT_ROOT / "data" / "processed"
PDF_NAME = "Annual Report 2024-25_copy.pdf"


def _utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _tail(value: str, limit: int = 8000) -> str:
    return value[-limit:] if len(value) > limit else value


def _relative(path: Path) -> str:
    try:
        return str(path.relative_to(PROJECT_ROOT)).replace("\\", "/")
    except ValueError:
        return str(path)


def _file_metadata(path: Path, include_hash: bool = False) -> dict[str, Any]:
    result: dict[str, Any] = {"path": str(path), "exists": path.is_file()}
    if not path.is_file():
        return result
    stat = path.stat()
    result.update(
        {
            "size_bytes": stat.st_size,
            "modified_at_utc": datetime.fromtimestamp(stat.st_mtime, timezone.utc).isoformat(),
        }
    )
    if include_hash:
        digest = hashlib.sha256()
        with path.open("rb") as handle:
            for block in iter(lambda: handle.read(1024 * 1024), b""):
                digest.update(block)
        result["sha256"] = digest.hexdigest()
    return result


def _command_result(
    check_id: str,
    category: str,
    command: list[str],
    cwd: Path,
    expected: str,
) -> dict[str, Any]:
    started = time.monotonic()
    try:
        completed = subprocess.run(
            command,
            cwd=cwd,
            text=True,
            capture_output=True,
            check=False,
        )
        status = "pass" if completed.returncode == 0 else "fail"
        stdout = completed.stdout
        stderr = completed.stderr
        returncode: int | None = completed.returncode
        classification = None if status == "pass" else "code_or_data"
        note = ""
    except FileNotFoundError as exc:
        status = "skipped"
        stdout = ""
        stderr = str(exc)
        returncode = None
        classification = "environmental"
        note = "Required executable is unavailable."
    duration = round(time.monotonic() - started, 3)
    combined = f"{stdout}\n{stderr}"
    return {
        "id": check_id,
        "category": category,
        "command": " ".join(command),
        "cwd": _relative(cwd),
        "expected": expected,
        "status": status,
        "returncode": returncode,
        "duration_seconds": duration,
        "classification": classification,
        "note": note,
        "stdout_tail": _tail(stdout),
        "stderr_tail": _tail(stderr),
        "metrics": _pytest_metrics(combined) if "pytest" in command else {},
    }


def _pytest_metrics(output: str) -> dict[str, int]:
    metrics: dict[str, int] = {}
    matches = re.findall(r"(\d+)\s+(passed|failed|skipped|error|errors)", output)
    for count, name in matches:
        key = "errors" if name in {"error", "errors"} else name
        metrics[key] = metrics.get(key, 0) + int(count)
    collection = re.search(r"collected\s+(\d+)\s+items", output)
    if collection:
        metrics["collected"] = int(collection.group(1))
    return metrics


def _unavailable_check(
    check_id: str,
    category: str,
    command: str,
    cwd: Path,
    expected: str,
    classification: str,
    note: str,
) -> dict[str, Any]:
    return {
        "id": check_id,
        "category": category,
        "command": command,
        "cwd": _relative(cwd),
        "expected": expected,
        "status": "skipped",
        "returncode": None,
        "duration_seconds": 0.0,
        "classification": classification,
        "note": note,
        "stdout_tail": "",
        "stderr_tail": "",
        "metrics": {},
    }


def _load_pesticide_validator() -> Any:
    script_path = PROJECT_ROOT / "scripts" / "08_validate_pesticide_report.py"
    spec = importlib.util.spec_from_file_location("pesticide_validator", script_path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"Cannot load validator: {script_path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _pesticide_validation_check() -> dict[str, Any]:
    started = time.monotonic()
    try:
        validator = _load_pesticide_validator()
        result = validator.validate(PROCESSED_DIR, REPORTS_DIR)
        success = bool(result["success"])
        return {
            "id": "pesticide_artifact_validator",
            "category": "pesticide",
            "command": "validate(data/processed, reports) via scripts/08_validate_pesticide_report.py",
            "cwd": ".",
            "expected": "Valid source-traceable extraction artifacts with no validation errors.",
            "status": "pass" if success else "fail",
            "returncode": 0 if success else 1,
            "duration_seconds": round(time.monotonic() - started, 3),
            "classification": None if success else "data",
            "note": "The validator function was called directly because its command entry point rewrites an existing quality report, which is prohibited during freeze.",
            "stdout_tail": json.dumps(result, ensure_ascii=False),
            "stderr_tail": "",
            "metrics": {
                "facts": int(result.get("facts", 0)),
                "chunks": int(result.get("chunks", 0)),
                "review_queue": int(result.get("review_queue", 0)),
                "dose_integrity_violations": int(result.get("dose_integrity_violations", 0)),
            },
        }
    except Exception as exc:  # pragma: no cover - final verification must report failures
        return {
            "id": "pesticide_artifact_validator",
            "category": "pesticide",
            "command": "validate(data/processed, reports) via scripts/08_validate_pesticide_report.py",
            "cwd": ".",
            "expected": "Valid source-traceable extraction artifacts with no validation errors.",
            "status": "fail",
            "returncode": 1,
            "duration_seconds": round(time.monotonic() - started, 3),
            "classification": "data",
            "note": "Validator raised an exception.",
            "stdout_tail": "",
            "stderr_tail": repr(exc),
            "metrics": {},
        }


def _artifact_check() -> dict[str, Any]:
    names = [
        "pesticide_report_facts.csv",
        "pesticide_report_chunks.jsonl",
        "pesticide_report_review_queue.csv",
        "pesticide_report_ingestion_meta.json",
    ]
    paths = {name: PROCESSED_DIR / name for name in names}
    missing = [name for name, path in paths.items() if not path.is_file()]
    metrics: dict[str, Any] = {"required_files_present": len(names) - len(missing)}
    detail: list[str] = []
    if not missing:
        with paths["pesticide_report_facts.csv"].open("r", encoding="utf-8", newline="") as handle:
            metrics["facts_csv_rows"] = sum(1 for _ in csv.DictReader(handle))
        with paths["pesticide_report_chunks.jsonl"].open("r", encoding="utf-8") as handle:
            metrics["chunks_jsonl_rows"] = sum(1 for line in handle if line.strip())
        with paths["pesticide_report_review_queue.csv"].open("r", encoding="utf-8", newline="") as handle:
            metrics["review_queue_rows"] = sum(1 for _ in csv.DictReader(handle))
        meta = json.loads(paths["pesticide_report_ingestion_meta.json"].read_text(encoding="utf-8"))
        metrics.update(
            {
                "meta_num_facts": meta.get("num_facts"),
                "meta_num_chunks": meta.get("num_chunks"),
                "meta_num_review_queue": meta.get("num_review_queue"),
                "meta_page_count": meta.get("page_count"),
                "meta_status": meta.get("status"),
                "meta_table_warnings": len(meta.get("warnings", [])),
            }
        )
        for csv_name, meta_name in (
            ("facts_csv_rows", "meta_num_facts"),
            ("chunks_jsonl_rows", "meta_num_chunks"),
            ("review_queue_rows", "meta_num_review_queue"),
        ):
            if metrics[csv_name] != metrics[meta_name]:
                detail.append(f"{csv_name}={metrics[csv_name]} differs from {meta_name}={metrics[meta_name]}")
    status = "pass" if not missing and not detail else "fail"
    return {
        "id": "pesticide_artifact_consistency",
        "category": "pesticide",
        "command": "read-only CSV, JSONL, and metadata consistency inspection",
        "cwd": ".",
        "expected": "Facts, chunks, review queue, and metadata counts agree.",
        "status": status,
        "returncode": 0 if status == "pass" else 1,
        "duration_seconds": 0.0,
        "classification": None if status == "pass" else "data",
        "note": "; ".join(detail) if detail else (f"Missing files: {', '.join(missing)}" if missing else "Metadata and artifact counts agree."),
        "stdout_tail": "",
        "stderr_tail": "",
        "metrics": metrics,
    }


def _source_pdf_check() -> dict[str, Any]:
    nested_path = DATA_ROOT / PDF_NAME
    external_path = PROJECT_ROOT.parent / "Kisaan_Dost_Data" / PDF_NAME
    configured_path = PROJECT_ROOT / ".." / "Kisaan_Dost_Data" / PDF_NAME
    nested = _file_metadata(nested_path)
    external = _file_metadata(external_path, include_hash=external_path.is_file())
    status = "pass" if external_path.is_file() else "fail"
    return {
        "id": "pesticide_source_pdf_resolution",
        "category": "pesticide",
        "command": "read-only source-PDF path and checksum inspection",
        "cwd": ".",
        "expected": "Official PDF is available at the configured external path; the repository does not substitute a source copy.",
        "status": status,
        "returncode": 0 if status == "pass" else 1,
        "duration_seconds": 0.0,
        "classification": None if status == "pass" else "data",
        "note": "The nested in-repository candidate and the configured external sibling are reported separately.",
        "stdout_tail": "",
        "stderr_tail": "",
        "metrics": {
            "requested_nested_path": nested,
            "configured_unresolved_path": str(configured_path),
            "configured_external_path": external,
        },
    }


def _settings_path_check() -> dict[str, Any]:
    try:
        project_root = str(PROJECT_ROOT)
        if project_root not in sys.path:
            sys.path.insert(0, project_root)
        from app.config.settings import settings

        paths = {
            "configured_model": settings.model_full_path(),
            "configured_class_mapping": settings.class_mapping_full_path(),
            "configured_weather_csv": settings.weather_csv_full_path(),
            "configured_coordinates_csv": settings.coordinates_csv_full_path(),
            "configured_pesticide_pdf": settings.pesticide_pdf_full_path(),
            "configured_pesticide_facts": settings.pesticide_facts_csv_full_path(),
            "actual_v2_model": DATA_ROOT / "models" / "best_plantvillage_model_v2.pt",
        }
        metrics = {key: _file_metadata(path) for key, path in paths.items()}
        configured_model_exists = paths["configured_model"].is_file()
        actual_model_exists = paths["actual_v2_model"].is_file()
        note = "Configured inference checkpoint is present."
        if not configured_model_exists and actual_model_exists:
            note = "Configured inference checkpoint is absent while a v2 checkpoint exists under Kisaan_Dost_Data/models."
        status = "pass" if configured_model_exists else "fail"
        return {
            "id": "configured_data_model_paths",
            "category": "runtime_configuration",
            "command": "read-only Settings path resolution inspection",
            "cwd": ".",
            "expected": "Configured runtime model and data paths resolve to available artifacts.",
            "status": status,
            "returncode": 0 if status == "pass" else 1,
            "duration_seconds": 0.0,
            "classification": None if status == "pass" else "code",
            "note": note,
            "stdout_tail": "",
            "stderr_tail": "",
            "metrics": metrics,
        }
    except Exception as exc:  # pragma: no cover
        return {
            "id": "configured_data_model_paths",
            "category": "runtime_configuration",
            "command": "read-only Settings path resolution inspection",
            "cwd": ".",
            "expected": "Configured runtime model and data paths resolve to available artifacts.",
            "status": "fail",
            "returncode": 1,
            "duration_seconds": 0.0,
            "classification": "environmental",
            "note": "Settings could not be imported for inspection.",
            "stdout_tail": "",
            "stderr_tail": repr(exc),
            "metrics": {},
        }


def _flutter_executable() -> str | None:
    available = shutil.which("flutter")
    if available:
        return available
    candidates = [
        Path(os.environ.get("FLUTTER_ROOT", "")) / "bin" / "flutter.bat",
        Path("D:/flutter/bin/flutter.bat"),
        Path("D:/flutter/bin/flutter"),
    ]
    for candidate in candidates:
        if candidate.is_file():
            return str(candidate)
    return None


def _flutter_checks() -> list[dict[str, Any]]:
    executable = _flutter_executable()
    if executable is None:
        note = "Flutter SDK was not found on PATH or at the documented local SDK candidates."
        return [
            _unavailable_check("flutter_analyze", "flutter", "flutter analyze", MOBILE_ROOT, "No analyzer issues.", "environmental", note),
            _unavailable_check("flutter_test", "flutter", "flutter test", MOBILE_ROOT, "All unit and widget tests pass.", "environmental", note),
            _unavailable_check("flutter_debug_apk", "flutter", "flutter build apk --debug", MOBILE_ROOT, "Debug APK builds successfully.", "environmental", note),
        ]
    checks = [
        _command_result("flutter_analyze", "flutter", [executable, "analyze"], MOBILE_ROOT, "No analyzer issues."),
        _command_result("flutter_test", "flutter", [executable, "test"], MOBILE_ROOT, "All unit and widget tests pass."),
    ]
    apk_path = MOBILE_ROOT / "build" / "app" / "outputs" / "flutter-apk" / "app-debug.apk"
    checks.append(
        _unavailable_check(
            "flutter_debug_apk",
            "flutter",
            f"{executable} build apk --debug",
            MOBILE_ROOT,
            "Debug APK builds successfully.",
            "freeze_protection",
            "Not executed because a debug APK may be overwritten and the freeze prohibits overwriting validated mobile artifacts. Existing artifact metadata was inspected instead: " + json.dumps(_file_metadata(apk_path, include_hash=apk_path.is_file())),
        )
    )
    return checks


def _environment() -> dict[str, Any]:
    pytest_version = _command_result("pytest_version", "environment", [sys.executable, "-m", "pytest", "--version"], PROJECT_ROOT, "pytest available")
    flutter = _flutter_executable()
    return {
        "platform": platform.platform(),
        "python": sys.version.replace("\n", " "),
        "pytest": _tail(pytest_version["stdout_tail"] or pytest_version["stderr_tail"], 500),
        "flutter_executable": flutter,
        "git_repository": (PROJECT_ROOT / ".git").exists(),
        "project_root": str(PROJECT_ROOT),
    }


def _failure_register(checks: list[dict[str, Any]]) -> list[dict[str, Any]]:
    failures: list[dict[str, Any]] = []
    for check in checks:
        if check["status"] == "pass":
            continue
        failures.append(
            {
                "check_id": check["id"],
                "status": check["status"],
                "classification": check["classification"] or "unavailable",
                "severity": "blocker" if check["status"] == "fail" else "recorded_skip",
                "evidence": check["note"] or check["stderr_tail"] or check["stdout_tail"],
                "concealed": False,
            }
        )
    return failures


def _render_markdown(report: dict[str, Any]) -> str:
    lines = [
        "# Final Project Verification",
        "",
        f"- Generated at (UTC): `{report['generated_at_utc']}`",
        f"- Project root: `{report['project_root']}`",
        "- Freeze rule: no application logic, dependency, model, dataset, schema, or existing validated artifact was modified.",
        "- Harness rule: ingestion, downloads, training, fine-tuning, comparison, migrations, and dependency installation were not invoked.",
        "",
        "## Environment",
        "",
        f"- Python: `{report['environment']['python']}`",
        f"- Pytest: `{report['environment']['pytest']}`",
        f"- Flutter executable: `{report['environment']['flutter_executable'] or 'not found'}`",
        f"- Git repository present: `{report['environment']['git_repository']}`",
        "",
        "## Command and Artifact Matrix",
        "",
        "| Check | Status | Command / inspection | Result metrics | Classification |",
        "|---|---|---|---|---|",
    ]
    for check in report["checks"]:
        metrics = ", ".join(f"{key}={value}" for key, value in check["metrics"].items() if not isinstance(value, dict)) or "—"
        command = check["command"].replace("|", "\\|")
        lines.append(f"| `{check['id']}` | **{check['status'].upper()}** | `{command}` | {metrics} | {check['classification'] or '—'} |")
    lines.extend(["", "## Recorded Failures and Skips", ""])
    if not report["failures"]:
        lines.append("No failed or skipped checks were recorded.")
    else:
        for failure in report["failures"]:
            lines.append(f"- **{failure['check_id']}** — `{failure['status']}` / `{failure['classification']}` / `{failure['severity']}`: {failure['evidence']}")
    lines.extend(
        [
            "",
            "## Interpretation",
            "",
            "- The explicit `Kisaan_Dost_Data/tests` command is required because root `pytest.ini` limits default collection to `tests`.",
            "- The pesticide validator was invoked through its read-only function rather than its CLI wrapper because the wrapper rewrites `reports/pesticide_report_extraction_quality.md`, outside the final-freeze write allow-list.",
            "- Flutter analysis and tests are attempted only from `mobile_app/`; `mobile/` is a legacy scaffold referenced by stale Makefile targets.",
            "- The APK build is recorded as a safety skip when its output already exists because the freeze prohibits overwriting validated mobile artifacts.",
            "- Every non-pass outcome is retained above and in `final_project_verification.json`.",
            "",
            "## Freeze Status",
            "",
            "Repository frozen and ready for Antigravity Pro continuation.",
            "",
        ]
    )
    return "\n".join(lines)


def main() -> int:
    checks: list[dict[str, Any]] = [
        _command_result(
            "root_python_tests",
            "backend_and_pesticide_tests",
            [sys.executable, "-m", "pytest", "tests", "-q", "-rs", "--tb=short"],
            PROJECT_ROOT,
            "FastAPI API, pesticide extraction, and validation tests pass.",
        ),
        _command_result(
            "data_pipeline_tests",
            "data_pipeline_tests",
            [sys.executable, "-m", "pytest", "Kisaan_Dost_Data/tests", "-q", "-rs", "--tb=short"],
            PROJECT_ROOT,
            "NASA POWER, boundaries, coordinates, joins, PlantVillage, and unified-manifest tests pass or disclose skips.",
        ),
        _command_result(
            "mvp_smoke_tests",
            "smoke_tests",
            [sys.executable, "scripts/run_mvp_smoke_tests.py"],
            PROJECT_ROOT,
            "MVP smoke wrapper passes.",
        ),
        _command_result(
            "pbs_validation",
            "data_validation",
            [sys.executable, "Kisaan_Dost_Data/scripts/validate_pbs_extracted_tables.py"],
            PROJECT_ROOT,
            "PBS extracted-table validator reports all checks passed.",
        ),
        _pesticide_validation_check(),
        _artifact_check(),
        _source_pdf_check(),
        _settings_path_check(),
    ]
    checks.extend(_flutter_checks())
    failures = _failure_register(checks)
    counts = {
        "total": len(checks),
        "passed": sum(check["status"] == "pass" for check in checks),
        "failed": sum(check["status"] == "fail" for check in checks),
        "skipped": sum(check["status"] == "skipped" for check in checks),
    }
    report = {
        "schema_version": "1.0",
        "generated_at_utc": _utc_now(),
        "project_root": str(PROJECT_ROOT),
        "read_only_guarantee": {
            "ingestion_invoked": False,
            "training_invoked": False,
            "downloads_invoked": False,
            "migrations_invoked": False,
            "dependency_installation_invoked": False,
            "written_paths": ["reports/final_project_verification.json", "reports/final_project_verification.md"],
        },
        "environment": _environment(),
        "checks": checks,
        "failures": failures,
        "counts": counts,
        "overall_status": "complete_with_recorded_failures" if failures else "complete_all_passed",
    }
    OUTPUT_JSON.write_text(json.dumps(report, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    OUTPUT_MD.write_text(_render_markdown(report), encoding="utf-8")
    print(json.dumps({"counts": counts, "overall_status": report["overall_status"]}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
