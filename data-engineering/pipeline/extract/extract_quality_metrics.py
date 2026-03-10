"""Extraction logic for the quality-metrics ETL pipeline."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
import logging
from typing import Optional

import pandas as pd
from sqlalchemy import text
from sqlalchemy.engine import Engine

LOGGER = logging.getLogger(__name__)


@dataclass
class ExtractedPayload:
    """Container for all extracted source datasets used by ETL."""

    datasets: pd.DataFrame
    rules: pd.DataFrame
    checks: pd.DataFrame
    scores: pd.DataFrame
    max_source_timestamp: Optional[datetime]


def _max_checked_at(checks: pd.DataFrame, scores: pd.DataFrame) -> Optional[datetime]:
    """Return the latest source timestamp across incremental source tables."""

    checked_at_frames = []
    if "checked_at" in checks:
        checked_at_frames.append(pd.to_datetime(checks["checked_at"], errors="coerce"))
    if "checked_at" in scores:
        checked_at_frames.append(pd.to_datetime(scores["checked_at"], errors="coerce"))
    if not checked_at_frames:
        return None

    combined = pd.concat(checked_at_frames, ignore_index=True).dropna()
    if combined.empty:
        return None

    latest_value = combined.max()
    if isinstance(latest_value, pd.Timestamp):
        return latest_value.to_pydatetime()
    if isinstance(latest_value, datetime):
        return latest_value
    return None


def extract_quality_payload(source_engine: Engine, watermark: Optional[datetime]) -> ExtractedPayload:
    """Extract source rows required for analytics ETL.

    Args:
        source_engine: SQLAlchemy engine for source/operational database.
        watermark: Last successful ETL watermark for incremental extraction.
    """

    params = {"watermark": watermark}

    datasets = pd.read_sql(
        text(
            """
            SELECT
                d.id,
                d.name,
                d.file_type,
                COALESCE(d.row_count, 0) AS row_count,
                COALESCE(d.column_count, 0) AS column_count,
                d.column_names,
                d.uploaded_by,
                d.uploaded_at,
                d.status
            FROM datasets d
            ORDER BY d.id
            """
        ),
        source_engine,
        params=params,
    )

    rules = pd.read_sql(
        text(
            """
            SELECT
                vr.id,
                vr.name,
                vr.dataset_type,
                vr.field_name,
                vr.rule_type,
                vr.parameters,
                vr.severity,
                COALESCE(vr.is_active, TRUE) AS is_active,
                vr.created_by,
                vr.created_at
            FROM validation_rules vr
            ORDER BY vr.id
            """
        ),
        source_engine,
        params=params,
    )

    checks = pd.read_sql(
        text(
            """
            SELECT
                cr.id AS source_check_result_id,
                cr.dataset_id,
                cr.rule_id,
                cr.passed,
                COALESCE(cr.failed_rows, 0) AS failed_rows,
                COALESCE(cr.total_rows, 0) AS total_rows,
                cr.details,
                cr.checked_at,
                UPPER(COALESCE(vr.rule_type, 'NOT_NULL')) AS rule_type,
                UPPER(COALESCE(vr.severity, 'MEDIUM')) AS severity
            FROM check_results cr
            JOIN validation_rules vr ON vr.id = cr.rule_id
            WHERE (:watermark IS NULL OR cr.checked_at > :watermark)
            ORDER BY cr.checked_at, cr.id
            """
        ),
        source_engine,
        params=params,
    )

    scores = pd.read_sql(
        text(
            """
            SELECT
                qs.id AS source_quality_score_id,
                qs.dataset_id,
                qs.score,
                COALESCE(qs.total_rules, 0) AS total_rules,
                COALESCE(qs.passed_rules, 0) AS passed_rules,
                COALESCE(qs.failed_rules, 0) AS failed_rules,
                qs.checked_at
            FROM quality_scores qs
            WHERE (:watermark IS NULL OR qs.checked_at > :watermark)
            ORDER BY qs.checked_at, qs.id
            """
        ),
        source_engine,
        params=params,
    )

    max_source_timestamp = _max_checked_at(checks=checks, scores=scores)

    LOGGER.info(
        "Extracted datasets=%s rules=%s checks=%s scores=%s (watermark=%s, max_source_timestamp=%s)",
        len(datasets),
        len(rules),
        len(checks),
        len(scores),
        watermark,
        max_source_timestamp,
    )
    return ExtractedPayload(
        datasets=datasets,
        rules=rules,
        checks=checks,
        scores=scores,
        max_source_timestamp=max_source_timestamp,
    )
