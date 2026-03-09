"""test_reports.py — Tests for GET /api/reports/{id} and GET /api/reports/trends."""
import pytest
# from conftest import CLEAN_CSV, DIRTY_CSV, csv_file, not_null_rule, range_rule
from tests.helpers import CLEAN_CSV, DIRTY_CSV, csv_file, json_file, not_null_rule, range_rule, unique_rule, regex_rule, data_type_rule

@pytest.fixture
def checked_dataset(client):
    """Upload, add rules, run checks — returns dataset_id."""
    ds = client.post("/api/datasets/upload", files=csv_file(CLEAN_CSV, "report_clean.csv")).json()
    client.post("/api/rules", json=not_null_rule("name", "HIGH"))
    client.post("/api/rules", json=range_rule("age", 0, 120, "MEDIUM"))
    client.post(f"/api/checks/run/{ds['id']}")
    return ds["id"]


class TestGetReport:
    def test_get_report_returns_200(self, client, checked_dataset):
        resp = client.get(f"/api/reports/{checked_dataset}")
        assert resp.status_code == 200

    def test_report_has_correct_fields(self, client, checked_dataset):
        data = client.get(f"/api/reports/{checked_dataset}").json()
        for field in ["dataset_id", "dataset_name", "score", "total_rules", "results", "checked_at"]:
            assert field in data

    def test_report_dataset_id_matches(self, client, checked_dataset):
        data = client.get(f"/api/reports/{checked_dataset}").json()
        assert data["dataset_id"] == checked_dataset

    def test_report_score_is_valid_range(self, client, checked_dataset):
        data = client.get(f"/api/reports/{checked_dataset}").json()
        assert 0.0 <= data["score"] <= 100.0

    def test_report_results_is_list(self, client, checked_dataset):
        data = client.get(f"/api/reports/{checked_dataset}").json()
        assert isinstance(data["results"], list)

    def test_report_clean_data_high_score(self, client, checked_dataset):
        data = client.get(f"/api/reports/{checked_dataset}").json()
        assert data["score"] >= 90.0

    def test_report_nonexistent_dataset_404(self, client):
        assert client.get("/api/reports/99999").status_code == 404

    def test_report_before_checks_404(self, client):
        ds = client.post("/api/datasets/upload", files=csv_file(CLEAN_CSV, "no_checks.csv")).json()
        assert client.get(f"/api/reports/{ds['id']}").status_code == 404


class TestGetTrends:
    def test_trends_returns_200(self, client, checked_dataset):
        resp = client.get("/api/reports/trends")
        assert resp.status_code == 200

    def test_trends_returns_list(self, client, checked_dataset):
        data = client.get("/api/reports/trends").json()
        assert isinstance(data, list)

    def test_trends_contains_score_entry(self, client, checked_dataset):
        data = client.get("/api/reports/trends").json()
        assert len(data) > 0
        entry = data[0]
        for field in ["id", "dataset_id", "score", "total_rules", "passed_rules", "failed_rules", "checked_at"]:
            assert field in entry

    def test_trends_custom_days(self, client, checked_dataset):
        resp = client.get("/api/reports/trends?days=7")
        assert resp.status_code == 200

    def test_trends_boundary_days_1(self, client):
        assert client.get("/api/reports/trends?days=1").status_code == 200

    def test_trends_boundary_days_365(self, client):
        assert client.get("/api/reports/trends?days=365").status_code == 200

    def test_trends_invalid_days_zero(self, client):
        assert client.get("/api/reports/trends?days=0").status_code == 422

    def test_trends_invalid_days_too_large(self, client):
        assert client.get("/api/reports/trends?days=999").status_code == 422
