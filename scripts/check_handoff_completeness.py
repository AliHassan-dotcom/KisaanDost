"""Check handoff completeness across Kisaan Dost repository.

This script performs a read-only audit of all freeze/handoff reports,
manifests, live components, data artifacts, model assets, mobile artifacts,
and disclosed blockers. It does not modify any source code or data.
"""

from __future__ import annotations

import csv
import json
import os
import sys
from pathlib import Path
from typing import Any

PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))
REPORTS_DIR = PROJECT_ROOT / "reports"
DATA_ROOT = PROJECT_ROOT / "Kisaan_Dost_Data"
PROCESSED_DIR = PROJECT_ROOT / "data" / "processed"
MOBILE_ROOT = PROJECT_ROOT / "mobile_app"

REQUIRED_REPORTS = [
    "final_project_verification.md",
    "final_project_verification.json",
    "project_handoff_manifest.md",
    "project_handoff_manifest.json",
    "test_build_matrix.md",
    "data_model_api_lineage.md",
    "mobile_mvp_demo_guide.md",
    "security_status_and_production_backlog.md",
    "antigravity_continuation_plan.md",
    "pesticide_report_source_reproducibility_status.md",
]

REQUIRED_DATA_FILES = [
    PROCESSED_DIR / "pesticide_report_facts.csv",
    PROCESSED_DIR / "pesticide_report_chunks.jsonl",
    PROCESSED_DIR / "pesticide_report_review_queue.csv",
    PROCESSED_DIR / "pesticide_report_ingestion_meta.json",
    DATA_ROOT / "processed" / "district_coordinates.csv",
    DATA_ROOT / "processed" / "weather_join_keys.csv",
    DATA_ROOT / "processed" / "district_monthly_weather.csv",
    DATA_ROOT / "raw" / "arcgis" / "punjab_district_boundaries.geojson",
    DATA_ROOT / "data" / "processed" / "plantvillage_class_mapping.csv",
    DATA_ROOT / "data" / "processed" / "plantvillage_manifest_clean.csv",
    DATA_ROOT / "data" / "processed" / "unified_crop_disease_manifest_clean.csv",
    DATA_ROOT / "processed" / "pbs_farm_structure.csv",
    DATA_ROOT / "processed" / "pbs_land_tenure.csv",
    DATA_ROOT / "processed" / "pbs_irrigation.csv",
    DATA_ROOT / "processed" / "pbs_crops.csv",
    DATA_ROOT / "processed" / "pbs_machinery.csv",
    DATA_ROOT / "processed" / "pbs_livestock.csv",
    DATA_ROOT / "processed" / "pbs_modern_farming.csv",
    DATA_ROOT / "processed" / "pbs_credit.csv",
    DATA_ROOT / "processed" / "kisaan_dost_context_only.csv",
]


def check_reports() -> dict[str, Any]:
    missing = []
    present = []
    for report_name in REQUIRED_REPORTS:
        report_path = REPORTS_DIR / report_name
        if report_path.is_file() and report_path.stat().st_size > 0:
            present.append(report_name)
        else:
            missing.append(report_name)
    return {
        "total_required": len(REQUIRED_REPORTS),
        "present_count": len(present),
        "present": present,
        "missing_count": len(missing),
        "missing": missing,
        "status": "complete" if not missing else "incomplete",
    }


def check_scripts() -> dict[str, Any]:
    run_verif = (PROJECT_ROOT / "scripts" / "run_final_verification.py").is_file()
    check_hand = (PROJECT_ROOT / "scripts" / "check_handoff_completeness.py").is_file()
    return {
        "run_final_verification_exists": run_verif,
        "check_handoff_completeness_exists": check_hand,
        "status": "complete" if run_verif and check_hand else "incomplete",
    }


def check_data_artifacts() -> dict[str, Any]:
    missing = []
    present = []
    for path in REQUIRED_DATA_FILES:
        rel = str(path.relative_to(PROJECT_ROOT)).replace("\\", "/")
        if path.is_file():
            present.append({"path": rel, "size_bytes": path.stat().st_size})
        else:
            missing.append(rel)
    return {
        "total_required": len(REQUIRED_DATA_FILES),
        "present_count": len(present),
        "present": present,
        "missing_count": len(missing),
        "missing": missing,
        "status": "complete" if not missing else "incomplete",
    }


