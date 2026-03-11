import io

# Test Data
CLEAN_CSV = """id,name,email,age,score
1,Alice,alice@example.com,25,95
2,Bob,bob@example.com,30,88
3,Charlie,charlie@example.com,35,92
4,Diana,diana@example.com,28,90
5,Eve,eve@example.com,32,87"""

VALID_JSON = '[{"id": 1, "name": "Alice", "age": 30}, {"id": 2, "name": "Bob", "age": 25}, {"id": 3, "name": "Carol", "age": 35}]'


def csv_file(content, name):
    """Create a CSV file upload for testing."""
    return {"file": (name, io.BytesIO(content.encode("utf-8")), "text/csv")}


def json_file(content, name):
    """Create a JSON file upload for testing."""
    return {"file": (name, io.BytesIO(content.encode("utf-8")), "application/json")}


class TestUploadJSON:
    """TC-U02, U07, U12 — JSON Upload"""

    def test_upload_valid_json(self, client, auth_token):
        """TC-U02 — Upload a valid JSON array returns 201."""
        headers = {"Authorization": f"Bearer {auth_token}"}
        json_data = '[{"id": 1, "name": "Alice", "age": 30}, {"id": 2, "name": "Bob", "age": 25}, {"id": 3, "name": "Carol", "age": 35}]'
        resp = client.post(
            "/api/datasets/upload",
            files=json_file(json_data, "data.json"),
            headers=headers,
        )
        if resp.status_code != 201:
            print(resp.json())
        assert resp.status_code == 201
        data = resp.json()
        assert data["file_type"] == "json"
        assert data["row_count"] == 3
        assert data["column_count"] == 3

    def test_upload_malformed_json(self, client, auth_token):
        """TC-U07 — Malformed JSON returns 400."""
        headers = {"Authorization": f"Bearer {auth_token}"}
        bad_json = '{"id": 1, "name": "Alice"'  # missing closing brace
        resp = client.post(
            "/api/datasets/upload",
            files=json_file(bad_json, "bad.json"),
            headers=headers,
        )
        assert resp.status_code == 400

    def test_upload_json_empty_array(self, client, auth_token):
        """TC-U07 extended — Empty JSON array."""
        headers = {"Authorization": f"Bearer {auth_token}"}
        resp = client.post(
            "/api/datasets/upload", files=json_file("[]", "empty.json"), headers=headers
        )
        # After our enhancement, this should return 400 due to empty DataFrame validation
        assert resp.status_code == 400


class TestUploadValidation:
    """TC-U03, U04 — Upload Input Validation"""

    def test_upload_unsupported_file_type(self, client, auth_token):
        """TC-U03 — .txt file returns 400."""
        headers = {"Authorization": f"Bearer {auth_token}"}
        files = {"file": ("notes.txt", io.BytesIO(b"hello world"), "text/plain")}
        resp = client.post("/api/datasets/upload", files=files, headers=headers)
        assert resp.status_code == 400
        assert (
            "unsupported" in resp.json()["detail"].lower()
            or "type" in resp.json()["detail"].lower()
        )

    def test_upload_pdf_rejected(self, client, auth_token):
        """TC-U03b — .pdf file is rejected."""
        headers = {"Authorization": f"Bearer {auth_token}"}
        files = {"file": ("doc.pdf", io.BytesIO(b"%PDF-1.4"), "application/pdf")}
        resp = client.post("/api/datasets/upload", files=files, headers=headers)
        assert resp.status_code == 400

    def test_upload_empty_csv(self, client, auth_token):
        """TC-U04 — Uploading a zero-byte file returns 400."""
        headers = {"Authorization": f"Bearer {auth_token}"}
        files = {"file": ("empty.csv", io.BytesIO(b""), "text/csv")}
        resp = client.post("/api/datasets/upload", files=files, headers=headers)
        assert resp.status_code == 400

    def test_upload_no_file_field(self, client, auth_token):
        """TC-U04 extended — Request with no file field returns 422."""
        headers = {"Authorization": f"Bearer {auth_token}"}
        resp = client.post("/api/datasets/upload", headers=headers)
        assert resp.status_code == 422

    def test_upload_file_exceeds_size_limit(self, client, auth_token):
        """TC-U04b — File exceeding 10MB size limit returns 400."""
        headers = {"Authorization": f"Bearer {auth_token}"}
        # Create a file larger than 10MB (10 * 1024 * 1024 bytes)
        large_content = "x" * (11 * 1024 * 1024)  # 11MB
        files = {"file": ("huge.csv", io.BytesIO(large_content.encode()), "text/csv")}
        resp = client.post("/api/datasets/upload", files=files, headers=headers)
        assert resp.status_code == 400
        assert (
            "exceeds maximum" in resp.json()["detail"].lower()
            or "10mb" in resp.json()["detail"].lower()
        )

    def test_upload_file_no_filename(self, client, auth_token):
        """TC-U04c — File with no filename returns 422."""
        headers = {"Authorization": f"Bearer {auth_token}"}
        files = {"file": ("", io.BytesIO(b"id,name\n1,test"), "text/csv")}
        resp = client.post("/api/datasets/upload", files=files, headers=headers)
        assert resp.status_code == 422

    def test_upload_csv_with_only_headers_no_data(self, client, auth_token):
        """TC-U05b — CSV with only headers (no data rows) should be rejected."""
        headers = {"Authorization": f"Bearer {auth_token}"}
        content = "id,name,email\n"
        resp = client.post(
            "/api/datasets/upload",
            files=csv_file(content, "headers_only.csv"),
            headers=headers,
        )
        # After our enhancement, this should return 400 due to empty DataFrame validation
        assert resp.status_code == 400
        assert "no data" in resp.json()["detail"].lower()


