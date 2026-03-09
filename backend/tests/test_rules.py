"""
test_rules.py — TC-R01 through TC-R13
Tests for POST/GET/PUT/DELETE /api/rules
"""

import json
import pytest
# from conftest import not_null_rule, data_type_rule, range_rule, unique_rule, regex_rule
from tests.helpers import CLEAN_CSV, DIRTY_CSV, csv_file, json_file, not_null_rule, range_rule, unique_rule, regex_rule, data_type_rule

class TestCreateRule:
    """TC-R01 to TC-R07 — Rule Creation"""

    def test_create_not_null_rule(self, client):
        """TC-R01 — Create a NOT_NULL rule returns 201 with correct fields."""
        resp = client.post("/api/rules", json=not_null_rule("email", "HIGH"))
        assert resp.status_code == 201
        data = resp.json()
        assert data["rule_type"] == "NOT_NULL"
        assert data["field_name"] == "email"
        assert data["severity"] == "HIGH"
        assert data["is_active"] is True
        assert "id" in data
        assert "created_at" in data

    def test_create_data_type_rule(self, client):
        """TC-R02 — Create a DATA_TYPE rule with parameters stored correctly."""
        resp = client.post("/api/rules", json=data_type_rule("age", "int", "MEDIUM"))
        assert resp.status_code == 201
        data = resp.json()
        assert data["rule_type"] == "DATA_TYPE"
        params = json.loads(data["parameters"])
        assert params["expected_type"] == "int"

    def test_create_range_rule(self, client):
        """TC-R03 — Create a RANGE rule with min/max parameters."""
        resp = client.post("/api/rules", json=range_rule("score", 0, 100, "MEDIUM"))
        assert resp.status_code == 201
        data = resp.json()
        assert data["rule_type"] == "RANGE"
        params = json.loads(data["parameters"])
        assert params["min"] == 0
        assert params["max"] == 100

    def test_create_unique_rule(self, client):
        """TC-R04 — Create a UNIQUE rule returns 201."""
        resp = client.post("/api/rules", json=unique_rule("id", "HIGH"))
        assert resp.status_code == 201
        assert resp.json()["rule_type"] == "UNIQUE"

    def test_create_regex_rule(self, client):
        """TC-R05 — Create a REGEX rule with pattern stored."""
        rule = regex_rule("email", r"^[\w.+-]+@[\w-]+\.\w+$", "LOW")
        resp = client.post("/api/rules", json=rule)
        assert resp.status_code == 201
        data = resp.json()
        assert data["rule_type"] == "REGEX"
        params = json.loads(data["parameters"])
        assert "pattern" in params

    def test_create_rule_invalid_type(self, client):
        """TC-R06 — Invalid rule_type returns 400."""
        bad_rule = not_null_rule("name", "HIGH")
        bad_rule["rule_type"] = "DOES_NOT_EXIST"
        resp = client.post("/api/rules", json=bad_rule)
        assert resp.status_code == 400

    def test_create_rule_invalid_severity(self, client):
        """TC-R07 — Invalid severity returns 400."""
        bad_rule = not_null_rule("name", "HIGH")
        bad_rule["severity"] = "CRITICAL"
        resp = client.post("/api/rules", json=bad_rule)
        assert resp.status_code == 400

    def test_create_rule_missing_required_fields(self, client):
        """TC-R06 extended — Missing required fields returns 422."""
        resp = client.post("/api/rules", json={"name": "incomplete"})
        assert resp.status_code == 422

    def test_create_rule_all_severities(self, client):
        """TC-R07 extended — HIGH, MEDIUM, LOW are all valid severities."""
        for sev in ["HIGH", "MEDIUM", "LOW"]:
            rule = not_null_rule(f"field_{sev.lower()}", sev)
            rule["name"] = f"severity_test_{sev}"
            resp = client.post("/api/rules", json=rule)
            assert resp.status_code == 201, f"Severity {sev} should be accepted"

    def test_create_rule_all_rule_types(self, client):
        """TC-R06 extended — All 5 valid rule types are accepted."""
        for rt in ["NOT_NULL", "DATA_TYPE", "RANGE", "UNIQUE", "REGEX"]:
            rule = {
                "name": f"type_test_{rt}",
                "dataset_type": "csv",
                "field_name": "test_field",
                "rule_type": rt,
                "severity": "LOW",
            }
            if rt == "DATA_TYPE":
                rule["parameters"] = json.dumps({"expected_type": "str"})
            elif rt == "RANGE":
                rule["parameters"] = json.dumps({"min": 0, "max": 100})
            elif rt == "REGEX":
                rule["parameters"] = json.dumps({"pattern": r".*"})
            resp = client.post("/api/rules", json=rule)
            assert resp.status_code == 201, f"Rule type {rt} should be accepted"

    def test_create_rule_empty_field_name(self, client):
        """TC-R06b — Empty field name returns 400."""
        rule = not_null_rule("", "HIGH")
        resp = client.post("/api/rules", json=rule)
        assert resp.status_code == 400
        assert "field name" in resp.json()["detail"].lower()

    def test_create_data_type_rule_missing_parameters(self, client):
        """TC-R06c — DATA_TYPE rule without parameters returns 400."""
        rule = {
            "name": "test_data_type",
            "dataset_type": "csv",
            "field_name": "age",
            "rule_type": "DATA_TYPE",
            "severity": "MEDIUM"
        }
        resp = client.post("/api/rules", json=rule)
        assert resp.status_code == 400
        assert "requires parameters" in resp.json()["detail"]

    def test_create_data_type_rule_invalid_type(self, client):
        """TC-R06d — DATA_TYPE rule with invalid expected_type returns 400."""
        rule = data_type_rule("age", "invalid_type", "MEDIUM")
        resp = client.post("/api/rules", json=rule)
        assert resp.status_code == 400
        assert "expected_type" in resp.json()["detail"]

    def test_create_range_rule_min_greater_than_max(self, client):
        """TC-R06e — RANGE rule with min >= max returns 400."""
        rule = range_rule("score", 100, 50, "MEDIUM")
        resp = client.post("/api/rules", json=rule)
        assert resp.status_code == 400
        assert "min" in resp.json()["detail"].lower() and "max" in resp.json()["detail"].lower()

    def test_create_range_rule_missing_parameters(self, client):
        """TC-R06f — RANGE rule without min or max returns 400."""
        rule = {
            "name": "test_range",
            "dataset_type": "csv",
            "field_name": "score",
            "rule_type": "RANGE",
            "severity": "MEDIUM"
        }
        resp = client.post("/api/rules", json=rule)
        assert resp.status_code == 400
        assert "requires" in resp.json()["detail"]

    def test_create_regex_rule_missing_pattern(self, client):
        """TC-R06g — REGEX rule without pattern returns 400."""
        rule = {
            "name": "test_regex",
            "dataset_type": "csv",
            "field_name": "email",
            "rule_type": "REGEX",
            "severity": "MEDIUM",
            "parameters": json.dumps({})
        }
        resp = client.post("/api/rules", json=rule)
        assert resp.status_code == 400
        assert "pattern" in resp.json()["detail"]

    def test_create_rule_invalid_json_parameters(self, client):
        """TC-R06h — Invalid JSON in parameters returns 400."""
        rule = {
            "name": "test_invalid_json",
            "dataset_type": "csv",
            "field_name": "age",
            "rule_type": "DATA_TYPE",
            "severity": "MEDIUM",
            "parameters": "not valid json"
        }
        resp = client.post("/api/rules", json=rule)
        assert resp.status_code == 400
        assert "json" in resp.json()["detail"].lower()


