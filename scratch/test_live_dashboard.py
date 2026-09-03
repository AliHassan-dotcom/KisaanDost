import asyncio
import json
from app.backend.services.risk_service import get_risk_service

def test_risk_service():
    svc = get_risk_service()
    assessment = svc.get_current_risk_assessment("Multan", "wheat")
    print("Risk Assessment for Multan (Wheat):")
    print(json.dumps(assessment, indent=2))
    assert assessment["risk_percent"] > 0
    assert len(assessment["hotspots"]) >= 3
    print("\nSUCCESS: Risk Service computed live telemetry from CSV!")

if __name__ == "__main__":
    test_risk_service()
