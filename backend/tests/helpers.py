"""
helpers.py — Test utilities for DataPulse pytest suite.
This file provides backward compatibility for tests that import from tests.helpers.
All fixtures and utilities are also available directly from conftest.py.
"""

import io
import json


# ── CSV / JSON test content ───────────────────────────────────────────────────

CLEAN_CSV = (
    "id,name,email,age,score\n"
    "1,Alice,alice@test.com,30,85\n"
    "2,Bob,bob@test.com,28,92\n"
    "3,Carol,carol@test.com,35,78\n"
    "4,David,david@test.com,42,88\n"
    "5,Eve,eve@test.com,26,95\n"
)

DIRTY_CSV = (
    "id,name,email,age,score\n"
    "1,,alice@test.com,30,85\n"
    "2,Bob,not-email,-5,\n"
    "3,Carol,carol@test.com,abc,78\n"
    "4,,david@test.com,42,88\n"
    "5,Eve,,26,150\n"
)

MIXED_CSV = (
    "id,name,email,age,score\n"
    "1,Alice,alice@test.com,30,85\n"
    "2,Bob,bob@test.com,28,92\n"
    "3,,carol@test.com,35,78\n"
    "4,David,david@test.com,42,88\n"
    "5,Eve,eve@test.com,200,95\n"
)

VALID_JSON = json.dumps([
    {"id": 1, "name": "Alice", "age": 30},
    {"id": 2, "name": "Bob",   "age": 25},
    {"id": 3, "name": "Carol", "age": 35},
])


def csv_file(content, filename="test.csv"):
    return {"file": (filename, io.BytesIO(content.encode()), "text/csv")}


def json_file(content, filename="test.json"):
    return {"file": (filename, io.BytesIO(content.encode()), "application/json")}


# ── Rule payload helpers ──────────────────────────────────────────────────────

def not_null_rule(field="name", severity="HIGH"):
    return {"name": f"no_nulls_{field}", "dataset_type": "csv",
            "field_name": field, "rule_type": "NOT_NULL", "severity": severity}


def data_type_rule(field="age", expected_type="int", severity="MEDIUM"):
    return {"name": f"type_{field}", "dataset_type": "csv", "field_name": field,
            "rule_type": "DATA_TYPE", "parameters": json.dumps({"expected_type": expected_type}),
            "severity": severity}


def range_rule(field="score", min_val=0, max_val=100, severity="MEDIUM"):
    return {"name": f"range_{field}", "dataset_type": "csv", "field_name": field,
            "rule_type": "RANGE", "parameters": json.dumps({"min": min_val, "max": max_val}),
            "severity": severity}


def unique_rule(field="id", severity="HIGH"):
    return {"name": f"unique_{field}", "dataset_type": "csv",
            "field_name": field, "rule_type": "UNIQUE", "severity": severity}


def regex_rule(field="email", pattern=r"^[\w.+-]+@[\w-]+\.\w+$", severity="LOW"):
    return {"name": f"regex_{field}", "dataset_type": "csv", "field_name": field,
            "rule_type": "REGEX", "parameters": json.dumps({"pattern": pattern}),
            "severity": severity}


__all__ = [
    "CLEAN_CSV",
    "DIRTY_CSV",
    "MIXED_CSV",
    "VALID_JSON",
    "csv_file",
    "json_file",
    "not_null_rule",
    "data_type_rule",
    "range_rule",
    "unique_rule",
    "regex_rule",
]
