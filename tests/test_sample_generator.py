"""
Tests for data_generators.sample_generator
"""

import csv
import json
import os
import tempfile

import pytest

from data_generators.sample_generator import SampleDataGenerator, main


# --------------------------------------------------------------------------- #
#  Fixtures                                                                   #
# --------------------------------------------------------------------------- #

@pytest.fixture()
def gen() -> SampleDataGenerator:
    return SampleDataGenerator(seed=42)


@pytest.fixture()
def tmp_dir(tmp_path):
    return str(tmp_path)


# --------------------------------------------------------------------------- #
#  generate_sales                                                             #
# --------------------------------------------------------------------------- #

class TestGenerateSales:
    def test_default_row_count(self, gen):
        records = gen.generate_sales()
        assert len(records) == 100

    def test_custom_row_count(self, gen):
        records = gen.generate_sales(rows=25)
        assert len(records) == 25

    def test_required_fields(self, gen):
        expected = {"id", "date", "product", "category", "quantity",
                    "unit_price", "total", "region", "customer_id", "status"}
        for rec in gen.generate_sales(rows=5):
            assert expected.issubset(rec.keys())

    def test_ids_are_sequential(self, gen):
        records = gen.generate_sales(rows=10)
        ids = [r["id"] for r in records]
        assert ids == list(range(1, 11))

    def test_total_equals_qty_times_price(self, gen):
        for rec in gen.generate_sales(rows=50):
            expected_total = round(rec["quantity"] * rec["unit_price"], 2)
            assert rec["total"] == expected_total

    def test_reproducible_with_same_seed(self):
        a = SampleDataGenerator(seed=7).generate_sales(rows=10)
        b = SampleDataGenerator(seed=7).generate_sales(rows=10)
        assert a == b

    def test_different_seeds_differ(self):
        a = SampleDataGenerator(seed=1).generate_sales(rows=10)
        b = SampleDataGenerator(seed=2).generate_sales(rows=10)
        assert a != b


# --------------------------------------------------------------------------- #
#  generate_users                                                             #
# --------------------------------------------------------------------------- #

class TestGenerateUsers:
    def test_row_count(self, gen):
        records = gen.generate_users(rows=20)
        assert len(records) == 20

    def test_required_fields(self, gen):
        expected = {"id", "username", "email", "role", "active", "created_at"}
        for rec in gen.generate_users(rows=5):
            assert expected.issubset(rec.keys())

    def test_email_contains_at(self, gen):
        for rec in gen.generate_users(rows=10):
            assert "@" in rec["email"]


# --------------------------------------------------------------------------- #
#  generate_quality_checks                                                   #
# --------------------------------------------------------------------------- #

class TestGenerateQualityChecks:
    def test_row_count(self, gen):
        records = gen.generate_quality_checks(rows=15)
        assert len(records) == 15

    def test_score_in_range(self, gen):
        for rec in gen.generate_quality_checks(rows=50):
            assert 0.0 <= rec["score"] <= 1.0


# --------------------------------------------------------------------------- #
#  generate_datasets_metadata                                                #
# --------------------------------------------------------------------------- #

class TestGenerateDatasetsMetadata:
    def test_row_count(self, gen):
        records = gen.generate_datasets_metadata(rows=8)
        assert len(records) == 8

    def test_required_fields(self, gen):
        expected = {"id", "name", "description", "file_type",
                    "row_count", "column_count", "uploaded_by",
                    "uploaded_at", "status"}
        for rec in gen.generate_datasets_metadata(rows=3):
            assert expected.issubset(rec.keys())


# --------------------------------------------------------------------------- #
#  save — CSV                                                                #
# --------------------------------------------------------------------------- #

class TestSaveCSV:
    def test_creates_file(self, gen, tmp_dir):
        records = gen.generate_sales(rows=5)
        path = gen.save(records, "sales", output_dir=tmp_dir, fmt="csv")
        assert os.path.isfile(path)

    def test_csv_row_count(self, gen, tmp_dir):
        records = gen.generate_sales(rows=10)
        path = gen.save(records, "sales", output_dir=tmp_dir, fmt="csv")
        with open(path, newline="", encoding="utf-8") as fh:
            reader = list(csv.DictReader(fh))
        assert len(reader) == 10

    def test_csv_has_headers(self, gen, tmp_dir):
        records = gen.generate_sales(rows=3)
        path = gen.save(records, "sales", output_dir=tmp_dir, fmt="csv")
        with open(path, encoding="utf-8") as fh:
            header = fh.readline()
        assert "id" in header and "total" in header


# --------------------------------------------------------------------------- #
#  save — JSON                                                               #
# --------------------------------------------------------------------------- #

class TestSaveJSON:
    def test_creates_file(self, gen, tmp_dir):
        records = gen.generate_users(rows=5)
        path = gen.save(records, "users", output_dir=tmp_dir, fmt="json")
        assert os.path.isfile(path)

    def test_json_row_count(self, gen, tmp_dir):
        records = gen.generate_users(rows=7)
        path = gen.save(records, "users", output_dir=tmp_dir, fmt="json")
        with open(path, encoding="utf-8") as fh:
            data = json.load(fh)
        assert len(data) == 7

    def test_unsupported_format_raises(self, gen, tmp_dir):
        with pytest.raises(ValueError, match="Unsupported format"):
            gen.save([], "x", output_dir=tmp_dir, fmt="parquet")


# --------------------------------------------------------------------------- #
#  CLI main()                                                                #
# --------------------------------------------------------------------------- #

class TestCLI:
    def test_main_creates_all_datasets(self, tmp_dir):
        main(["--rows", "10", "--output", tmp_dir, "--format", "csv"])
        files = os.listdir(tmp_dir)
        assert any(f.startswith("sales") for f in files)
        assert any(f.startswith("users") for f in files)
        assert any(f.startswith("quality_checks") for f in files)
        assert any(f.startswith("datasets_metadata") for f in files)

    def test_main_json_format(self, tmp_dir):
        main(["--rows", "5", "--output", tmp_dir, "--format", "json"])
        files = os.listdir(tmp_dir)
        assert any(f.endswith(".json") for f in files)
