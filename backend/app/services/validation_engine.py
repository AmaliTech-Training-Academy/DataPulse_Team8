"""Validation engine - FULLY IMPLEMENTED."""

import json
import re
import pandas as pd


class ValidationEngine:
    """Runs data quality checks against a DataFrame."""

    def run_all_checks(self, df: pd.DataFrame, rules: list) -> list:
        """Run all validation checks. Returns list of result dicts."""
        results = []
        for rule in rules:
            params = json.loads(rule.parameters) if rule.parameters else {}
            if rule.rule_type == "NOT_NULL":
                result = self.null_check(df, rule.field_name)
            elif rule.rule_type == "DATA_TYPE":
                result = self.type_check(
                    df, rule.field_name, params.get("expected_type", "str")
                )
            elif rule.rule_type == "RANGE":
                result = self.range_check(
                    df, rule.field_name, params.get("min"), params.get("max")
                )
            elif rule.rule_type == "UNIQUE":
                result = self.unique_check(df, rule.field_name)
            elif rule.rule_type == "REGEX":
                result = self.regex_check(
                    df, rule.field_name, params.get("pattern", "")
                )
            else:
                result = {
                    "passed": False,
                    "failed_rows": 0,
                    "total_rows": len(df),
                    "details": f"Unknown rule_type: {rule.rule_type}",
                }
            result["rule_id"] = rule.id
            results.append(result)
        return results

    def null_check(self, df: pd.DataFrame, field: str) -> dict:
        """Check for null values in a field."""
        if field not in df.columns:
            return {
                "passed": False,
                "failed_rows": len(df),
                "total_rows": len(df),
                "details": f"Field '{field}' not found in dataset",
            }
        null_count = int(df[field].isnull().sum())
        return {
            "passed": null_count == 0,
            "failed_rows": null_count,
            "total_rows": len(df),
            "details": f"{null_count} null values found in '{field}'",
        }

    def type_check(self, df: pd.DataFrame, field: str, expected_type: str) -> dict:
        """Check that all values can be cast to expected_type (int/float/str/bool)."""
        if field not in df.columns:
            return {
                "passed": False,
                "failed_rows": len(df),
                "total_rows": len(df),
                "details": f"Field '{field}' not found in dataset",
            }
        total = len(df)
        series = df[field].dropna()
        type_map = {
            "int": lambda v: int(str(v)),
            "float": lambda v: float(str(v)),
            "str": lambda v: str(v),
            "bool": lambda v: (
                (_ for _ in ()).throw(ValueError())
                if str(v).lower() not in ("true", "false", "1", "0")
                else True
            ),
        }
        if expected_type not in type_map:
            return {
                "passed": False,
                "failed_rows": 0,
                "total_rows": total,
                "details": f"Unknown type '{expected_type}'. Use: int, float, str, bool",
            }
        failed = 0
        for val in series:
            try:
                if expected_type == "bool":
                    if str(val).lower() not in ("true", "false", "1", "0"):
                        raise ValueError()
                elif expected_type == "int":
                    (
                        int(str(val).split(".")[0])
                        if "." in str(val)
                        and str(val).replace(".", "").replace("-", "").isdigit()
                        else int(str(val))
                    )
                elif expected_type == "float":
                    float(str(val))
            except (ValueError, TypeError):
                failed += 1
        return {
            "passed": failed == 0,
            "failed_rows": failed,
            "total_rows": total,
            "details": f"{failed} values in '{field}' cannot be cast to {expected_type}",
        }

    def range_check(self, df: pd.DataFrame, field: str, min_val, max_val) -> dict:
        """Check numeric values fall within [min_val, max_val] inclusive."""
        if field not in df.columns:
            return {
                "passed": False,
                "failed_rows": len(df),
                "total_rows": len(df),
                "details": f"Field '{field}' not found in dataset",
            }
        total = len(df)
        series = pd.to_numeric(df[field], errors="coerce")
        non_numeric = int(series.isna().sum()) - int(df[field].isna().sum())
        if non_numeric > 0:
            return {
                "passed": False,
                "failed_rows": non_numeric,
                "total_rows": total,
                "details": f"Field '{field}' contains non-numeric values",
            }
        valid = series.dropna()
        mask = pd.Series([False] * len(valid), index=valid.index)
        if min_val is not None:
            mask |= valid < float(min_val)
        if max_val is not None:
            mask |= valid > float(max_val)
        failed = int(mask.sum())
        bounds = f"min={min_val}, max={max_val}"
        return {
            "passed": failed == 0,
            "failed_rows": failed,
            "total_rows": total,
            "details": f"{failed} values in '{field}' outside range [{bounds}]",
        }

    def unique_check(self, df: pd.DataFrame, field: str) -> dict:
        """Check that all non-null values in a column are unique."""
        if field not in df.columns:
            return {
                "passed": False,
                "failed_rows": len(df),
                "total_rows": len(df),
                "details": f"Field '{field}' not found in dataset",
            }
        total = len(df)
        series = df[field].dropna()
        failed = int(series.duplicated(keep=False).sum())
        return {
            "passed": failed == 0,
            "failed_rows": failed,
            "total_rows": total,
            "details": f"{failed} duplicate values found in '{field}'",
        }

    def regex_check(self, df: pd.DataFrame, field: str, pattern: str) -> dict:
        """Check that all non-null values match a regex pattern."""
        if field not in df.columns:
            return {
                "passed": False,
                "failed_rows": len(df),
                "total_rows": len(df),
                "details": f"Field '{field}' not found in dataset",
            }
        try:
            compiled = re.compile(pattern)
        except re.error as e:
            return {
                "passed": False,
                "failed_rows": 0,
                "total_rows": len(df),
                "details": f"Invalid regex pattern '{pattern}': {e}",
            }
        total = len(df)
        series = df[field].dropna().astype(str)
        failed = int((~series.str.match(compiled)).sum())
        return {
            "passed": failed == 0,
            "failed_rows": failed,
            "total_rows": total,
            "details": f"{failed} values in '{field}' do not match pattern '{pattern}'",
        }
