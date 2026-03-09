from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

def test_get_dataset_report_not_found():
    response = client.get("/api/reports/99999")
    assert response.status_code == 404

def test_get_quality_trends_empty():
    response = client.get("/api/reports/trends?days=30&interval=day")
    assert response.status_code == 200
    data = response.json()
    assert "trend_data" in data
    assert data["trend_data"] == []
    
    # Check that invalid interval fails
    response_invalid = client.get("/api/reports/trends?interval=yearly")
    assert response_invalid.status_code == 400