class TestListRules:
    """TC-R08, TC-R09 — Rule Listing"""

    def test_list_rules_returns_200(self, client):
        """TC-R08 — GET /api/rules returns 200 with a list."""
        resp = client.get("/api/rules")
        assert resp.status_code == 200
        assert isinstance(resp.json(), list)

    def test_list_rules_contains_created_rule(self, client):
        """TC-R08 extended — A newly created rule appears in the list."""
        rule = not_null_rule("list_check_field", "HIGH")
        rule["name"] = "unique_list_check_rule"
        client.post("/api/rules", json=rule)
        resp = client.get("/api/rules")
        names = [r["name"] for r in resp.json()]
        assert "unique_list_check_rule" in names

    def test_list_rules_filter_by_dataset_type(self, client):
        """TC-R09 — Filter by dataset_type returns only matching rules."""
        # Create a JSON-typed rule
        json_rule = not_null_rule("json_field", "HIGH")
        json_rule["name"] = "json_type_rule"
        json_rule["dataset_type"] = "json"
        client.post("/api/rules", json=json_rule)

        resp = client.get("/api/rules?dataset_type=json")
        assert resp.status_code == 200
        for rule in resp.json():
            assert rule["dataset_type"] == "json"

    def test_list_rules_only_active(self, client):
        """TC-R08 extended — Inactive rules should not appear in list."""
        resp = client.get("/api/rules")
        for rule in resp.json():
            assert rule["is_active"] is True

    def test_list_rules_response_shape(self, client):
        """TC-R08 extended — Each rule has the expected fields."""
        resp = client.get("/api/rules")
        if resp.json():
            rule = resp.json()[0]
            for field in ["id", "name", "dataset_type", "field_name", "rule_type", "severity", "is_active", "created_at"]:
                assert field in rule, f"Missing field: {field}"


