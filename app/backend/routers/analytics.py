"""Analytics API router for Predictive Yield Modeling and What-If Scenario Analysis."""

from __future__ import annotations

from typing import Optional
from fastapi import APIRouter, Depends, Query
from pydantic import BaseModel

from app.backend.services.yield_prediction_service import YieldPredictionService, get_yield_prediction_service
from app.backend.services.scenario_analysis_service import ScenarioAnalysisService, get_scenario_analysis_service
from app.security.auth import get_current_user

router = APIRouter(prefix="/analytics", tags=["analytics"])


class YieldPredictionRequest(BaseModel):
    district: str = "Lahore"
    crop: str = "Wheat"
    acres: float = 5.0
    soil_type: Optional[str] = "Loam"
    irrigation_type: Optional[str] = "Canal + Tubewell"
    target_yield_maunds: Optional[float] = None


class ScenarioAnalysisRequest(BaseModel):
    district: str = "Lahore"
    crop: str = "Wheat"
    acres: float = 5.0
    temp_delta: float = 0.0
    rainfall_delta: float = 0.0
    humidity_delta: float = 0.0
    sowing_shift_days: int = 0
    irrigation_ratio: float = 1.0


@router.post("/yield-prediction")
async def predict_yield_post(
    payload: YieldPredictionRequest,
    current_user: dict = Depends(get_current_user),
    service: YieldPredictionService = Depends(get_yield_prediction_service),
):
    """Run machine learning yield forecast for specified district, crop, and farm parameters."""
    return service.predict_yield(
        district=payload.district,
        crop=payload.crop,
        acres=payload.acres,
        soil_type=payload.soil_type,
        irrigation_type=payload.irrigation_type,
        target_yield_maunds=payload.target_yield_maunds,
    )


@router.get("/yield-prediction")
async def predict_yield_get(
    district: str = Query("Lahore", description="Punjab district name"),
    crop: str = Query("Wheat", description="Crop name (Wheat, Cotton, Rice, Sugarcane, Maize, Potato)"),
    acres: float = Query(5.0, ge=0.5, le=500.0),
    soil_type: Optional[str] = Query(None),
    irrigation_type: Optional[str] = Query(None),
    current_user: dict = Depends(get_current_user),
    service: YieldPredictionService = Depends(get_yield_prediction_service),
):
    """Retrieve yield forecast via GET query parameters."""
    return service.predict_yield(
        district=district,
        crop=crop,
        acres=acres,
        soil_type=soil_type,
        irrigation_type=irrigation_type,
    )


@router.post("/what-if-scenario")
async def simulate_scenario_post(
    payload: ScenarioAnalysisRequest,
    current_user: dict = Depends(get_current_user),
    service: ScenarioAnalysisService = Depends(get_scenario_analysis_service),
):
    """Simulate climate and management variations across pest risk, disease, and yield models."""
    return service.simulate_scenario(
        district=payload.district,
        crop=payload.crop,
        acres=payload.acres,
        temp_delta=payload.temp_delta,
        rainfall_delta=payload.rainfall_delta,
        humidity_delta=payload.humidity_delta,
        sowing_shift_days=payload.sowing_shift_days,
        irrigation_ratio=payload.irrigation_ratio,
    )


@router.get("/what-if-scenario")
async def simulate_scenario_get(
    district: str = Query("Lahore"),
    crop: str = Query("Wheat"),
    acres: float = Query(5.0),
    temp_delta: float = Query(0.0),
    rainfall_delta: float = Query(0.0),
    humidity_delta: float = Query(0.0),
    sowing_shift_days: int = Query(0),
    irrigation_ratio: float = Query(1.0),
    current_user: dict = Depends(get_current_user),
    service: ScenarioAnalysisService = Depends(get_scenario_analysis_service),
):
    """Simulate scenario via GET query parameters."""
    return service.simulate_scenario(
        district=district,
        crop=crop,
        acres=acres,
        temp_delta=temp_delta,
        rainfall_delta=rainfall_delta,
        humidity_delta=humidity_delta,
        sowing_shift_days=sowing_shift_days,
        irrigation_ratio=irrigation_ratio,
    )
