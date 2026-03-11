"""Tests for the quality checks endpoint and engine."""

import pytest
from app.models.check_result import CheckResult, QualityScore
from tests.helpers import (
    CLEAN_CSV,
    DIRTY_CSV,
    csv_file,
    not_null_rule,
    data_type_rule,
    range_rule,
    unique_rule,
    regex_rule
)


class TestRunChecks:
    def test_run_checks_unauthorized(self, client):
        resp = client.post("/api/checks/run/999")
        assert resp.status_code == 403

    def test_run_checks_dataset_not_found(self, client, auth_token):
        headers = {"Authorization": f"Bearer {auth_token}"}
        resp = client.post("/api/checks/run/9999", headers=headers)
        assert resp.status_code == 404

    def test_run_checks_success_clean_data(self, client, auth_token, test_db):
        headers = {"Authorization": f"Bearer {auth_token}"}
        
        # 1. Upload dataset
        ds = client.post(
            "/api/datasets/upload", 
            files=csv_file(CLEAN_CSV, "check_clean.csv"), 
            headers=headers
        ).json()
        assert "id" in ds, ds
        ds_id = ds["id"]
        
        # 2. Add rules of all 5 types
        rules = [
            not_null_rule("name", "HIGH"),
            data_type_rule("age", "int", "MEDIUM"),
            range_rule("score", 0, 100, "HIGH"),
            unique_rule("id", "HIGH"),
            regex_rule("email", r"^[\w\.-]+@[\w\.-]+\.\w+$", "MEDIUM")
        ]
        
        for rule in rules:
            r = client.post("/api/rules", json=rule, headers=headers)
            assert r.status_code == 201
            
        # 3. Run checks
        resp = client.post(f"/api/checks/run/{ds_id}", headers=headers)
        assert resp.status_code == 200
        data = resp.json()
        
        assert data["status"] == "VALIDATED"
        assert "score" in data
        assert data["score"] == 100.0  # Clean data should pass all
        
        # 4. Verify DB persistence
        db_results = test_db.query(CheckResult).filter(CheckResult.dataset_id == ds_id).all()
        assert len(db_results) == 5
        assert all(r.passed for r in db_results)
        
        db_score = test_db.query(QualityScore).filter(QualityScore.dataset_id == ds_id).first()
        assert db_score is not None
        assert db_score.score == 100.0
        assert db_score.passed_rules == 5
        assert db_score.failed_rules == 0
        assert db_score.total_rules == 5

    def test_run_checks_dirty_data(self, client, auth_token, test_db):
        headers = {"Authorization": f"Bearer {auth_token}"}
        ds = client.post(
            "/api/datasets/upload", 
            files=csv_file(DIRTY_CSV, "check_dirty.csv"), 
            headers=headers
        ).json()
        assert "id" in ds, ds
        ds_id = ds["id"]
        
        # Add rules that will fail
        # Dirty CSV has missing 'name' on row 3
        # Has duplicate 'Eve' (id 5, index 4 and 5)
        # Has invalid 'age' on row 4
        client.post("/api/rules", json=not_null_rule("name", "HIGH"), headers=headers)
        client.post("/api/rules", json=data_type_rule("age", "int", "HIGH"), headers=headers)
        client.post("/api/rules", json=unique_rule("id", "HIGH"), headers=headers)
        
        resp = client.post(f"/api/checks/run/{ds_id}", headers=headers)
        assert resp.status_code == 200
        data = resp.json()
        
        assert data["score"] < 100.0
        assert data["results_summary"]["failed_rules"] > 0
        assert data["results_summary"]["passed_rules"] < 3
        
        # Verify persistence for failed results
        db_results = test_db.query(CheckResult).filter(CheckResult.dataset_id == ds_id).all()
        # Should have some failures
        assert any(not r.passed for r in db_results)
        
    def test_run_checks_no_active_rules(self, client, auth_token):
        """Test dataset with no rules."""
        headers = {"Authorization": f"Bearer {auth_token}"}
        ds = client.post(
            "/api/datasets/upload", 
            files=csv_file(CLEAN_CSV, "check_no_rules.csv"), 
            headers=headers
        ).json()
        
        # Run checks directly with no rules matching
        # Wait, if there are rules created globally from other tests, they might match if field_name is the same.
        # But this dataset has fields 'id', 'name', 'email', 'age', 'score' which match globally.
        # To test NO RULES, we should upload a csv with completely different column names that NO global rule matches.
        WEIRD_CSV = "col1,col2,col3\n1,2,3"
        ds_weird = client.post(
            "/api/datasets/upload", 
            files=csv_file(WEIRD_CSV, "weird.csv"), 
            headers=headers
        ).json()
        
        resp = client.post(f"/api/checks/run/{ds_weird['id']}", headers=headers)
        assert resp.status_code == 400
        assert "No active rules applicable" in resp.json()["detail"]


class TestGetCheckResults:
    def test_get_results_success(self, client, auth_token):
        headers = {"Authorization": f"Bearer {auth_token}"}
        
        ds = client.post(
            "/api/datasets/upload", 
            files=csv_file(CLEAN_CSV, "results_test.csv"), 
            headers=headers
        ).json()
        
        client.post("/api/rules", json=not_null_rule("name", "HIGH"), headers=headers)
        client.post(f"/api/checks/run/{ds['id']}", headers=headers)
        
        resp = client.get(f"/api/checks/results/{ds['id']}", headers=headers)
        assert resp.status_code == 200
        data = resp.json()
        assert isinstance(data, list)
        assert len(data) >= 1
        assert "rule_id" in data[0]
        assert "passed" in data[0]

    def test_get_results_unauthorized_dataset(self, client, auth_token, sample_user):
        """User cannot view results belonging to someone else."""
        headers = {"Authorization": f"Bearer {auth_token}"}
        
        ds = client.post(
            "/api/datasets/upload", 
            files=csv_file(CLEAN_CSV, "authz_test.csv"), 
            headers=headers
        ).json()
        
        # Register second user
        user2 = client.post("/api/auth/register", json={
            "email": "user2@test.com", "password": "Password123", "full_name": "User Two"
        }).json()
        headers2 = {"Authorization": f"Bearer {user2['access_token']}"}
        
        resp = client.get(f"/api/checks/results/{ds['id']}", headers=headers2)
        assert resp.status_code == 403
