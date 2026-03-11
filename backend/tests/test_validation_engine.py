"""Unit tests for the ValidationEngine."""

import json
import pandas as pd
from app.services.validation_engine import ValidationEngine

# Mock Rule class mimicking SQLAlchemy model
class MockRule:
    def __init__(self, id, rule_type, field_name, parameters=None):
        self.id = id
        self.rule_type = rule_type
        self.field_name = field_name
        self.parameters = json.dumps(parameters) if parameters else None

def test_validation_engine_empty_dataframe():
    engine = ValidationEngine()
    df = pd.DataFrame()
    rules = [MockRule(1, "NOT_NULL", "name")]
    
    results = engine.run_all_checks(df, rules)
    assert len(results) == 1
    assert results[0]["passed"] is False
    assert "Dataset is empty" in results[0]["details"]

def test_validation_engine_missing_field():
    engine = ValidationEngine()
    df = pd.DataFrame({"age": [25, 30]})
    rules = [MockRule(1, "RANGE", "score", {"min": 0, "max": 100})]
    
    results = engine.run_all_checks(df, rules)
    assert len(results) == 1
    assert results[0]["passed"] is False
    assert "not found in dataset" in results[0]["details"]

def test_validation_engine_all_null_column_passes_conditional_rules():
    """If a column is 100% null, it should fail NOT_NULL but pass Type, Range, Unique, Regex."""
    engine = ValidationEngine()
    df = pd.DataFrame({
        "all_nulls": [None, None, None]
    })
    
    rules = [
        MockRule(1, "NOT_NULL", "all_nulls"),
        MockRule(2, "DATA_TYPE", "all_nulls", {"expected_type": "int"}),
        MockRule(3, "RANGE", "all_nulls", {"min": 0, "max": 100}),
        MockRule(4, "UNIQUE", "all_nulls"),
        MockRule(5, "REGEX", "all_nulls", {"pattern": "^[A-Z]+$"})
    ]
    
    results = engine.run_all_checks(df, rules)
    assert len(results) == 5
    
    # 1. NOT_NULL should fail
    assert results[0]["rule_type"] == "NOT_NULL" if "rule_type" in results[0] else results[0]["rule_id"] == 1
    assert results[0]["passed"] is False
    assert "completely empty" in results[0]["details"]
    assert results[0]["failed_rows"] == 3
    
    # 2-5. DATA_TYPE, RANGE, UNIQUE, REGEX should pass by default for 100% null columns
    for res in results[1:]:
        assert res["passed"] is True
        assert res["failed_rows"] == 0
        assert "entirely null" in res["details"]

def test_validation_engine_mixed_nulls():
    engine = ValidationEngine()
    df = pd.DataFrame({
        "mixed": [25, None, 30, 150] # 1 null, 1 out of range, 2 valid
    })
    
    rules = [MockRule(1, "RANGE", "mixed", {"min": 0, "max": 100})]
    results = engine.run_all_checks(df, rules)
    
    assert results[0]["passed"] is False
    assert results[0]["failed_rows"] == 1  # only '150' fails the range check
    assert "outside allowed range" in results[0]["details"]

def test_validation_engine_regex_matches():
    engine = ValidationEngine()
    df = pd.DataFrame({
        "emails": ["test@example.com", "invalid-email", None, "valid@test.org"]
    })
    
    rules = [MockRule(1, "REGEX", "emails", {"pattern": r"^[\w\.-]+@[\w\.-]+\.\w+$"})]
    results = engine.run_all_checks(df, rules)
    
    assert results[0]["passed"] is False
    assert results[0]["failed_rows"] == 1  # 'invalid-email' fails. None is ignored.
    assert "failed to match regex pattern" in results[0]["details"]
