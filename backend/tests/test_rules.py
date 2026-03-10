import json
import pytest
import uuid
from fastapi.testclient import TestClient
from tests.helpers import not_null_rule, range_rule, unique_rule, regex_rule, data_type_rule

def helper_create_rule(client: TestClient, auth_token: str):
    response = client.post(
        "/api/rules",
        headers={"Authorization": f"Bearer {auth_token}"},
        json=not_null_rule("amount")
    )
    assert response.status_code == 201
    data = response.json()
    assert "id" in data
    assert data["created_by"] is not None
    return data["id"]

class TestCreateRule:
    """TC-R01 to TC-R07 — Rule Creation"""

    def test_create_not_null_rule(self, client, auth_token):
        """TC-R01 — Create a NOT_NULL rule returns 201 with correct fields."""
        headers = {"Authorization": f"Bearer {auth_token}"}
        resp = client.post("/api/rules", json=not_null_rule("email", "HIGH"), headers=headers)
        assert resp.status_code == 201
        data = resp.json()
        assert data["rule_type"] == "NOT_NULL"
        assert data["field_name"] == "email"

    def test_create_data_type_rule(self, client, auth_token):
        """TC-R02 — Create a DATA_TYPE rule with parameters stored correctly."""
        headers = {"Authorization": f"Bearer {auth_token}"}
        resp = client.post("/api/rules", json=data_type_rule("age", "int", "MEDIUM"), headers=headers)
        assert resp.status_code == 201
        data = resp.json()
        assert data["rule_type"] == "DATA_TYPE"
        params = json.loads(data["parameters"])
        assert params["expected_type"] == "int"

    def test_create_range_rule(self, client, auth_token):
        """TC-R03 — Create a RANGE rule with min/max parameters."""
        headers = {"Authorization": f"Bearer {auth_token}"}
        resp = client.post("/api/rules", json=range_rule("score", 0, 100, "MEDIUM"), headers=headers)
        assert resp.status_code == 201
        data = resp.json()
        assert data["rule_type"] == "RANGE"
        params = json.loads(data["parameters"])
        assert params["min"] == 0
        assert params["max"] == 100

    def test_create_unique_rule(self, client, auth_token):
        """TC-R04 — Create a UNIQUE rule returns 201."""
        headers = {"Authorization": f"Bearer {auth_token}"}
        resp = client.post("/api/rules", json=unique_rule("id", "HIGH"), headers=headers)
        assert resp.status_code == 201
        assert resp.json()["rule_type"] == "UNIQUE"

    def test_create_regex_rule(self, client, auth_token):
        """TC-R05 — Create a REGEX rule with pattern stored."""
        headers = {"Authorization": f"Bearer {auth_token}"}
        rule = regex_rule("email", r"^[\w.+-]+@[\w-]+\.\w+$", "LOW")
        resp = client.post("/api/rules", json=rule, headers=headers)
        assert resp.status_code == 201
        data = resp.json()
        assert data["rule_type"] == "REGEX"
        params = json.loads(data["parameters"])
        assert "pattern" in params

    def test_create_rule_invalid_type(self, client, auth_token):
        """TC-R06 — Invalid rule_type returns 400."""
        headers = {"Authorization": f"Bearer {auth_token}"}
        bad_rule = not_null_rule("name", "HIGH")
        bad_rule["rule_type"] = "DOES_NOT_EXIST"
        resp = client.post("/api/rules", json=bad_rule, headers=headers)
        assert resp.status_code == 400

    def test_create_rule_invalid_severity(self, client, auth_token):
        """TC-R07 — Invalid severity returns 400."""
        headers = {"Authorization": f"Bearer {auth_token}"}
        bad_rule = not_null_rule("name", "HIGH")
        bad_rule["severity"] = "CRITICAL"
        resp = client.post("/api/rules", json=bad_rule, headers=headers)
        assert resp.status_code == 400

    def test_create_rule_missing_required_fields(self, client, auth_token):
        """TC-R06 extended — Missing required fields returns 422."""
        headers = {"Authorization": f"Bearer {auth_token}"}
        # missing field_name, rule_type, etc.
        resp = client.post("/api/rules", json={"name": "incomplete", "dataset_type": "csv"}, headers=headers)
        assert resp.status_code == 422

    def test_create_rule_empty_field_name(self, client, auth_token):
        """TC-R06b — Empty field name returns 400."""
        headers = {"Authorization": f"Bearer {auth_token}"}
        rule = not_null_rule("", "HIGH")
        resp = client.post("/api/rules", json=rule, headers=headers)
        assert resp.status_code == 400

    def test_create_range_rule_min_greater_than_max(self, client, auth_token):
        """TC-R06e — RANGE rule with min >= max returns 400."""
        headers = {"Authorization": f"Bearer {auth_token}"}
        rule = range_rule("score", 100, 50, "MEDIUM")
        resp = client.post("/api/rules", json=rule, headers=headers)
        assert resp.status_code == 400

