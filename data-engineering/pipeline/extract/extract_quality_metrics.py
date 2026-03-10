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

    LOGGER.info("Extracted dimensions datasets=%s rules=%s", len(datasets), len(rules))
    return ExtractedPayload(
        datasets=datasets,
        rules=rules,
        checks=pd.DataFrame(),
        scores=pd.DataFrame(),
        max_source_timestamp=None,
    )
