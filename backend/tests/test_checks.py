"""test_checks.py — Tests for POST /api/checks/run and GET /api/checks/results."""
import pytest
# from conftest import CLEAN_CSV, DIRTY_CSV, csv_file, not_null_rule, range_rule, unique_rule
from tests.helpers import CLEAN_CSV, DIRTY_CSV, csv_file, json_file, not_null_rule, range_rule, unique_rule, regex_rule, data_type_rule

@pytest.fixture
def dataset_with_rules(client):
    ds = client.post("/api/datasets/upload", files=csv_file(CLEAN_CSV, "checks_clean.csv")).json()
    client.post("/api/rules", json=not_null_rule("name", "HIGH"))
    client.post("/api/rules", json=unique_rule("id", "HIGH"))
    return ds["id"]


class TestRunChecks:
    def test_run_checks_returns_200_with_score(self, client, dataset_with_rules):
        resp = client.post(f"/api/checks/run/{dataset_with_rules}")
        assert resp.status_code == 200
        data = resp.json()
        assert "score" in data
        assert 0.0 <= data["score"] <= 100.0

    def test_run_checks_clean_data_high_score(self, client, dataset_with_rules):
        resp = client.post(f"/api/checks/run/{dataset_with_rules}")
        assert resp.json()["score"] >= 90.0

    def test_run_checks_dirty_data_lower_score(self, client):
        ds = client.post("/api/datasets/upload", files=csv_file(DIRTY_CSV, "dirty_run.csv")).json()
        client.post("/api/rules", json=not_null_rule("name", "HIGH"))
        resp = client.post(f"/api/checks/run/{ds['id']}")
        assert resp.status_code == 200
        assert resp.json()["score"] < 100.0

    def test_run_checks_updates_dataset_status(self, client, dataset_with_rules):
        client.post(f"/api/checks/run/{dataset_with_rules}")
        datasets = client.get("/api/datasets").json()["datasets"]
        target = next((d for d in datasets if d["id"] == dataset_with_rules), None)
        assert target["status"] in ("VALIDATED", "FAILED")

    def test_run_checks_nonexistent_dataset(self, client):
        resp = client.post("/api/checks/run/99999")
        assert resp.status_code == 404

    def test_run_checks_returns_result_counts(self, client, dataset_with_rules):
        resp = client.post(f"/api/checks/run/{dataset_with_rules}")
        data = resp.json()
        assert "total_rules" in data
        assert "passed_rules" in data
        assert "failed_rules" in data


class TestGetCheckResults:
    def test_get_results_after_run(self, client, dataset_with_rules):
        client.post(f"/api/checks/run/{dataset_with_rules}")
        resp = client.get(f"/api/checks/results/{dataset_with_rules}")
        assert resp.status_code == 200
        assert isinstance(resp.json(), list)
        assert len(resp.json()) > 0

    def test_results_have_correct_fields(self, client, dataset_with_rules):
        client.post(f"/api/checks/run/{dataset_with_rules}")
        results = client.get(f"/api/checks/results/{dataset_with_rules}").json()
        for field in ["id", "dataset_id", "rule_id", "passed", "failed_rows", "total_rows", "checked_at"]:
            assert field in results[0]

    def test_results_for_nonexistent_dataset(self, client):
        resp = client.get("/api/checks/results/99999")
        assert resp.status_code == 404

    def test_results_empty_before_run(self, client):
        ds = client.post("/api/datasets/upload", files=csv_file(CLEAN_CSV, "no_run_yet.csv")).json()
        resp = client.get(f"/api/checks/results/{ds['id']}")
        assert resp.status_code == 200
        assert resp.json() == []
