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


def test_get_dataset_report_success_and_csv(client, auth_token, test_db):
    headers = {"Authorization": f"Bearer {auth_token}"}
    from tests.helpers import CLEAN_CSV, csv_file, not_null_rule

    ds = client.post(
        "/api/datasets/upload",
        files=csv_file(CLEAN_CSV, "report_test.csv"),
        headers=headers,
    ).json()

    client.post("/api/rules", json=not_null_rule("name", "HIGH"), headers=headers)
    client.post(f"/api/checks/run/{ds['id']}", headers=headers)

    # Test JSON
    resp = client.get(f"/api/reports/{ds['id']}", headers=headers)
    assert resp.status_code == 200
    assert "score" in resp.json()

    # Test Unauthorized
    user2 = client.post(
        "/api/auth/register",
        json={
            "email": "report_viewer@test.com",
            "password": "Password123",
            "full_name": "Viewer",
        },
    ).json()
    headers2 = {"Authorization": f"Bearer {user2['access_token']}"}
    resp_unauth = client.get(f"/api/reports/{ds['id']}", headers=headers2)
    assert resp_unauth.status_code == 403

    # Test CSV format
    resp_csv = client.get(f"/api/reports/{ds['id']}?format=csv", headers=headers)
    assert resp_csv.status_code == 200
    assert "text/csv" in resp_csv.headers["content-type"]
    assert "Executive Summary" in resp_csv.text


def test_get_dataset_report_not_found_report(client, auth_token):
    headers = {"Authorization": f"Bearer {auth_token}"}
    from tests.helpers import CLEAN_CSV, csv_file

    ds = client.post(
        "/api/datasets/upload",
        files=csv_file(CLEAN_CSV, "no_report_test.csv"),
        headers=headers,
    ).json()
    resp = client.get(f"/api/reports/{ds['id']}", headers=headers)
    assert resp.status_code == 404
    assert "Report not found for dataset" in resp.text
