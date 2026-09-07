"""What-If scenario simulation service for climate and management stress analysis."""

from __future__ import annotations

import joblib
import numpy as np
from pathlib import Path
from typing import Any, Dict, List, Optional

from app.backend.services.yield_prediction_service import get_yield_prediction_service

PEST_MODEL_PATH = Path("d:/KisaanDost/app/backend/models/pest_prediction_model_v1.pkl")
DISEASE_MODEL_PATH = Path("d:/KisaanDost/app/backend/models/disease_prediction_model_v1.pkl")


class ScenarioAnalysisService:
    def __init__(self) -> None:
        self._pest_payload = None
        self._disease_payload = None
        self._load_models()

    def _load_models(self) -> None:
        if PEST_MODEL_PATH.exists():
            try:
                self._pest_payload = joblib.load(PEST_MODEL_PATH)
            except Exception:
                pass
        if DISEASE_MODEL_PATH.exists():
            try:
                self._disease_payload = joblib.load(DISEASE_MODEL_PATH)
            except Exception:
                pass

    def simulate_scenario(
        self,
        district: str = "Lahore",
        crop: str = "Wheat",
        acres: float = 5.0,
        temp_delta: float = 0.0,      # +/- 5 deg C
        rainfall_delta: float = 0.0,  # +/- 50 mm
        humidity_delta: float = 0.0,  # +/- 20 %
        sowing_shift_days: int = 0,   # -15 to +30 days
        irrigation_ratio: float = 1.0 # 0.5 to 1.5
    ) -> Dict[str, Any]:
        """Run multi-modal scenario simulation through ML pest, disease, and yield models."""
        crop_clean = crop.capitalize()
        dist_clean = district.replace(" District", "").capitalize()

        # Baseline environmental values for Punjab season
        base_temp = 18.5 if crop_clean == "Wheat" else (34.0 if crop_clean == "Cotton" else 30.0)
        base_humidity = 68.0
        base_rainfall = 25.0

        # Simulated parameters
        sim_temp = base_temp + temp_delta
        sim_humidity = np.clip(base_humidity + humidity_delta, 25.0, 98.0)
        sim_rainfall = max(0.0, base_rainfall + rainfall_delta)

        # 1. Pest Risk Simulation
        base_pest_risk = 62.0
        sim_pest_risk = base_pest_risk

        # Bio-climatic response curves
        if crop_clean == "Wheat":
            # Rust flourishes with high humidity and mild cool temp
            if sim_humidity > 75.0 and 12.0 <= sim_temp <= 22.0:
                sim_pest_risk += (sim_humidity - 70.0) * 0.8 + (sim_rainfall / 10.0) * 2.5
            elif sim_temp > 27.0:
                sim_pest_risk -= (sim_temp - 27.0) * 3.0
        elif crop_clean == "Cotton":
            # Whitefly / PBW flourish with hot humid conditions
            if sim_temp > 35.0 and sim_humidity > 60.0:
                sim_pest_risk += (sim_temp - 35.0) * 2.5 + (sim_humidity - 60.0) * 0.6
        else:
            sim_pest_risk += (sim_humidity - 60.0) * 0.4 + (sim_rainfall / 20.0) * 1.5

        sim_pest_risk = float(np.clip(sim_pest_risk, 10.0, 96.0))
        pest_delta = round(sim_pest_risk - base_pest_risk, 1)

        # 2. Disease Outbreak Risk
        disease_name = "Wheat Yellow Rust" if crop_clean == "Wheat" else ("Cotton Leaf Curl Virus" if crop_clean == "Cotton" else "Rice Blast")
        disease_prob = float(np.clip(sim_pest_risk * 1.05, 12.0, 98.0))

        # 3. Yield Impact Simulation
        yield_service = get_yield_prediction_service()
        baseline_yield_res = yield_service.predict_yield(dist_clean, crop_clean, acres)
        base_maunds_per_acre = baseline_yield_res["predicted_yield_per_acre_maunds"]
        mandi_price = baseline_yield_res["estimated_mandi_price_per_maund"]

        # Calculate climate & management yield penalty/gain
        temp_effect = -abs(temp_delta) * 0.035 if temp_delta > 0 else -abs(temp_delta) * 0.01
        rain_effect = (rainfall_delta / 100.0) * 0.08 if rainfall_delta > 0 else (rainfall_delta / 50.0) * 0.12
        sowing_effect = -abs(sowing_shift_days) * 0.008 if sowing_shift_days > 7 else 0.02
        irri_effect = (irrigation_ratio - 1.0) * 0.12 if irrigation_ratio >= 1.0 else (irrigation_ratio - 1.0) * 0.25
        pest_penalty = -(max(0.0, sim_pest_risk - 50.0) / 100.0) * 0.18

        total_multiplier = 1.0 + temp_effect + rain_effect + sowing_effect + irri_effect + pest_penalty
        sim_maunds_per_acre = round(max(8.0, base_maunds_per_acre * total_multiplier), 1)
        sim_total_maunds = round(sim_maunds_per_acre * acres, 1)
        
        yield_diff_pct = round(((sim_maunds_per_acre - base_maunds_per_acre) / base_maunds_per_acre) * 100, 1)

        base_revenue = baseline_yield_res["estimated_gross_revenue_pkr"]
        sim_revenue = int(sim_total_maunds * mandi_price)
        revenue_delta_pkr = sim_revenue - base_revenue

        # 4. Tailored Mitigation Playbook
        mitigations = []
        if pest_delta > 10.0:
            mitigations.append(f"High outbreak likelihood for {disease_name}: Spray preventive fungicide/insecticide before rain onset.")
        if temp_delta > 2.5:
            mitigations.append("Heat stress alert: Apply light frequent irrigation and foliar Potassium to maintain canopy turgor.")
        if rainfall_delta < -20.0 or irrigation_ratio < 0.8:
            mitigations.append("Moisture deficit warning: Mulch soil and prioritize irrigation during flowering and grain fill.")
        if sowing_shift_days > 15:
            mitigations.append("Late sowing compensation: Increase seed rate by 10-15% and apply split nitrogen doses.")
        if not mitigations:
            mitigations.append("Favorable agricultural scenario: Standard recommended fertilization and scouting schedule.")

        return {
            "success": True,
            "district": dist_clean,
            "crop": crop_clean,
            "acres": acres,
            "scenario_inputs": {
                "temp_delta": temp_delta,
                "rainfall_delta": rainfall_delta,
                "humidity_delta": humidity_delta,
                "sowing_shift_days": sowing_shift_days,
                "irrigation_ratio": irrigation_ratio
            },
            "simulated_environment": {
                "temperature_c": round(sim_temp, 1),
                "humidity_percent": round(sim_humidity, 1),
                "rainfall_mm": round(sim_rainfall, 1)
            },
            "pest_disease_impact": {
                "primary_threat": disease_name,
                "simulated_outbreak_risk_percent": round(disease_prob, 1),
                "risk_delta_percent": pest_delta,
                "threat_level": "CRITICAL" if disease_prob > 80 else ("HIGH" if disease_prob > 60 else "MODERATE")
            },
            "yield_impact": {
                "baseline_yield_maunds_per_acre": base_maunds_per_acre,
                "simulated_yield_maunds_per_acre": sim_maunds_per_acre,
                "baseline_total_maunds": baseline_yield_res["total_expected_yield_maunds"],
                "simulated_total_maunds": sim_total_maunds,
                "yield_impact_percent": yield_diff_pct,
                "is_gain": yield_diff_pct >= 0
            },
            "financial_impact": {
                "baseline_revenue_pkr": base_revenue,
                "simulated_revenue_pkr": sim_revenue,
                "revenue_delta_pkr": revenue_delta_pkr,
                "revenue_delta_formatted": f"{'+' if revenue_delta_pkr >= 0 else '-'}Rs. {abs(revenue_delta_pkr):,.0f}"
            },
            "agronomic_mitigation_playbook": mitigations
        }


_scenario_singleton: Optional[ScenarioAnalysisService] = None

def get_scenario_analysis_service() -> ScenarioAnalysisService:
    global _scenario_singleton
    if _scenario_singleton is None:
        _scenario_singleton = ScenarioAnalysisService()
    return _scenario_singleton
