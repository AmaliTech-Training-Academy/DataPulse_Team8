"""
test_upload.py — TC-U01 through TC-U12
Tests for POST /api/datasets/upload and GET /api/datasets
"""

import io
import json
import pytest
# from conftest import CLEAN_CSV, DIRTY_CSV, VALID_JSON, csv_file, json_file
from tests.helpers import CLEAN_CSV, DIRTY_CSV, csv_file, json_file, not_null_rule, range_rule, unique_rule, regex_rule, data_type_rule

class TestUploadCSV:
    """TC-U01, U05, U06, U08, U09 — CSV Upload"""

    def test_upload_valid_csv(self, client):
        """TC-U01 — Upload a valid CSV returns 201 with correct metadata."""
        resp = client.post("/api/datasets/upload", files=csv_file(CLEAN_CSV, "clean.csv"))
        assert resp.status_code == 201
        data = resp.json()
        assert data["file_type"] == "csv"
        assert data["row_count"] == 5
        assert data["column_count"] == 5
        assert data["status"] == "PENDING"
        assert "id" in data
        assert "uploaded_at" in data

    def test_upload_csv_column_names_stored(self, client):
        """TC-U01 extended — Column names are stored correctly."""
        resp = client.post("/api/datasets/upload", files=csv_file(CLEAN_CSV, "cols.csv"))
        data = resp.json()
        cols = json.loads(data["column_names"])
        assert "id" in cols
        assert "name" in cols
        assert "email" in cols
        assert "age" in cols
        assert "score" in cols

    def test_upload_csv_header_only(self, client):
        """TC-U05 — CSV with headers but no data rows."""
        content = "id,name,email\n"
        resp = client.post("/api/datasets/upload", files=csv_file(content, "header_only.csv"))
        assert resp.status_code == 201
        data = resp.json()
        assert data["row_count"] == 0
        assert data["column_count"] == 3

    def test_upload_malformed_csv(self, client):
        """TC-U06 — CSV with inconsistent column counts per row."""
        bad = "id,name,age\n1,Alice\n2,Bob,25,extra_col\n"
        resp = client.post("/api/datasets/upload", files=csv_file(bad, "bad.csv"))
        # pandas may read this with NaN or it may fail — both are acceptable;
        # a 400 is ideal, but 201 with inferred schema is also valid
        assert resp.status_code in (201, 400)

    def test_upload_large_csv(self, client):
        """TC-U08 — Large CSV (~1000 rows) should upload successfully."""
        rows = ["id,value,label"]
        for i in range(1000):
            rows.append(f"{i},value_{i},label_{i % 10}")
        large_csv = "\n".join(rows) + "\n"
        resp = client.post("/api/datasets/upload", files=csv_file(large_csv, "large.csv"))
        assert resp.status_code == 201
        assert resp.json()["row_count"] == 1000

    def test_upload_csv_special_characters(self, client):
        """TC-U09 — CSV with UTF-8 special characters in values."""
        content = "id,name,city\n1,André,São Paulo\n2,Zoë,München\n"
        resp = client.post("/api/datasets/upload", files=csv_file(content, "utf8.csv"))
        assert resp.status_code == 201
        assert resp.json()["row_count"] == 2

    def test_upload_dirty_csv_succeeds(self, client):
        """TC-U01 extended — Dirty data should still upload (validation is separate step)."""
        resp = client.post("/api/datasets/upload", files=csv_file(DIRTY_CSV, "dirty.csv"))
        assert resp.status_code == 201
        assert resp.json()["status"] == "PENDING"


class TestUploadJSON:
    """TC-U02, U07, U12 — JSON Upload"""

    def test_upload_valid_json(self, client):
        """TC-U02 — Upload a valid JSON array returns 201."""
        resp = client.post("/api/datasets/upload", files=json_file(VALID_JSON, "data.json"))
        assert resp.status_code == 201
        data = resp.json()
        assert data["file_type"] == "json"
        assert data["row_count"] == 3
        assert data["column_count"] == 3

    def test_upload_malformed_json(self, client):
        """TC-U07 — Malformed JSON returns 400."""
        bad_json = '{"id": 1, "name": "Alice"'  # missing closing brace
        resp = client.post("/api/datasets/upload", files=json_file(bad_json, "bad.json"))
        assert resp.status_code == 400

    def test_upload_json_empty_array(self, client):
        """TC-U07 extended — Empty JSON array."""
        resp = client.post("/api/datasets/upload", files=json_file("[]", "empty.json"))
        # Pandas may error or return 0 rows — document the behavior
        assert resp.status_code in (201, 400)


