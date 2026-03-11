"""test_e2e.py — End-to-end integration tests (TC-E01 through TC-E06)."""
from tests.helpers import (
    CLEAN_CSV,
    DIRTY_CSV,
    csv_file,
    not_null_rule,
    range_rule,
    unique_rule,
)


def get_auth_headers(client, email="e2e@test.com"):
    auth = client.post(
        "/api/auth/register",
        json={"email": email, "password": "Password123", "full_name": "E2E Tester"},
    ).json()
    if "access_token" not in auth:
        # maybe already registered
        auth = client.post(
            "/api/auth/login", json={"email": email, "password": "Password123"}
        ).json()
    return {"Authorization": f"Bearer {auth['access_token']}"}


class TestE2EHappyPath:
    def test_full_flow_clean_data(self, client):
        """TC-E01 — Register → Upload → Rules → Run → Report."""
        headers = get_auth_headers(client, "e2e_happy@test.com")

        # Upload clean CSV
        ds = client.post(
            "/api/datasets/upload",
            files=csv_file(CLEAN_CSV, "e2e_clean.csv"),
            headers=headers,
        ).json()
        assert ds["status"] == "PENDING" and ds["row_count"] == 5

        # Add rules
        for rule in [
            not_null_rule("name", "HIGH"),
            not_null_rule("email", "HIGH"),
            range_rule("age", 0, 120, "MEDIUM"),
            unique_rule("id", "HIGH"),
        ]:
            r = client.post("/api/rules", json=rule, headers=headers)
            assert r.status_code == 201

        # Run checks
        check = client.post(f"/api/checks/run/{ds['id']}", headers=headers)
        assert check.status_code == 200
        assert check.json()["score"] >= 90.0

        # Dataset status updated
        datasets = client.get("/api/datasets", headers=headers).json()["datasets"]
        updated = next((d for d in datasets if d["id"] == ds["id"]), None)
        assert updated is not None
        assert updated["status"] in ("VALIDATED", "FAILED")

        # Get report
        report = client.get(f"/api/reports/{ds['id']}", headers=headers).json()
        assert report["dataset_id"] == ds["id"]
        assert report["score"] >= 90.0
        assert len(report["results"]) > 0


class TestE2EDirtyData:
    def test_full_flow_dirty_data_low_score(self, client):
        """TC-E02 — Dirty data with strict rules → low score."""
        headers = get_auth_headers(client, "e2e_dirty@test.com")
        ds = client.post(
            "/api/datasets/upload",
            files=csv_file(DIRTY_CSV, "e2e_dirty.csv"),
            headers=headers,
        ).json()
        client.post("/api/rules", json=not_null_rule("name", "HIGH"), headers=headers)
        client.post("/api/rules", json=not_null_rule("email", "HIGH"), headers=headers)

        check = client.post(f"/api/checks/run/{ds['id']}", headers=headers)
        assert check.status_code == 200
        assert check.json()["score"] < 100.0

        report = client.get(f"/api/reports/{ds['id']}", headers=headers).json()
        assert report["score"] < 100.0
        assert len(report["results"]) > 0


class TestE2EMultipleDatasets:
    def test_datasets_scored_independently(self, client):
        """TC-E04 — Two datasets have separate results."""
        headers = get_auth_headers(client, "e2e_multi@test.com")
        ds1 = client.post(
            "/api/datasets/upload",
            files=csv_file(CLEAN_CSV, "iso_clean.csv"),
            headers=headers,
        ).json()
        ds2 = client.post(
            "/api/datasets/upload",
            files=csv_file(DIRTY_CSV, "iso_dirty.csv"),
            headers=headers,
        ).json()

        client.post("/api/rules", json=not_null_rule("name", "HIGH"), headers=headers)

        client.post(f"/api/checks/run/{ds1['id']}", headers=headers)
        client.post(f"/api/checks/run/{ds2['id']}", headers=headers)

        r1 = client.get(f"/api/reports/{ds1['id']}", headers=headers).json()
        r2 = client.get(f"/api/reports/{ds2['id']}", headers=headers).json()

        assert r1["dataset_id"] == ds1["id"]
        assert r2["dataset_id"] == ds2["id"]
        assert r1["score"] > r2["score"]


class TestE2ERuleUpdateAndDelete:
    def test_update_rule_then_recheck(self, client):
        """TC-E06 partial — Update rule severity and re-run."""
        headers = get_auth_headers(client, "e2e_update@test.com")
        ds = client.post(
            "/api/datasets/upload",
            files=csv_file(CLEAN_CSV, "e2e_update.csv"),
            headers=headers,
        ).json()
        rule = client.post(
            "/api/rules", json=not_null_rule("name", "HIGH"), headers=headers
        ).json()
        rule_id = rule["id"]

        # Update severity to LOW (using PATCH since PUT isn't supported)
        updated = client.patch(
            f"/api/rules/{rule_id}", json={"severity": "LOW"}, headers=headers
        )
        assert updated.status_code == 200
        assert updated.json()["severity"] == "LOW"

        # Re-run checks — should still work
        check = client.post(f"/api/checks/run/{ds['id']}", headers=headers)
        assert check.status_code == 200

    def test_delete_rule_removes_from_list(self, client):
        """TC-R13 — Deleted rule not returned in GET /api/rules."""
        headers = get_auth_headers(client, "e2e_delete@test.com")
        rule = client.post(
            "/api/rules", json=not_null_rule("deleteme_field", "HIGH"), headers=headers
        ).json()
        rule_id = rule["id"]

        del_resp = client.delete(f"/api/rules/{rule_id}", headers=headers)
        assert del_resp.status_code == 204

        ids = [r["id"] for r in client.get("/api/rules", headers=headers).json()]
        assert rule_id not in ids


class TestE2EHealthAndSmoke:
    def test_health_check(self, client):
        assert client.get("/health").json()["status"] == "healthy"

    def test_root_endpoint(self, client):
        data = client.get("/").json()
        assert data["name"] == "DataPulse"

    def test_trends_populated_after_checks(self, client):
        headers = get_auth_headers(client, "e2e_trends@test.com")
        ds = client.post(
            "/api/datasets/upload",
            files=csv_file(CLEAN_CSV, "trend_e2e.csv"),
            headers=headers,
        ).json()
        client.post("/api/rules", json=not_null_rule("name", "HIGH"), headers=headers)
        client.post(f"/api/checks/run/{ds['id']}", headers=headers)
        trends = client.get("/api/reports/trends", headers=headers).json()
        assert len(trends) > 0
