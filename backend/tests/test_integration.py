"""End-to-End integration tests for sample datasets verifying specific quality scores."""

import pytest
from tests.helpers import (
    CLEAN_CSV,
    DIRTY_CSV,
    MIXED_CSV,
    csv_file,
    not_null_rule,
    data_type_rule,
    range_rule,
    unique_rule,
    regex_rule
)


def get_auth_headers(client, email="e2e_integration@test.com"):
    auth = client.post("/api/auth/register", json={
        "email": email, "password": "Password123", "full_name": "E2E Integration Tester"
    }).json()
    if "access_token" not in auth:
        auth = client.post("/api/auth/login", json={
            "email": email, "password": "Password123"
        }).json()
    return {"Authorization": f"Bearer {auth['access_token']}"}


class TestIntegrationSampleDatasets:
    """PR 5 Integration Test Requirements:
    - Test end-to-end: upload -> create rules -> run checks -> verify score
    - Verify clean_data.csv (~95 score, ideally 100)
    - Verify messy_data.csv (~40 score)
    - Verify mixed_data.csv (~70 score)
    """

    def setup_rules(self, client, headers, test_db):
        """Setup standard 5 rules with total weight 11."""
        from app.models.rule import ValidationRule
        test_db.query(ValidationRule).delete()
        test_db.commit()
        
        rules = [
            not_null_rule("name", "HIGH"),            # weight 3
            data_type_rule("age", "int", "HIGH"),     # weight 3
            regex_rule("email", r"^[\w\.-]+@[\w\.-]+\.\w+$", "MEDIUM"), # weight 2
            range_rule("score", 0, 100, "MEDIUM"),    # weight 2
            unique_rule("id", "LOW")                  # weight 1
        ]
        
        for rule in rules:
            resp = client.post("/api/rules", json=rule, headers=headers)
            assert resp.status_code == 201

    def test_clean_data_score(self, client, test_db):
        """Clean data should pass all rules (11/11 = 100%)."""
        headers = get_auth_headers(client, "clean@test.com")
        
        # Upload
        ds = client.post("/api/datasets/upload", files=csv_file(CLEAN_CSV, "clean_data.csv"), headers=headers).json()
        assert ds["status"] == "PENDING"
        
        # Rules
        self.setup_rules(client, headers, test_db)
        
        # Run Checks
        check = client.post(f"/api/checks/run/{ds['id']}", headers=headers)
        assert check.status_code == 200
        
        # Verify Report
        report = client.get(f"/api/reports/{ds['id']}", headers=headers).json()
        assert report["score"] == 100.0  # 100%

    def test_mixed_data_score(self, client, test_db):
        """Mixed data fails only 'name' NOT_NULL (weight 3).
        Passes 8/11 weights -> 72.7% (matches '~70 score')."""
        headers = get_auth_headers(client, "mixed@test.com")
        
        ds = client.post("/api/datasets/upload", files=csv_file(MIXED_CSV, "mixed_data.csv"), headers=headers).json()
        self.setup_rules(client, headers, test_db)
        
        client.post(f"/api/checks/run/{ds['id']}", headers=headers)
        
        report = client.get(f"/api/reports/{ds['id']}", headers=headers).json()
        assert 70.0 <= report["score"] <= 75.0  # ~ 72.73

    def test_messy_data_score(self, client, test_db):
        """Messy data fails 'name', 'age', and 'id'. 
        Passes 'email', 'score' (total weight 4).
        Passes 4/11 weights -> 36.36% (matches '~40 score')."""
        headers = get_auth_headers(client, "messy@test.com")
        
        ds = client.post("/api/datasets/upload", files=csv_file(DIRTY_CSV, "messy_data.csv"), headers=headers).json()
        self.setup_rules(client, headers, test_db)
        
        client.post(f"/api/checks/run/{ds['id']}", headers=headers)
        
        report = client.get(f"/api/reports/{ds['id']}", headers=headers).json()
        assert 35.0 <= report["score"] <= 45.0  # ~ 36.36