class TestUpdateRule:
    """TC-R10, TC-R11 — Rule Update (TODO endpoint)"""

    def test_update_rule_field_name(self, client):
        """TC-R10 — Update field_name succeeds and is returned."""
        rule_resp = client.post("/api/rules", json=not_null_rule("original_field", "HIGH"))
        rule_id = rule_resp.json()["id"]
        resp = client.put(f"/api/rules/{rule_id}", json={"field_name": "new_field"})
        assert resp.status_code == 200
        assert resp.json()["field_name"] == "new_field"

    def test_update_rule_severity(self, client):
        """TC-R10 — Update severity to LOW succeeds."""
        rule_resp = client.post("/api/rules", json=not_null_rule("sev_field", "HIGH"))
        rule_id = rule_resp.json()["id"]
        resp = client.put(f"/api/rules/{rule_id}", json={"severity": "LOW"})
        assert resp.status_code == 200
        assert resp.json()["severity"] == "LOW"

    def test_update_nonexistent_rule(self, client):
        """TC-R11 — PUT /api/rules/99999 should return 404."""
        resp = client.put("/api/rules/99999", json={"field_name": "whatever"})
        assert resp.status_code == 404

    def test_update_rule_partial_update(self, client):
        """TC-R10b — Partial update only changes specified fields."""
        rule_resp = client.post("/api/rules", json=not_null_rule("partial_field", "HIGH"))
        rule_id = rule_resp.json()["id"]
        original_name = rule_resp.json()["name"]
        
        resp = client.put(f"/api/rules/{rule_id}", json={"severity": "MEDIUM"})
        assert resp.status_code == 200
        assert resp.json()["severity"] == "MEDIUM"
        assert resp.json()["name"] == original_name  # Name unchanged


class TestDeleteRule:
    """TC-R12, TC-R13 — Rule Deletion"""

    def test_delete_rule_soft_deletes(self, client):
        """TC-R12 — Delete returns 204 and rule is deactivated."""
        rule_resp = client.post("/api/rules", json=not_null_rule("soft_delete_field", "HIGH"))
        rule_id = rule_resp.json()["id"]
        del_resp = client.delete(f"/api/rules/{rule_id}")
        assert del_resp.status_code == 204

    def test_deleted_rule_absent_from_list(self, client):
        """TC-R13 — Deleted rule not returned by GET /api/rules."""
        rule_resp = client.post("/api/rules", json=not_null_rule("absent_check_field", "HIGH"))
        rule_id = rule_resp.json()["id"]
        client.delete(f"/api/rules/{rule_id}")
        ids = [r["id"] for r in client.get("/api/rules").json()]
        assert rule_id not in ids

    def test_delete_nonexistent_rule(self, client):
        """TC-R11 extended — DELETE /api/rules/99999 returns 404."""
        resp = client.delete("/api/rules/99999")
        assert resp.status_code == 404

    def test_delete_rule_twice_idempotent(self, client):
        """TC-R12b — Deleting same rule twice should still return 204."""
        rule_resp = client.post("/api/rules", json=not_null_rule("double_delete", "HIGH"))
        rule_id = rule_resp.json()["id"]
        
        # First delete
        resp1 = client.delete(f"/api/rules/{rule_id}")
        assert resp1.status_code == 204
        
        # Second delete - should still work (idempotent)
        resp2 = client.delete(f"/api/rules/{rule_id}")
        assert resp2.status_code == 204
