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
        json={"storm_duration_hours": 6, "transfer_power_kw": 5},
    )
    assert response.status_code == 200

    body = response.json()
    assert "assessments" in body
    assert "transfers" in body
    assert "load_recommendations" in body
    assert "coverage_pct" in body


def test_storm_replan_api():
    response = client.post(
        "/api/storm/replan",
        json={"storm_duration_hours": 6, "transfer_power_kw": 5},
    )
    assert response.status_code == 200
    assert "transfers" in response.json()
