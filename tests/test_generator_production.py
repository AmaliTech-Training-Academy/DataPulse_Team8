"""
Tests for data_generators.generator_production
"""

import csv
import json
import os
import sys

import pytest

from data_generators.generator_production import (
    BUILTIN_SCHEMAS,
    GenerationResult,
    ProductionDataGenerator,
    main,
)


# --------------------------------------------------------------------------- #
#  Fixtures                                                                   #
# --------------------------------------------------------------------------- #

@pytest.fixture()
def gen() -> ProductionDataGenerator:
    return ProductionDataGenerator(seed=0, log_level="WARNING")


@pytest.fixture()
def tmp_dir(tmp_path):
    return str(tmp_path)


# --------------------------------------------------------------------------- #
#  GenerationResult                                                           #
# --------------------------------------------------------------------------- #

class TestGenerationResult:
    def test_success_no_errors(self):
        r = GenerationResult("sales", 10, 10)
        assert r.success is True

    def test_failure_with_errors(self):
        r = GenerationResult("sales", 10, 10, validation_errors=["oops"])
        assert r.success is False

    def test_summary_contains_schema_name(self):
        r = GenerationResult("users", 5, 5)
        assert "users" in r.summary()


# --------------------------------------------------------------------------- #
#  Schema coverage                                                            #
# --------------------------------------------------------------------------- #

class TestBuiltinSchemas:
    @pytest.mark.parametrize("schema_name", list(BUILTIN_SCHEMAS.keys()))
    def test_each_schema_generates_rows(self, gen, schema_name):
        result = gen.run(schema_name=schema_name, rows=20, dry_run=True)
        assert result.rows_generated == 20
        assert result.success

    def test_unknown_schema_raises(self, gen):
        with pytest.raises(ValueError, match="Unknown schema"):
            gen.run(schema_name="nonexistent", rows=5, dry_run=True)


# --------------------------------------------------------------------------- #
#  Data correctness                                                           #
# --------------------------------------------------------------------------- #

class TestDataCorrectness:
    def test_sequence_ids_are_unique_and_sequential(self, gen):
        result = gen.run("sales", rows=50, dry_run=True)
        # Validation passes means no duplicate sequence values
        assert result.success

    def test_reproducible_output(self):
        r1 = ProductionDataGenerator(seed=99, log_level="WARNING").run(
            "users", rows=10, dry_run=True
        )
        r2 = ProductionDataGenerator(seed=99, log_level="WARNING").run(
            "users", rows=10, dry_run=True
        )
        assert r1.rows_generated == r2.rows_generated
        assert r1.success == r2.success

    def test_large_batch(self, gen):
        result = gen.run("quality_checks", rows=2_500, dry_run=True)
        assert result.rows_generated == 2_500
        assert result.success


# --------------------------------------------------------------------------- #
#  File output — CSV                                                          #
# --------------------------------------------------------------------------- #

class TestCSVOutput:
    def test_creates_csv_file(self, gen, tmp_dir):
        result = gen.run("sales", rows=10, output_dir=tmp_dir, fmt="csv")
        assert result.output_path is not None
        assert os.path.isfile(result.output_path)

    def test_csv_row_count(self, gen, tmp_dir):
        result = gen.run("sales", rows=15, output_dir=tmp_dir, fmt="csv")
        with open(result.output_path, newline="", encoding="utf-8") as fh:
            rows = list(csv.DictReader(fh))
        assert len(rows) == 15

    def test_csv_has_expected_columns(self, gen, tmp_dir):
        result = gen.run("users", rows=5, output_dir=tmp_dir, fmt="csv")
        with open(result.output_path, newline="", encoding="utf-8") as fh:
            reader = csv.DictReader(fh)
            cols = reader.fieldnames
        assert "id" in cols
        assert "username" in cols


# --------------------------------------------------------------------------- #
#  File output — JSON                                                         #
# --------------------------------------------------------------------------- #

class TestJSONOutput:
    def test_creates_json_file(self, gen, tmp_dir):
        result = gen.run("users", rows=5, output_dir=tmp_dir, fmt="json")
        assert os.path.isfile(result.output_path)

    def test_json_row_count(self, gen, tmp_dir):
        result = gen.run("datasets_metadata", rows=8, output_dir=tmp_dir, fmt="json")
        with open(result.output_path, encoding="utf-8") as fh:
            data = json.load(fh)
        assert len(data) == 8

    def test_unsupported_format_raises(self, gen, tmp_dir):
        with pytest.raises(ValueError, match="Unsupported format"):
            gen._write([], "x", tmp_dir, "parquet")


# --------------------------------------------------------------------------- #
#  Custom schema                                                              #
# --------------------------------------------------------------------------- #

class TestCustomSchema:
    CUSTOM_SCHEMA = [
        {"name": "id",    "type": "sequence"},
        {"name": "label", "type": "str",    "prefix": "lbl_", "length": 4},
        {"name": "score", "type": "float",  "min": 0.0, "max": 100.0, "decimals": 1},
    ]

    def test_custom_schema_generates_correct_fields(self, gen):
        result = gen.run(
            schema_name="custom",
            rows=10,
            custom_schema=self.CUSTOM_SCHEMA,
            dry_run=True,
        )
        assert result.rows_generated == 10
        assert result.success

    def test_load_schema_from_file(self, tmp_dir):
        schema_data = {"name": "test_schema", "fields": self.CUSTOM_SCHEMA}
        path = os.path.join(tmp_dir, "schema.json")
        with open(path, "w") as fh:
            json.dump(schema_data, fh)

        name, fields = ProductionDataGenerator.load_schema(path)
        assert name == "test_schema"
        assert len(fields) == 3


# --------------------------------------------------------------------------- #
#  Validation                                                                 #
# --------------------------------------------------------------------------- #

class TestValidation:
    def test_null_field_fails_validation(self, gen):
        records = [{"id": 1, "name": None}]
        schema = [
            {"name": "id",   "type": "sequence"},
            {"name": "name", "type": "str", "prefix": "", "length": 4},
        ]
        errors = gen._validate(records, schema)
        assert any("null" in e for e in errors)

    def test_out_of_range_int_fails_validation(self, gen):
        records = [{"id": 1, "score": 200}]
        schema = [
            {"name": "id",    "type": "sequence"},
            {"name": "score", "type": "int", "min": 0, "max": 100},
        ]
        errors = gen._validate(records, schema)
        assert any("score" in e for e in errors)


# --------------------------------------------------------------------------- #
#  CLI main()                                                                #
# --------------------------------------------------------------------------- #

class TestCLI:
    def test_cli_dry_run_exits_zero(self, tmp_dir):
        with pytest.raises(SystemExit) as exc_info:
            main(["--schema", "sales", "--rows", "20", "--dry-run", "--log-level", "WARNING"])
        assert exc_info.value.code == 0

    def test_cli_writes_file(self, tmp_dir):
        with pytest.raises(SystemExit) as exc_info:
            main([
                "--schema", "users",
                "--rows", "10",
                "--output", tmp_dir,
                "--format", "json",
                "--log-level", "WARNING",
            ])
        assert exc_info.value.code == 0
        files = os.listdir(tmp_dir)
        assert any(f.startswith("users") for f in files)
