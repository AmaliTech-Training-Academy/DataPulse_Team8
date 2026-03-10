import io
import json
import os

CLEAN_CSV = """id,name,email,age,score
1,Alice,alice@example.com,25,95
2,Bob,bob@example.com,30,88
3,Charlie,charlie@example.com,35,92
4,Diana,diana@example.com,28,90
5,Eve,eve@example.com,32,87"""

DIRTY_CSV = """id,name,email,age,score
1,Alice,alice@example.com,25,95
2,Bob,bob@example.com,,88
3,,charlie@example.com,35,75
4,Diana,diana@example.com,invalid,90
5,Eve,eve@example.com,32,87
5,Eve,eve@example.com,32,87"""

MIXED_CSV = """id,name,email,age,score
1,Alice,alice@example.com,25,95
2,Bob,bob@example.com,30,88
3,,charlie@example.com,35,92
4,Diana,diana@example.com,28,90
5,Eve,eve@example.com,32,87"""

VALID_JSON = '{"data": []}'


def csv_file(content, name):
    """Create a CSV file upload from content string or file path.

    Args:
        content: Either CSV content as string or path to CSV file
        name: Filename for the upload
    """
    if isinstance(content, str) and os.path.exists(content):
        # It's a file path
        return {"file": (name, open(content, "rb"), "text/csv")}
    else:
        # It's inline content
        return {"file": (name, io.BytesIO(content.encode("utf-8")), "text/csv")}


def json_file(content, name):
    """Create a JSON file upload from content string or file path.

    Args:
        content: Either JSON content as string or path to JSON file
        name: Filename for the upload
    """
    if isinstance(content, str) and os.path.exists(content):
        # It's a file path
        with open(content, "rb") as f:
            file_content = f.read()
    else:
        # It's inline content
        file_content = content.encode("utf-8")
    return {"file": (name, io.BytesIO(file_content), "application/json")}


def not_null_rule(field_name: str, severity: str = "MEDIUM"):
    return {
        "name": f"Not Null {field_name}",
        "dataset_type": "csv",
        "field_name": field_name,
        "rule_type": "NOT_NULL",
        "severity": severity,
    }


def data_type_rule(field_name: str, expected_type: str, severity: str = "MEDIUM"):
    return {
        "name": f"Data Type {field_name}",
        "dataset_type": "csv",
        "field_name": field_name,
        "rule_type": "DATA_TYPE",
        "parameters": json.dumps({"expected_type": expected_type}),
        "severity": severity,
    }


def range_rule(
    field_name: str, min_val: float, max_val: float, severity: str = "MEDIUM"
):
    return {
        "name": f"Range {field_name}",
        "dataset_type": "csv",
        "field_name": field_name,
        "rule_type": "RANGE",
        "parameters": json.dumps({"min": min_val, "max": max_val}),
        "severity": severity,
    }


def unique_rule(field_name: str, severity: str = "MEDIUM"):
    return {
        "name": f"Unique {field_name}",
        "dataset_type": "csv",
        "field_name": field_name,
        "rule_type": "UNIQUE",
        "severity": severity,
    }


def regex_rule(field_name: str, pattern: str, severity: str = "MEDIUM"):
    return {
        "name": f"Regex {field_name}",
        "dataset_type": "csv",
        "field_name": field_name,
        "rule_type": "REGEX",
        "parameters": json.dumps({"pattern": pattern}),
        "severity": severity,
    }
