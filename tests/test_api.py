from fastapi.testclient import TestClient

from app.api.main import app

client = TestClient(app)


def test_health():
    response = client.get("/health")

    assert response.status_code == 200
    assert response.json()["status"] == "ok"


def test_storm_plan_api():
    response = client.post(
        "/api/storm/plan",
        json={
            "storm_duration_hours": 6,
            "transfer_power_kw": 5,
        },
    )

    assert response.status_code == 200

    body = response.json()

    assert "assessments" in body
    assert "grid_contributions" in body
    assert "grid_distributions" in body
    assert "load_recommendations" in body

    assert "total_energy_needed_kwh" in body
    assert "total_safe_surplus_kwh" in body
    assert "total_grid_energy_kwh" in body
    assert "total_distributed_energy_kwh" in body
    assert "unfulfilled_deficit_kwh" in body

    assert "coverage_pct" in body
    assert "is_ready" in body

    # Direct donor -> recipient transfers are no longer part
    # of the storm orchestration API.
    assert "transfers" not in body


def test_storm_replan_api():
    response = client.post(
        "/api/storm/replan",
        json={
            "storm_duration_hours": 6,
            "transfer_power_kw": 5,
        },
    )

    assert response.status_code == 200

    body = response.json()

    assert "assessments" in body
    assert "grid_contributions" in body
    assert "grid_distributions" in body
    assert "load_recommendations" in body

    assert "total_grid_energy_kwh" in body
    assert "total_distributed_energy_kwh" in body
    assert "unfulfilled_deficit_kwh" in body

    assert "coverage_pct" in body
    assert "is_ready" in body

    assert "transfers" not in body