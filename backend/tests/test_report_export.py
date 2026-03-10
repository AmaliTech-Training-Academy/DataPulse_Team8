"""Unit tests for the CSV/JSON Export endpoint."""
import pytest
from httpx import Response
from app.models.check_result import QualityScore, CheckResult
from tests.helpers import CLEAN_CSV, csv_file, not_null_rule


def get_auth_headers(client, email="export_tester@test.com"):
    auth = client.post("/api/auth/register", json={
        "email": email, "password": "Password123", "full_name": "Export Tester"
    }).json()
    if "access_token" not in auth:
        auth = client.post("/api/auth/login", json={
            "email": email, "password": "Password123"
        }).json()
    return {"Authorization": f"Bearer {auth['access_token']}"}


def setup_dataset_with_report(client, headers) -> dict:
    """Helper to upload a dataset and generate a report."""
    ds = client.post("/api/datasets/upload", files=csv_file(CLEAN_CSV, "export_ds.csv"), headers=headers).json()
    client.post("/api/rules", json=not_null_rule("name", "HIGH"), headers=headers)
    
    # generate report
    client.post(f"/api/checks/run/{ds['id']}", headers=headers)
    return ds


class TestReportExport:
    def test_export_json_default(self, client):
        """Test the native /export endpoint defaults to json natively."""
        headers = get_auth_headers(client, "export1@test.com")
        ds = setup_dataset_with_report(client, headers)
        
        # Test original endpoint
        resp = client.get(f"/api/reports/{ds['id']}?format=json", headers=headers)
        assert resp.status_code == 200
        assert "executive_summary" in resp.json()
        assert "results" in resp.json()
        
        # Test new /export alias endpoint
        export_resp = client.get(f"/api/reports/{ds['id']}/export?format=json", headers=headers)
        assert export_resp.status_code == 200
        assert "executive_summary" in export_resp.json()

    def test_export_csv_format(self, client):
        """Test the CSV export streaming representation."""
        headers = get_auth_headers(client, "export2@test.com")
        ds = setup_dataset_with_report(client, headers)
        
        resp = client.get(f"/api/reports/{ds['id']}/export?format=csv", headers=headers)
        
        # Validate the response header is Attachment CSV
        assert resp.status_code == 200
        assert "text/csv" in resp.headers.get("Content-Type", "").lower()
        assert f"attachment; filename=report_{ds['id']}.csv" in resp.headers.get("Content-Disposition", "")
        
        # Validate CSV content
        csv_text = resp.text
        assert "Executive Summary" in csv_text
        assert "Score" in csv_text
        assert "Total Rules" in csv_text
        assert "Detailed Findings" in csv_text
        assert "Passed" in csv_text
        
    def test_export_unauthorized(self, client):
        """Test that another user cannot export this report."""
        headers_creator = get_auth_headers(client, "export3_creator@test.com")
        ds = setup_dataset_with_report(client, headers_creator)
        
        headers_attacker = get_auth_headers(client, "export3_attacker@test.com")
        resp = client.get(f"/api/reports/{ds['id']}/export?format=csv", headers=headers_attacker)
        
        # Unauthorized access should trigger a 403
        assert resp.status_code == 403

    def test_export_not_found(self, client):
        """Test exporting a non-existent report."""
        headers = get_auth_headers(client, "export4@test.com")
        resp = client.get("/api/reports/99999/export", headers=headers)
        assert resp.status_code == 404