def check_models_and_apk() -> dict[str, Any]:
    v2_model = DATA_ROOT / "models" / "best_plantvillage_model_v2.pt"
    baseline_model = DATA_ROOT / "models" / "best_plantvillage_model.pt"
    apk_path = MOBILE_ROOT / "build" / "app" / "outputs" / "flutter-apk" / "app-debug.apk"

    return {
        "v2_model": {
            "path": str(v2_model.relative_to(PROJECT_ROOT)).replace("\\", "/"),
            "exists": v2_model.is_file(),
            "size_bytes": v2_model.stat().st_size if v2_model.is_file() else 0,
        },
        "baseline_model": {
            "path": str(baseline_model.relative_to(PROJECT_ROOT)).replace("\\", "/"),
            "exists": baseline_model.is_file(),
            "size_bytes": baseline_model.stat().st_size if baseline_model.is_file() else 0,
        },
        "preserved_debug_apk": {
            "path": str(apk_path.relative_to(PROJECT_ROOT)).replace("\\", "/"),
            "exists": apk_path.is_file(),
            "size_bytes": apk_path.stat().st_size if apk_path.is_file() else 0,
        },
    }


def check_disclosed_blockers() -> dict[str, Any]:
    # Blocker 1: Configured model path resolution
    from app.config import settings

    configured_model_path = settings.model_full_path()
    actual_model_path = DATA_ROOT / "models" / "best_plantvillage_model_v2.pt"
    is_model_resolved = configured_model_path.is_file()

    # Blocker 2: Pesticide source PDF portability
    nested_pdf_path = DATA_ROOT / "Annual Report 2024-25_copy.pdf"
    external_sibling_pdf_path = PROJECT_ROOT.parent / "Kisaan_Dost_Data" / "Annual Report 2024-25_copy.pdf"

    return {
        "blocker_1_model_path_resolution": {
            "configured_path": str(configured_model_path),
            "configured_path_exists": is_model_resolved,
            "actual_path": str(actual_model_path.relative_to(PROJECT_ROOT)).replace("\\", "/"),
            "actual_path_exists": actual_model_path.is_file(),
            "status": "resolved" if is_model_resolved else "active_disclosed_blocker",
            "description": "app/config/settings.py resolves to verified Kisaan_Dost_Data/models/best_plantvillage_model_v2.pt checkpoint." if is_model_resolved else "app/config/settings.py resolves to non-existent model path.",
        },
        "blocker_2_pesticide_pdf_portability": {
            "nested_repo_path": str(nested_pdf_path.relative_to(PROJECT_ROOT)).replace("\\", "/"),
            "nested_repo_path_exists": nested_pdf_path.is_file(),
            "external_sibling_path": str(external_sibling_pdf_path),
            "external_sibling_path_exists": external_sibling_pdf_path.is_file(),
            "external_size_bytes": external_sibling_pdf_path.stat().st_size if external_sibling_pdf_path.is_file() else 0,
            "status": "resolved" if nested_pdf_path.is_file() else "active_disclosed_blocker",
            "description": "Official annual report PDF restored and verified at Kisaan_Dost_Data/Annual Report 2024-25_copy.pdf." if nested_pdf_path.is_file() else "Official annual report PDF absent from nested in-repo path; present at external sibling directory on local workstation.",
        },
    }


def check_verification_evidence() -> dict[str, Any]:
    verif_json = REPORTS_DIR / "final_project_verification.json"
    if not verif_json.is_file():
        return {"status": "missing_verification_json"}
    data = json.loads(verif_json.read_text(encoding="utf-8"))
    counts = data.get("counts", {})
    failures = data.get("failures", [])
    checks = {c["id"]: c["status"] for c in data.get("checks", [])}
    return {
        "counts": counts,
        "failures": failures,
        "checks_summary": checks,
        "overall_status": data.get("overall_status"),
    }


def run_check() -> dict[str, Any]:
    reports_status = check_reports()
    scripts_status = check_scripts()
    data_status = check_data_artifacts()
    models_apk_status = check_models_and_apk()
    blockers_status = check_disclosed_blockers()
    verification_evidence = check_verification_evidence()

    is_complete = (
        reports_status["status"] == "complete"
        and scripts_status["status"] == "complete"
        and data_status["status"] == "complete"
        and models_apk_status["v2_model"]["exists"]
        and (models_apk_status["preserved_debug_apk"]["exists"] or (MOBILE_ROOT / "pubspec.yaml").is_file())
    )

    return {
        "schema_version": "1.0",
        "project_root": str(PROJECT_ROOT),
        "completeness_status": "COMPLETE" if is_complete else "INCOMPLETE",
        "reports": reports_status,
        "scripts": scripts_status,
        "data_artifacts": data_status,
        "models_and_apk": models_apk_status,
        "disclosed_blockers": blockers_status,
        "prior_verification_evidence": verification_evidence,
        "safe_for_feature_continuation": is_complete,
    }


def main() -> int:
    result = run_check()
    print(json.dumps(result, indent=2))
    return 0 if result["completeness_status"] == "COMPLETE" else 1


if __name__ == "__main__":
    sys.exit(main())
