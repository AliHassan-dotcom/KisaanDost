"""Risk engine — pure function, no I/O, no DB (architecture/01-system-architecture.md).

Contract (stable across phases — rules v1 → ML disease model v2):

    inputs:  ndvi_mean, ndvi_anomaly, ndwi_mean,
             forecast(rain_mm_7d, tmax, tmin), crop_type, season
    output:  {level: low|medium|high, reasons: [max 3, ranked, bilingual],
              action: irrigate|spray|wait|harvest|sell|consult_advisor}
"""
from dataclasses import dataclass
from typing import Literal

RiskLevel = Literal["low", "medium", "high"]
Action = Literal["irrigate", "spray", "wait", "harvest", "sell", "consult_advisor"]
ENGINE_VERSION = "rules-v1"


@dataclass(frozen=True)
class RiskInputs:
    ndvi_mean: float
    ndvi_anomaly: float
    ndwi_mean: float
    rain_mm_7d: float
    tmax: float
    tmin: float
    crop_type: str
    season: str


@dataclass(frozen=True)
class Reason:
    code: str
    text_en: str
    text_ur: str


@dataclass(frozen=True)
class RiskOutput:
    level: RiskLevel
    reasons: list[Reason]
    action: Action
    engine_version: str = ENGINE_VERSION


def score(inputs: RiskInputs) -> RiskOutput:
    """Rules v1 — explainable thresholds. Replace internals in Phase 2; never the output shape."""
    raise NotImplementedError
