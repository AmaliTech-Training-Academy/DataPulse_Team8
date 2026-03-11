from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_get_dataset_report_not_found(client, auth_token):
    headers = {"Authorization": f"Bearer {auth_token}"}
    response = client.get("/api/reports/99999", headers=headers)
    assert response.status_code == 404


def test_get_quality_trends_empty(client, auth_token):
    headers = {"Authorization": f"Bearer {auth_token}"}
    response = client.get("/api/reports/trends?days=30&interval=day", headers=headers)
    assert response.status_code == 200
    data = response.json()
    assert "trend_data" in data
    assert isinstance(data["trend_data"], list)
    assert isinstance(data["trend_data"], list)

    # Check that invalid interval fails
    response_invalid = client.get(
        "/api/reports/trends?interval=yearly", headers=headers
    )
    assert response_invalid.status_code == 400
