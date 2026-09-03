from fastapi.testclient import TestClient
from app.backend.main import app

client = TestClient(app)

def test_warning_endpoint():
    res = client.get("/api/v1/pest-model/warning?district=Lahore&crop=Wheat")
    assert res.status_code == 200
    data = res.json()
    assert data["status"] == "success"
    assert data["crop"] == "Wheat"
    assert "Yellow Rust" in data["pest"]
    assert data["warning_level"] == "HIGH RISK"

def test_analyze_endpoint():
    payload = {
        "crop_type": "Wheat",
        "district": "Lahore",
        "month": 2,
        "temp_avg": 16.5,
        "humidity_avg": 78.0,
        "rainfall_mm": 30.0,
        "growth_stage": "tillering"
    }
    res = client.post("/api/v1/pest-model/analyze", json=payload)
    assert res.status_code == 200
    data = res.json()
    assert data["status"] == "success"
    assert data["crop"] == "Wheat"
    assert data["outbreak_probability"] > 50.0
    assert "recommendation" in data
    assert "Tilt" in data["recommendation"]["brand"]

def test_recommend_endpoint():
    res = client.get("/api/v1/pest-model/recommend?pest=yellow_rust&crop=wheat&acres=5")
    assert res.status_code == 200
    data = res.json()
    assert data["status"] == "success"
    assert data["acres"] == 5.0
    assert "Tilt" in data["pesticide_brand"]
    assert "Rs." in data["estimated_cost_pkr"]

def test_ipm_endpoint():
    res = client.get("/api/v1/pest-model/ipm/advice?crop=Cotton")
    assert res.status_code == 200
    data = res.json()
    assert data["status"] == "success"
    assert data["crop"] == "Cotton"
    assert "Trichogramma" in data["biological_control"] or "pheromone" in data["biological_control"]
