"""Validation engine."""

import json
import logging

import pandas as pd

logger = logging.getLogger("datapulse.validation")


class ValidationEngine:
    """Runs data quality checks against a DataFrame."""

    def run_all_checks(self, df: pd.DataFrame, rules: list) -> list:
        """Run all validation checks. Returns list of result dicts."""
        logger.info(f"Starting validation engine. DataFrame length: {len(df)}, Rules count: {len(rules)}")
        results = []
        for rule in rules:
            logger.debug(f"Running rule {rule.id} ({rule.rule_type}) on field '{rule.field_name}'")
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
                logger.warning(f"Unknown rule_type encountered: {rule.rule_type}")
                result = {
                    "passed": False,
                    "failed_rows": 0,
                    "total_rows": len(df),
                    "details": f"Error: Unknown rule_type '{rule.rule_type}'",
                }

            result["rule_id"] = rule.id
            if not result["passed"]:
                logger.info(f"Rule {rule.id} failed: {result['details']}")
            results.append(result)

        logger.info(f"Validation engine completed {len(results)} checks.")
        return results

    def null_check(self, df: pd.DataFrame, field: str) -> dict:
        """Check for null values in a field."""
        if df.empty:
            return {
                "passed": False,
                "failed_rows": 0,
                "total_rows": 0,
                "details": f"Dataset is empty, cannot check nulls for '{field}'",
            }

        if field not in df.columns:
            logger.warning(f"null_check: Field '{field}' not found in dataset columns: {list(df.columns)}")
            return {
                "passed": False,
                "failed_rows": len(df),
                "total_rows": len(df),
                "details": f"Error: Field '{field}' not found in dataset",
            }

        null_count = int(df[field].isnull().sum())
        passed = (null_count == 0)

        details = "No null values found" if passed else f"Found {null_count} null value{'s' if null_count > 1 else ''} in '{field}'"
        if null_count == len(df):
            details = f"Column '{field}' is completely empty (100% null)"

        return {
            "passed": passed,
            "failed_rows": null_count,
            "total_rows": len(df),
            "details": details,
        }

    def type_check(self, df: pd.DataFrame, field: str, expected_type: str) -> dict:
        """Check data types. Attempts to cast the column to expected_type."""
        if df.empty:
            return {
                "passed": False,
                "failed_rows": 0,
                "total_rows": 0,
                "details": f"Dataset is empty, cannot perform type check for '{field}'",
            }

        if field not in df.columns:
            return {
                "passed": False,
                "failed_rows": len(df),
                "total_rows": len(df),
                "details": f"Error: Field '{field}' not found in dataset",
            }

        non_null_s = df[field].dropna()
        if non_null_s.empty:
            return {
                "passed": True,
                "failed_rows": 0,
                "total_rows": len(df),
                "details": f"Column '{field}' is entirely null, passing type check by default",
            }

        failed_count = 0
        if expected_type in ("int", "float", "numeric", "number"):
            cast = pd.to_numeric(non_null_s, errors="coerce")
            failed_count = int(cast.isnull().sum())
        elif expected_type in ("bool", "boolean"):
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
            "details": f"{failed_count} row{'s' if failed_count != 1 else ''} failed type casting to '{expected_type}' in '{field}'",
        }

    def range_check(self, df: pd.DataFrame, field: str, min_val: float, max_val: float) -> dict:
        """Check value ranges."""
        if df.empty:
            return {
                "passed": False,
                "failed_rows": 0,
                "total_rows": 0,
                "details": f"Dataset is empty, cannot perform range check for '{field}'",
            }

        if field not in df.columns:
            return {
                "passed": False,
                "failed_rows": len(df),
                "total_rows": len(df),
                "details": f"Error: Field '{field}' not found in dataset",
            }

        s = pd.to_numeric(df[field], errors="coerce").dropna()
        if s.empty:
            return {
                "passed": True,
                "failed_rows": 0,
                "total_rows": len(df),
                "details": f"Column '{field}' is entirely null or non-numeric, skipping range check",
            }

        failed_mask = pd.Series(False, index=s.index)
        if min_val is not None:
            failed_mask |= s < float(min_val)
        if max_val is not None:
            failed_mask |= s > float(max_val)

        failed_count = int(failed_mask.sum())
        range_str = f"[{min_val if min_val is not None else '-inf'}, {max_val if max_val is not None else 'inf'}]"

        return {
            "passed": failed_count == 0,
            "failed_rows": failed_count,
            "total_rows": len(df),
            "details": f"{failed_count} row{'s' if failed_count != 1 else ''} outside allowed range {range_str} in '{field}'",
        }

    def unique_check(self, df: pd.DataFrame, field: str) -> dict:
        """Check uniqueness."""
        if df.empty:
            return {
                "passed": False,
                "failed_rows": 0,
                "total_rows": 0,
                "details": f"Dataset is empty, cannot perform unique check for '{field}'",
            }

        if field not in df.columns:
            return {
                "passed": False,
                "failed_rows": len(df),
                "total_rows": len(df),
                "details": f"Error: Field '{field}' not found in dataset",
            }

        non_null_s = df[field].dropna()
        if non_null_s.empty:
            return {
                "passed": True,
                "failed_rows": 0,
                "total_rows": len(df),
                "details": f"Column '{field}' is entirely null, passing unique check by default",
            }

        duplicates = non_null_s.duplicated(keep=False)
        failed_count = int(duplicates.sum())

        return {
            "passed": failed_count == 0,
            "failed_rows": failed_count,
            "total_rows": len(df),
            "details": f"Found {failed_count} non-unique (duplicate) value{'s' if failed_count != 1 else ''} in '{field}'",
        }

    def regex_check(self, df: pd.DataFrame, field: str, pattern: str) -> dict:
        """Check regex pattern matching."""
        if df.empty:
            return {
                "passed": False,
                "failed_rows": 0,
                "total_rows": 0,
                "details": f"Dataset is empty, cannot perform regex check for '{field}'",
            }

        if field not in df.columns:
            return {
                "passed": False,
                "failed_rows": len(df),
                "total_rows": len(df),
                "details": f"Error: Field '{field}' not found in dataset",
            }

        non_null_s = df[field].dropna()
        if non_null_s.empty:
            return {
                "passed": True,
                "failed_rows": 0,
                "total_rows": len(df),
                "details": f"Column '{field}' is entirely null, passing regex check by default",
            }

        matched = non_null_s.astype(str).str.match(pattern)
        failed_count = int((~matched).sum())

        return {
            "passed": failed_count == 0,
            "failed_rows": failed_count,
            "total_rows": len(df),
            "details": f"{failed_count} value{'s' if failed_count != 1 else ''} failed to match regex pattern '{pattern}' in '{field}'",
        }
