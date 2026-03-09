"""test_e2e.py — End-to-end integration tests (TC-E01 through TC-E06)."""
import pytest
# from conftest import CLEAN_CSV, DIRTY_CSV, MIXED_CSV, csv_file, not_null_rule, range_rule, unique_rule
from tests.helpers import CLEAN_CSV, DIRTY_CSV, csv_file, json_file, not_null_rule, range_rule, unique_rule, regex_rule, data_type_rule

class TestE2EHappyPath:
    def test_full_flow_clean_data(self, client):
        """TC-E01 — Register → Upload → Rules → Run → Report."""
        # Register
        auth = client.post("/api/auth/register", json={
            "email": "e2e_happy@test.com", "password": "pass123", "full_name": "E2E Happy"
        }).json()
        assert "access_token" in auth

        # Upload clean CSV
        ds = client.post("/api/datasets/upload", files=csv_file(CLEAN_CSV, "e2e_clean.csv")).json()
        assert ds["status"] == "PENDING" and ds["row_count"] == 5

        # Add rules
        for rule in [not_null_rule("name"), not_null_rule("email"), range_rule("age", 0, 120), unique_rule("id")]:
            r = client.post("/api/rules", json=rule)
            assert r.status_code == 201

        # Run checks
        check = client.post(f"/api/checks/run/{ds['id']}")
        assert check.status_code == 200
        assert check.json()["score"] >= 90.0

        # Dataset status updated
        datasets = client.get("/api/datasets").json()["datasets"]
        updated = next(d for d in datasets if d["id"] == ds["id"])
        assert updated["status"] in ("VALIDATED", "FAILED")

        # Get report
        report = client.get(f"/api/reports/{ds['id']}").json()
        assert report["dataset_id"] == ds["id"]
        assert report["score"] >= 90.0
        assert len(report["results"]) > 0


class TestE2EDirtyData:
    def test_full_flow_dirty_data_low_score(self, client):
        """TC-E02 — Dirty data with strict rules → low score."""
        ds = client.post("/api/datasets/upload", files=csv_file(DIRTY_CSV, "e2e_dirty.csv")).json()
        client.post("/api/rules", json=not_null_rule("name", "HIGH"))
        client.post("/api/rules", json=not_null_rule("email", "HIGH"))

        check = client.post(f"/api/checks/run/{ds['id']}")
        assert check.status_code == 200
        assert check.json()["score"] < 100.0

        report = client.get(f"/api/reports/{ds['id']}").json()
        assert report["score"] < 100.0
        assert len(report["results"]) > 0


class TestE2EMultipleDatasets:
    def test_datasets_scored_independently(self, client):
        """TC-E04 — Two datasets have separate results."""
        ds1 = client.post("/api/datasets/upload", files=csv_file(CLEAN_CSV, "iso_clean.csv")).json()
        ds2 = client.post("/api/datasets/upload", files=csv_file(DIRTY_CSV, "iso_dirty.csv")).json()

        client.post("/api/rules", json=not_null_rule("name", "HIGH"))

        client.post(f"/api/checks/run/{ds1['id']}")
        client.post(f"/api/checks/run/{ds2['id']}")

        r1 = client.get(f"/api/reports/{ds1['id']}").json()
        r2 = client.get(f"/api/reports/{ds2['id']}").json()

        assert r1["dataset_id"] == ds1["id"]
        assert r2["dataset_id"] == ds2["id"]
        assert r1["score"] > r2["score"]


class TestE2ERuleUpdateAndDelete:
    def test_update_rule_then_recheck(self, client):
        """TC-E06 partial — Update rule severity and re-run."""
        ds = client.post("/api/datasets/upload", files=csv_file(CLEAN_CSV, "e2e_update.csv")).json()
        rule = client.post("/api/rules", json=not_null_rule("name", "HIGH")).json()
        rule_id = rule["id"]

        # Update severity to LOW
        updated = client.put(f"/api/rules/{rule_id}", json={"severity": "LOW"})
        assert updated.status_code == 200
        assert updated.json()["severity"] == "LOW"

        # Re-run checks — should still work
        check = client.post(f"/api/checks/run/{ds['id']}")
        assert check.status_code == 200

    def test_delete_rule_removes_from_list(self, client):
        """TC-R13 — Deleted rule not returned in GET /api/rules."""
        rule = client.post("/api/rules", json=not_null_rule("deleteme_field")).json()
        rule_id = rule["id"]

        del_resp = client.delete(f"/api/rules/{rule_id}")
        assert del_resp.status_code == 204

        ids = [r["id"] for r in client.get("/api/rules").json()]
        assert rule_id not in ids


class TestE2EHealthAndSmoke:
    def test_health_check(self, client):
        assert client.get("/health").json()["status"] == "healthy"

    def test_root_endpoint(self, client):
        data = client.get("/").json()
        assert data["name"] == "DataPulse"

    def test_trends_populated_after_checks(self, client):
        ds = client.post("/api/datasets/upload", files=csv_file(CLEAN_CSV, "trend_e2e.csv")).json()
        client.post("/api/rules", json=not_null_rule("name"))
        client.post(f"/api/checks/run/{ds['id']}")
        trends = client.get("/api/reports/trends").json()
        assert len(trends) > 0
