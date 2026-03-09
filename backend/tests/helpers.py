# helpers.py
import io
import os

CLEAN_CSV = """id,name,email,age,score
1,Alice,alice@example.com,25,95
2,Bob,bob@example.com,30,88
3,Charlie,charlie@example.com,35,92
4,Diana,diana@example.com,28,90
5,Eve,eve@example.com,32,87"""

DIRTY_CSV = """id,name,email,age,score
1,Alice,alice@example.com,25,95
2,Bob,,30,88
3,,charlie@example.com,35,
4,Diana,diana@example.com,invalid,90
5,Eve,eve@example.com,32,87
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

def not_null_rule(field, severity):
    return {"type": "not_null", "field": field, "severity": severity}

def range_rule(field, min_val, max_val, severity):
    return {"type": "range", "field": field, "min": min_val, "max": max_val, "severity": severity}

def unique_rule(field, severity):
    return {"type": "unique", "field": field, "severity": severity}

def regex_rule(field, pattern, severity):
    return {"type": "regex", "field": field, "pattern": pattern, "severity": severity}

def data_type_rule(field, dtype, severity):
    return {"type": "data_type", "field": field, "dtype": dtype, "severity": severity}