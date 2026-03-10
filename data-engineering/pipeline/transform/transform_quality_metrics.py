"""Transformation logic for the quality-metrics ETL pipeline."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
import logging

import pandas as pd

from extract.extract_quality_metrics import ExtractedPayload

LOGGER = logging.getLogger(__name__)

ALLOWED_RULE_TYPES = {"NOT_NULL", "DATA_TYPE", "RANGE", "UNIQUE", "REGEX"}
ALLOWED_SEVERITY = {"HIGH", "MEDIUM", "LOW"}
ALLOWED_DATASET_STATUS = {"PENDING", "VALIDATED", "FAILED"}
ALLOWED_FILE_TYPES = {"csv", "json"}


@dataclass
class TransformedPayload:
    """Container for transformed DataFrames ready for load phase."""

    dim_datasets: pd.DataFrame
    dim_rules: pd.DataFrame
    dim_date: pd.DataFrame
    fact_quality_checks: pd.DataFrame
    fact_quality_scores: pd.DataFrame
    target_watermark: datetime | None
    rows_extracted: int


def _to_datetime(series: pd.Series) -> pd.Series:
    """Convert a pandas series to timezone-aware UTC datetime values."""

    return pd.to_datetime(series, errors="coerce", utc=True)


def _to_date_key(series: pd.Series) -> pd.Series:
    """Convert datetimes to integer date keys in YYYYMMDD format."""

    return pd.to_datetime(series, errors="coerce").dt.strftime("%Y%m%d").astype("Int64")


def _normalize_allowed(series: pd.Series, allowed: set[str], fallback: str, uppercase: bool = True) -> pd.Series:
    """Normalize values against an allow-list and fallback invalid values."""

    values = series.fillna(fallback).astype(str)
    if uppercase:
        values = values.str.upper()
    return values.where(values.isin(allowed), fallback)


def _build_dim_datasets(datasets: pd.DataFrame, loaded_at: datetime) -> pd.DataFrame:
    """Build dim_datasets payload."""

    if datasets.empty:
        return pd.DataFrame(
            columns=[
                "id",
                "name",
                "file_type",
                "row_count",
                "column_count",
                "column_names",
                "uploaded_by",
                "uploaded_at",
                "status",
                "first_seen_at",
                "last_seen_at",
            ]
        )

    frame = datasets.copy()
    frame["uploaded_at"] = _to_datetime(frame["uploaded_at"]).fillna(loaded_at)
    frame["file_type"] = frame["file_type"].fillna("csv").astype(str).str.lower()
    frame["file_type"] = frame["file_type"].where(frame["file_type"].isin(ALLOWED_FILE_TYPES), "csv")
    frame["status"] = _normalize_allowed(frame["status"], ALLOWED_DATASET_STATUS, "PENDING")
    frame["row_count"] = pd.to_numeric(frame["row_count"], errors="coerce").fillna(0).astype(int)
    frame["column_count"] = pd.to_numeric(frame["column_count"], errors="coerce").fillna(0).astype(int)
    frame["first_seen_at"] = frame["uploaded_at"]
    frame["last_seen_at"] = loaded_at
    return frame[
        [
            "id",
            "name",
            "file_type",
            "row_count",
            "column_count",
            "column_names",
            "uploaded_by",
            "uploaded_at",
            "status",
            "first_seen_at",
            "last_seen_at",
        ]
    ]


def _build_dim_rules(rules: pd.DataFrame, loaded_at: datetime) -> pd.DataFrame:
    """Build dim_rules payload."""

    if rules.empty:
        return pd.DataFrame(
            columns=[
                "id",
                "name",
                "dataset_type",
                "field_name",
                "rule_type",
                "parameters",
                "severity",
                "is_active",
                "created_by",
                "created_at",
                "first_seen_at",
                "last_seen_at",
            ]
        )

    frame = rules.copy()
    frame["created_at"] = _to_datetime(frame["created_at"]).fillna(loaded_at)
    frame["rule_type"] = _normalize_allowed(frame["rule_type"], ALLOWED_RULE_TYPES, "NOT_NULL")
    frame["severity"] = _normalize_allowed(frame["severity"], ALLOWED_SEVERITY, "MEDIUM")
    frame["is_active"] = frame["is_active"].fillna(True).astype(bool)
    frame["first_seen_at"] = frame["created_at"]
    frame["last_seen_at"] = loaded_at
    return frame[
        [
            "id",
            "name",
            "dataset_type",
            "field_name",
            "rule_type",
            "parameters",
            "severity",
            "is_active",
            "created_by",
            "created_at",
            "first_seen_at",
            "last_seen_at",
        ]
    ]


def _build_fact_quality_checks(checks: pd.DataFrame, loaded_at: datetime) -> pd.DataFrame:
    """Build fact_quality_checks payload."""

    if checks.empty:
        return pd.DataFrame(
            columns=[
                "source_check_result_id",
                "dataset_id",
                "rule_id",
                "rule_type",
                "severity",
                "passed",
                "failed_rows",
                "total_rows",
                "failure_rate",
                "score",
                "details",
                "checked_at",
                "date_key",
                "etl_loaded_at",
            ]
        )

    frame = checks.copy()
    frame["checked_at"] = _to_datetime(frame["checked_at"]).fillna(loaded_at)
    frame["rule_type"] = _normalize_allowed(frame["rule_type"], ALLOWED_RULE_TYPES, "NOT_NULL")
    frame["severity"] = _normalize_allowed(frame["severity"], ALLOWED_SEVERITY, "MEDIUM")
    frame["passed"] = frame["passed"].fillna(False).astype(bool)
    frame["failed_rows"] = pd.to_numeric(frame["failed_rows"], errors="coerce").fillna(0).astype(int).clip(lower=0)
    frame["total_rows"] = pd.to_numeric(frame["total_rows"], errors="coerce").fillna(0).astype(int).clip(lower=0)
    frame["failed_rows"] = frame[["failed_rows", "total_rows"]].min(axis=1)
    safe_total = frame["total_rows"].replace(0, pd.NA)
    frame["failure_rate"] = (frame["failed_rows"] / safe_total).fillna(0).clip(lower=0, upper=1).round(4)
    frame["score"] = pd.NA
    frame["date_key"] = _to_date_key(frame["checked_at"])
    frame["etl_loaded_at"] = loaded_at
    return frame[
        [
            "source_check_result_id",
            "dataset_id",
            "rule_id",
            "rule_type",
            "severity",
            "passed",
            "failed_rows",
            "total_rows",
            "failure_rate",
            "score",
            "details",
            "checked_at",
            "date_key",
            "etl_loaded_at",
        ]
    ]


def _build_fact_quality_scores(scores: pd.DataFrame, loaded_at: datetime) -> pd.DataFrame:
    """Build fact_quality_scores payload."""

    if scores.empty:
        return pd.DataFrame(
            columns=[
                "source_quality_score_id",
                "dataset_id",
                "score",
                "total_rules",
                "passed_rules",
                "failed_rules",
                "checked_at",
                "date_key",
                "etl_loaded_at",
            ]
        )

    frame = scores.copy()
    frame["checked_at"] = _to_datetime(frame["checked_at"]).fillna(loaded_at)
    frame["score"] = pd.to_numeric(frame["score"], errors="coerce").fillna(0).clip(lower=0, upper=100).round(2)
    frame["total_rules"] = pd.to_numeric(frame["total_rules"], errors="coerce").fillna(0).astype(int).clip(lower=0)
    frame["passed_rules"] = pd.to_numeric(frame["passed_rules"], errors="coerce").fillna(0).astype(int).clip(lower=0)
    frame["failed_rules"] = pd.to_numeric(frame["failed_rules"], errors="coerce").fillna(0).astype(int).clip(lower=0)
    invalid_mask = frame["passed_rules"] + frame["failed_rules"] != frame["total_rules"]
    frame.loc[invalid_mask, "failed_rules"] = (frame["total_rules"] - frame["passed_rules"]).clip(lower=0)
    frame["date_key"] = _to_date_key(frame["checked_at"])
    frame["etl_loaded_at"] = loaded_at
    return frame[
        [
            "source_quality_score_id",
            "dataset_id",
            "score",
            "total_rules",
            "passed_rules",
            "failed_rules",
            "checked_at",
            "date_key",
            "etl_loaded_at",
        ]
    ]


def _build_dim_date(fact_checks: pd.DataFrame, fact_scores: pd.DataFrame) -> pd.DataFrame:
    """Build dim_date payload from fact date keys present in the run."""

    keys = pd.Series(dtype="Int64")
    if not fact_checks.empty:
        keys = pd.concat([keys, fact_checks["date_key"]], ignore_index=True)
    if not fact_scores.empty:
        keys = pd.concat([keys, fact_scores["date_key"]], ignore_index=True)

    keys = keys.dropna().astype(int).drop_duplicates()
    if keys.empty:
        return pd.DataFrame(
            columns=[
                "date_key",
                "full_date",
                "day_of_week",
                "day_of_month",
                "day_of_year",
                "week_of_year",
                "month",
                "month_name",
                "quarter",
                "year",
                "is_weekend",
            ]
        )

    full_date = pd.to_datetime(keys.astype(str), format="%Y%m%d", errors="coerce")
    frame = pd.DataFrame({"date_key": keys.values, "full_date": full_date})
    frame = frame.dropna(subset=["full_date"]).sort_values("date_key")
    frame["day_of_week"] = frame["full_date"].dt.isocalendar().day.astype(int)
    frame["day_of_month"] = frame["full_date"].dt.day.astype(int)
    frame["day_of_year"] = frame["full_date"].dt.dayofyear.astype(int)
    frame["week_of_year"] = frame["full_date"].dt.isocalendar().week.astype(int)
    frame["month"] = frame["full_date"].dt.month.astype(int)
    frame["month_name"] = frame["full_date"].dt.strftime("%B")
    frame["quarter"] = frame["full_date"].dt.quarter.astype(int)
    frame["year"] = frame["full_date"].dt.year.astype(int)
    frame["is_weekend"] = frame["day_of_week"].isin([6, 7])
    frame["full_date"] = frame["full_date"].dt.date
    return frame


def transform_quality_payload(extracted: ExtractedPayload) -> TransformedPayload:
    """Transform extracted source data into analytics-ready dimensions and facts."""

    loaded_at = datetime.now(timezone.utc)
    dim_datasets = _build_dim_datasets(extracted.datasets, loaded_at)
    dim_rules = _build_dim_rules(extracted.rules, loaded_at)
    fact_quality_checks = _build_fact_quality_checks(extracted.checks, loaded_at)
    fact_quality_scores = _build_fact_quality_scores(extracted.scores, loaded_at)
    dim_date = _build_dim_date(fact_quality_checks, fact_quality_scores)
    rows_extracted = (
        len(extracted.datasets)
        + len(extracted.rules)
        + len(extracted.checks)
        + len(extracted.scores)
    )
    LOGGER.info(
        (
            "Transformation complete. dim_datasets=%s dim_rules=%s "
            "fact_checks=%s fact_scores=%s dim_date=%s rows_extracted=%s"
        ),
        len(dim_datasets),
        len(dim_rules),
        len(fact_quality_checks),
        len(fact_quality_scores),
        len(dim_date),
        rows_extracted,
    )
    return TransformedPayload(
        dim_datasets=dim_datasets,
        dim_rules=dim_rules,
        dim_date=dim_date,
        fact_quality_checks=fact_quality_checks,
        fact_quality_scores=fact_quality_scores,
        target_watermark=extracted.max_source_timestamp,
        rows_extracted=rows_extracted,
    )