class TestListRules:
    """TC-R08, TC-R09 — Rule Listing"""

    def test_list_rules_returns_200(self, client, auth_token):
        """TC-R08 — GET /api/rules returns 200 with a list."""
        headers = {"Authorization": f"Bearer {auth_token}"}
        resp = client.get("/api/rules", headers=headers)
        assert resp.status_code == 200
        assert isinstance(resp.json(), list)

    def test_list_rules_contains_created_rule(self, client, auth_token):
        """TC-R08 extended — A newly created rule appears in the list."""
        headers = {"Authorization": f"Bearer {auth_token}"}
        rule = not_null_rule("list_check_field", "HIGH")
        rule["name"] = "unique_list_check_rule"
        client.post("/api/rules", json=rule, headers=headers)
        resp = client.get("/api/rules", headers=headers)
        names = [r["name"] for r in resp.json()]
        assert "unique_list_check_rule" in names

class TestUpdateRule:
    """TC-R10, TC-R11 — Rule Update"""

    def test_update_rule_as_owner(self, client, auth_token):
        rule_id = helper_create_rule(client, auth_token)
        response = client.patch(
            f"/api/rules/{rule_id}",
            headers={"Authorization": f"Bearer {auth_token}"},
            json={"name": "Updated Rule Name"},
        )
        assert response.status_code == 200
        assert response.json()["name"] == "Updated Rule Name"

    def test_update_rule_as_admin(self, client, auth_token, admin_token):
        rule_id = helper_create_rule(client, auth_token)
        response = client.patch(
            f"/api/rules/{rule_id}",
            headers={"Authorization": f"Bearer {admin_token}"},
            json={"severity": "LOW"},
        )
        assert response.status_code == 200
        assert response.json()["severity"] == "LOW"

    def test_update_rule_as_non_owner(self, client, auth_token):
        rule_id = helper_create_rule(client, auth_token)
        res = client.post(
            "/api/auth/register",
            json={"email": f"other_{uuid.uuid4().hex}@req.com", "password": "Password123", "full_name": "Other"},
        )
        other_token = res.json()["access_token"]
        response = client.patch(
            f"/api/rules/{rule_id}",
            headers={"Authorization": f"Bearer {other_token}"},
            json={"severity": "LOW"},
        )
        assert response.status_code == 403

class TestDeleteRule:
    """TC-R12, TC-R13 — Rule Deletion"""

    def test_delete_rule_as_owner(self, client, auth_token):
        rule_id = helper_create_rule(client, auth_token)
        response = client.delete(
            f"/api/rules/{rule_id}", headers={"Authorization": f"Bearer {auth_token}"}
        )
        assert response.status_code == 204

    def test_delete_rule_as_non_owner(self, client, auth_token):
        rule_id = helper_create_rule(client, auth_token)
        res = client.post(
            "/api/auth/register",
            json={"email": f"another_{uuid.uuid4().hex}@req.com", "password": "Password123", "full_name": "Other2"},
        )
        other_token = res.json()["access_token"]
        response = client.delete(
            f"/api/rules/{rule_id}", headers={"Authorization": f"Bearer {other_token}"}
        )
        assert response.status_code == 403