class TestListDatasets:
    """TC-U10, U11 — GET /api/datasets"""

    def test_list_datasets_returns_200(self, client, auth_token):
        """TC-U10 — GET /api/datasets returns 200 with expected shape."""
        headers = {"Authorization": f"Bearer {auth_token}"}
        resp = client.get("/api/datasets", headers=headers)
        assert resp.status_code == 200
        data = resp.json()
        assert "datasets" in data
        assert "total" in data
        assert isinstance(data["datasets"], list)
        assert isinstance(data["total"], int)

    def test_list_datasets_total_increases_after_upload(self, client, auth_token):
        """TC-U10 extended — Total count increases after each upload."""
        headers = {"Authorization": f"Bearer {auth_token}"}
        before = client.get("/api/datasets", headers=headers).json()["total"]
        client.post(
            "/api/datasets/upload",
            files=csv_file(CLEAN_CSV, "count_check.csv"),
            headers=headers,
        )
        after = client.get("/api/datasets", headers=headers).json()["total"]
        assert after == before + 1

    def test_list_datasets_pagination_limit(self, client, auth_token):
        """TC-U11 — Pagination limit is respected."""
        headers = {"Authorization": f"Bearer {auth_token}"}
        resp = client.get("/api/datasets?skip=0&limit=2", headers=headers)
        assert resp.status_code == 200
        data = resp.json()
        assert len(data["datasets"]) <= 2

    def test_list_datasets_pagination_skip(self, client, auth_token):
        """TC-U11b — Skip parameter offsets the result set."""
        headers = {"Authorization": f"Bearer {auth_token}"}
        all_data = client.get("/api/datasets?skip=0&limit=100", headers=headers).json()[
            "datasets"
        ]
        if len(all_data) > 1:
            skipped = client.get(
                "/api/datasets?skip=1&limit=100", headers=headers
            ).json()["datasets"]
            assert len(skipped) == len(all_data) - 1

    def test_list_datasets_invalid_limit(self, client, auth_token):
        """TC-U11c — Limit exceeding max (100) returns 422."""
        headers = {"Authorization": f"Bearer {auth_token}"}
        resp = client.get("/api/datasets?limit=999", headers=headers)
        assert resp.status_code == 422

    def test_list_datasets_negative_skip(self, client, auth_token):
        """TC-U11d — Negative skip returns 422."""
        headers = {"Authorization": f"Bearer {auth_token}"}
        resp = client.get("/api/datasets?skip=-1", headers=headers)
        assert resp.status_code == 422

    def test_dataset_response_fields(self, client, auth_token):
        """TC-U01 extended — Each dataset in list has all required fields."""
        headers = {"Authorization": f"Bearer {auth_token}"}
        client.post(
            "/api/datasets/upload",
            files=csv_file(CLEAN_CSV, "fields_check.csv"),
            headers=headers,
        )
        resp = client.get("/api/datasets?limit=1", headers=headers)
        ds = resp.json()["datasets"][0]
        for field in [
            "id",
            "name",
            "file_type",
            "row_count",
            "column_count",
            "status",
            "uploaded_at",
        ]:
            assert field in ds, f"Missing field: {field}"


def test_upload_csv_success(client, auth_token):
    """Test uploading a valid CSV file."""
    csv_content = """id,name,age
1,Alice,30
2,Bob,25
3,Carol,35
"""
    files = {"file": ("test.csv", io.BytesIO(csv_content.encode()), "text/csv")}
    headers = {"Authorization": f"Bearer {auth_token}"}
    resp = client.post("/api/datasets/upload", files=files, headers=headers)
    assert resp.status_code == 201
    data = resp.json()
    assert data["name"] == "test"
    assert data["file_type"] == "csv"
    assert data["row_count"] == 3
    assert data["column_count"] == 3
    assert data["status"] == "PENDING"
