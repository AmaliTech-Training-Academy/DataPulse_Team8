# helpers.py
CLEAN_CSV = "tests/data/checks_clean.csv"
DIRTY_CSV = "tests/data/checks_dirty.csv"
VALID_JSON = "tests/data/valid.json"

def csv_file(path, name):
    return {"file": (name, open(path, "rb"), "text/csv")}

def json_file(path, name):
    import io
    if isinstance(path, str) and not path.endswith(".json"):
        content = path.encode("utf-8")
    else:
        with open(path, "rb") as f:
            content = f.read()
    return {"file": (name, io.BytesIO(content), "application/json")}

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