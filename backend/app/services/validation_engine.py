"""Validation engine - PARTIAL implementation."""

import json
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
                "details": f"Field {field} not found in dataset",
            }
        null_count = int(df[field].isnull().sum())
        return {
            "passed": null_count == 0,
            "failed_rows": null_count,
            "total_rows": len(df),
            "details": f"{null_count} null values found in {field}",
        }

    def type_check(self, df, field, expected_type):
        """Check data types.

        Attempts to cast the column to expected_type (int, float, date, bool).
        """
        if field not in df.columns:
            return {
                "passed": False,
                "failed_rows": len(df),
                "total_rows": len(df),
                "details": f"Field {field} not found",
            }

        failed_count = 0
        non_null_s = df[field].dropna()
        if expected_type in ("int", "float", "numeric", "number"):
            cast = pd.to_numeric(non_null_s, errors="coerce")
            failed_count = int(cast.isnull().sum())
        elif expected_type == "bool" or expected_type == "boolean":

            def is_bool(x):
                return str(x).lower() in ("true", "false", "1", "0", "yes", "no")

            failed_count = int((~non_null_s.apply(is_bool)).sum())
        elif expected_type in ("date", "datetime"):
            cast = pd.to_datetime(non_null_s, errors="coerce")
            failed_count = int(cast.isnull().sum())

        return {
            "passed": failed_count == 0,
            "failed_rows": failed_count,
            "total_rows": len(df),
            "details": f"{failed_count} rows failed type casting to {expected_type}",
        }

    def range_check(self, df, field, min_val, max_val):
        """Check value ranges."""
        if field not in df.columns:
            return {
                "passed": False,
                "failed_rows": len(df),
                "total_rows": len(df),
                "details": f"Field {field} not found",
            }

        s = pd.to_numeric(df[field], errors="coerce").dropna()

        failed_mask = pd.Series(False, index=s.index)
        if min_val is not None:
            failed_mask |= s < float(min_val)
        if max_val is not None:
            failed_mask |= s > float(max_val)

        failed_count = int(failed_mask.sum())

        return {
            "passed": failed_count == 0,
            "failed_rows": failed_count,
            "total_rows": len(df),
            "details": f"{failed_count} rows outside range [{min_val}, {max_val}]",
        }

    def unique_check(self, df, field):
        """Check uniqueness."""
        if field not in df.columns:
            return {
                "passed": False,
                "failed_rows": len(df),
                "total_rows": len(df),
                "details": f"Field {field} not found",
            }

        duplicates = df[field].duplicated(keep=False)
        failed_count = int(duplicates.sum())

        return {
            "passed": failed_count == 0,
            "failed_rows": failed_count,
            "total_rows": len(df),
            "details": f"{failed_count} non-unique values found in {field}",
        }

    def regex_check(self, df, field, pattern):
        """Check regex pattern matching."""
        if field not in df.columns:
            return {
                "passed": False,
                "failed_rows": len(df),
                "total_rows": len(df),
                "details": f"Field {field} not found",
            }

        non_null_s = df[field].dropna().astype(str)
        matched = non_null_s.str.match(pattern)
        failed_count = int((~matched).sum())

        return {
            "passed": failed_count == 0,
            "failed_rows": failed_count,
            "total_rows": len(df),
            "details": f"{failed_count} values failed to match pattern {pattern}",
        }