class TestUploadValidation:
    """TC-U03, U04 — Upload Input Validation"""

    def test_upload_unsupported_file_type(self, client):
        """TC-U03 — .txt file returns 400."""
        files = {"file": ("notes.txt", io.BytesIO(b"hello world"), "text/plain")}
        resp = client.post("/api/datasets/upload", files=files)
        assert resp.status_code == 400
        assert "unsupported" in resp.json()["detail"].lower() or "type" in resp.json()["detail"].lower()

    def test_upload_pdf_rejected(self, client):
        """TC-U03b — .pdf file is rejected."""
        files = {"file": ("doc.pdf", io.BytesIO(b"%PDF-1.4"), "application/pdf")}
        resp = client.post("/api/datasets/upload", files=files)
        assert resp.status_code == 400

    def test_upload_empty_csv(self, client):
        """TC-U04 — Uploading a zero-byte file returns 400."""
        files = {"file": ("empty.csv", io.BytesIO(b""), "text/csv")}
        resp = client.post("/api/datasets/upload", files=files)
        assert resp.status_code == 400

    def test_upload_no_file_field(self, client):
        """TC-U04 extended — Request with no file field returns 422."""
        resp = client.post("/api/datasets/upload")
        assert resp.status_code == 422


class TestListDatasets:
    """TC-U10, U11 — GET /api/datasets"""

    def test_list_datasets_returns_200(self, client):
        """TC-U10 — GET /api/datasets returns 200 with expected shape."""
        resp = client.get("/api/datasets")
        assert resp.status_code == 200
        data = resp.json()
        assert "datasets" in data
        assert "total" in data
        assert isinstance(data["datasets"], list)
        assert isinstance(data["total"], int)

    def test_list_datasets_total_increases_after_upload(self, client):
        """TC-U10 extended — Total count increases after each upload."""
        before = client.get("/api/datasets").json()["total"]
        client.post("/api/datasets/upload", files=csv_file(CLEAN_CSV, "count_check.csv"))
        after = client.get("/api/datasets").json()["total"]
        assert after == before + 1

    def test_list_datasets_pagination_limit(self, client):
        """TC-U11 — Pagination limit is respected."""
        resp = client.get("/api/datasets?skip=0&limit=2")
        assert resp.status_code == 200
        data = resp.json()
        assert len(data["datasets"]) <= 2

    def test_list_datasets_pagination_skip(self, client):
        """TC-U11b — Skip parameter offsets the result set."""
        all_data = client.get("/api/datasets?skip=0&limit=100").json()["datasets"]
        if len(all_data) > 1:
            skipped = client.get("/api/datasets?skip=1&limit=100").json()["datasets"]
            assert len(skipped) == len(all_data) - 1

    def test_list_datasets_invalid_limit(self, client):
        """TC-U11c — Limit exceeding max (100) returns 422."""
        resp = client.get("/api/datasets?limit=999")
        assert resp.status_code == 422

    def test_list_datasets_negative_skip(self, client):
        """TC-U11d — Negative skip returns 422."""
        resp = client.get("/api/datasets?skip=-1")
        assert resp.status_code == 422

    def test_dataset_response_fields(self, client):
        """TC-U01 extended — Each dataset in list has all required fields."""
        client.post("/api/datasets/upload", files=csv_file(CLEAN_CSV, "fields_check.csv"))
        resp = client.get("/api/datasets?limit=1")
        ds = resp.json()["datasets"][0]
        for field in ["id", "name", "file_type", "row_count", "column_count", "status", "uploaded_at"]:
            assert field in ds, f"Missing field: {field}"
