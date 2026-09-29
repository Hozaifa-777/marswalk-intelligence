from fastapi.testclient import TestClient
from app.main import app
from app.core.science.consumables import calculate_eva_consumables
from app.schemas.mission import ConsumablesRequest

client = TestClient(app)


def test_consumables_without_optional_fields():
    # Test request missing payload_kg and slope_percent
    req = ConsumablesRequest(distance_km=2.0, average_raw_terrain_cost=1.0)
    res = calculate_eva_consumables(req)

    assert res.estimated_duration_hours > 0
    assert res.payload_penalty_kcal_hr == 0.0
    assert res.slope_penalty_kcal_hr == 0.0


def test_consumables_with_payload_and_slope():
    req = ConsumablesRequest(
        distance_km=2.0,
        average_raw_terrain_cost=1.0,
        average_slope_percent=5.0,
        payload_kg=15.0,
    )
    res = calculate_eva_consumables(req)

    assert res.payload_penalty_kcal_hr > 0
    assert res.slope_penalty_kcal_hr > 0
    assert res.average_metabolic_rate_kcal_hr > 200.0


def test_api_endpoint_consumables():
    payload = {
        "distance_km": 3.0,
        "average_raw_terrain_cost": 1.2,
        "payload_kg": 10.0,
    }
    response = client.post("/api/v1/mission/consumables", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert "estimated_oxygen_liters" in data
    assert data["assumptions"]["payload_mass_kg"] == 10.0
