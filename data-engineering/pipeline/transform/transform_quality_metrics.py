"""Transformation logic for the quality-metrics ETL pipeline."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
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


def transform_quality_payload(extracted: ExtractedPayload) -> TransformedPayload:
    """Transform extracted source data into analytics-ready dimensions and facts."""

    return TransformedPayload(
        dim_datasets=extracted.datasets.copy(),
        dim_rules=extracted.rules.copy(),
        dim_date=pd.DataFrame(),
        fact_quality_checks=extracted.checks.copy(),
        fact_quality_scores=extracted.scores.copy(),
        target_watermark=extracted.max_source_timestamp,
        rows_extracted=(
            len(extracted.datasets)
            + len(extracted.rules)
            + len(extracted.checks)
            + len(extracted.scores)
        ),
    )
