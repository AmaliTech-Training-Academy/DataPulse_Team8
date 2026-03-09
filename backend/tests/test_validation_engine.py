"""
test_validation_engine.py — Unit tests for ValidationEngine (all checks implemented).
"""
import pytest
import pandas as pd
from unittest.mock import MagicMock
from app.services.validation_engine import ValidationEngine


@pytest.fixture
def engine():
    return ValidationEngine()


def mock_rule(rule_type, field_name, parameters=None, rule_id=1, severity="HIGH"):
    rule = MagicMock()
    rule.id = rule_id
    rule.rule_type = rule_type
    rule.field_name = field_name
    rule.parameters = parameters
    rule.severity = severity
    return rule


class TestNullCheck:
    def test_all_present_passes(self, engine):
        df = pd.DataFrame({"name": ["Alice", "Bob", "Carol"]})
        r = engine.null_check(df, "name")
        assert r["passed"] is True and r["failed_rows"] == 0

    def test_some_nulls_fails(self, engine):
        df = pd.DataFrame({"name": ["Alice", None, "Carol", None, "Eve"]})
        r = engine.null_check(df, "name")
        assert r["passed"] is False and r["failed_rows"] == 2 and r["total_rows"] == 5

    def test_all_null_fails(self, engine):
        df = pd.DataFrame({"name": [None, None, None]})
        r = engine.null_check(df, "name")
        assert r["passed"] is False and r["failed_rows"] == r["total_rows"]

    def test_field_not_found(self, engine):
        df = pd.DataFrame({"other": [1, 2]})
        r = engine.null_check(df, "missing")
        assert r["passed"] is False and "not found" in r["details"].lower()


class TestTypeCheck:
    def test_int_all_valid(self, engine):
        df = pd.DataFrame({"age": [25, 30, 45]})
        r = engine.type_check(df, "age", "int")
        assert r["passed"] is True and r["failed_rows"] == 0

    def test_int_with_strings_fails(self, engine):
        df = pd.DataFrame({"age": [25, "abc", 30, "xyz", 45]})
        r = engine.type_check(df, "age", "int")
        assert r["passed"] is False and r["failed_rows"] == 2

    def test_float_all_valid(self, engine):
        df = pd.DataFrame({"price": [1.5, 2.0, 3.99]})
        r = engine.type_check(df, "price", "float")
        assert r["passed"] is True

    def test_str_always_passes(self, engine):
        df = pd.DataFrame({"name": ["Alice", "Bob"]})
        r = engine.type_check(df, "name", "str")
        assert r["passed"] is True

    def test_unknown_type_returns_error(self, engine):
        df = pd.DataFrame({"col": [1, 2]})
        r = engine.type_check(df, "col", "datetime")
        assert r["passed"] is False and "unknown" in r["details"].lower()

    def test_field_not_found(self, engine):
        df = pd.DataFrame({"other": [1]})
        r = engine.type_check(df, "missing", "int")
        assert r["passed"] is False


class TestRangeCheck:
    def test_all_within_range(self, engine):
        df = pd.DataFrame({"age": [18, 30, 65, 90]})
        r = engine.range_check(df, "age", 0, 120)
        assert r["passed"] is True and r["failed_rows"] == 0

    def test_below_min_fails(self, engine):
        df = pd.DataFrame({"age": [15, 25, 16, 30, 22]})
        r = engine.range_check(df, "age", 18, 100)
        assert r["passed"] is False and r["failed_rows"] == 2

    def test_above_max_fails(self, engine):
        df = pd.DataFrame({"score": [80, 95, 150, 70]})
        r = engine.range_check(df, "score", 0, 100)
        assert r["passed"] is False and r["failed_rows"] == 1

    def test_boundary_values_inclusive(self, engine):
        df = pd.DataFrame({"age": [18, 40, 65]})
        r = engine.range_check(df, "age", 18, 65)
        assert r["passed"] is True and r["failed_rows"] == 0

    def test_non_numeric_field_fails(self, engine):
        df = pd.DataFrame({"name": ["Alice", "Bob"]})
        r = engine.range_check(df, "name", 0, 100)
        assert r["passed"] is False

    def test_min_only(self, engine):
        df = pd.DataFrame({"val": [-5, 0, 10, 100]})
        r = engine.range_check(df, "val", 0, None)
        assert r["passed"] is False and r["failed_rows"] == 1

    def test_field_not_found(self, engine):
        df = pd.DataFrame({"other": [1]})
        r = engine.range_check(df, "missing", 0, 10)
        assert r["passed"] is False


class TestUniqueCheck:
    def test_all_unique_passes(self, engine):
        df = pd.DataFrame({"id": [1, 2, 3, 4, 5]})
        r = engine.unique_check(df, "id")
        assert r["passed"] is True and r["failed_rows"] == 0

    def test_duplicates_fail(self, engine):
        df = pd.DataFrame({"id": [1, 2, 2, 3, 1]})
        r = engine.unique_check(df, "id")
        assert r["passed"] is False and r["failed_rows"] > 0

    def test_all_same_fails(self, engine):
        df = pd.DataFrame({"status": ["active"] * 5})
        r = engine.unique_check(df, "status")
        assert r["passed"] is False

    def test_field_not_found(self, engine):
        df = pd.DataFrame({"other": [1, 2]})
        r = engine.unique_check(df, "missing")
        assert r["passed"] is False


class TestRegexCheck:
    def test_all_match_passes(self, engine):
        df = pd.DataFrame({"phone": ["555-1234", "555-5678", "555-9999"]})
        r = engine.regex_check(df, "phone", r"^\d{3}-\d{4}$")
        assert r["passed"] is True and r["failed_rows"] == 0

    def test_some_fail(self, engine):
        df = pd.DataFrame({"code": ["abc", "ABC", "def", "DEF", "xyz"]})
        r = engine.regex_check(df, "code", r"^[a-z]+$")
        assert r["passed"] is False and r["failed_rows"] == 2

    def test_invalid_pattern_handled(self, engine):
        df = pd.DataFrame({"col": ["test"]})
        r = engine.regex_check(df, "col", r"[unclosed(")
        assert isinstance(r, dict) and "invalid" in r["details"].lower()

    def test_field_not_found(self, engine):
        df = pd.DataFrame({"other": ["x"]})
        r = engine.regex_check(df, "missing", r".*")
        assert r["passed"] is False


class TestRunAllChecks:
    def test_returns_one_result_per_rule(self, engine):
        import json
        df = pd.DataFrame({"name": ["Alice", "Bob"], "age": [30, 25]})
        rules = [mock_rule("NOT_NULL", "name", rule_id=1),
                 mock_rule("NOT_NULL", "age",  rule_id=2)]
        results = engine.run_all_checks(df, rules)
        assert len(results) == 2

    def test_each_result_has_rule_id(self, engine):
        df = pd.DataFrame({"col": ["a", "b"]})
        results = engine.run_all_checks(df, [mock_rule("NOT_NULL", "col", rule_id=42)])
        assert results[0]["rule_id"] == 42

    def test_empty_rules(self, engine):
        df = pd.DataFrame({"col": [1, 2]})
        assert engine.run_all_checks(df, []) == []

    def test_unknown_rule_type_handled(self, engine):
        df = pd.DataFrame({"col": [1]})
        results = engine.run_all_checks(df, [mock_rule("UNKNOWN", "col", rule_id=99)])
        assert len(results) == 1 and results[0]["passed"] is False
