"""Load logic for the quality-metrics ETL pipeline."""

from __future__ import annotations

import logging
from typing import Any

import pandas as pd
from sqlalchemy.engine import Engine

from transform.transform_quality_metrics import TransformedPayload

LOGGER = logging.getLogger(__name__)


def _to_records(frame: pd.DataFrame) -> list[dict[str, Any]]:
    """Convert DataFrame to SQL-safe records by mapping NaN/NaT to None."""

    if frame.empty:
        return []
    rows = frame.to_dict(orient="records")
    normalized_rows: list[dict[str, Any]] = []
    for row in rows:
        normalized: dict[str, Any] = {}
        for key, value in row.items():
            if isinstance(value, pd.Timestamp):
                normalized[key] = value.to_pydatetime()
            elif pd.isna(value):
                normalized[key] = None
            else:
                normalized[key] = value
        normalized_rows.append(normalized)
    return normalized_rows


def load_quality_payload(
    target_engine: Engine, transformed: TransformedPayload, batch_id: int
) -> dict[str, int]:
    """Load transformed data into analytics schema tables."""

    LOGGER.info("Load phase not fully wired yet. batch_id=%s", batch_id)
    _ = target_engine
    _ = transformed
    return {
        "rows_loaded": 0,
        "dim_datasets_upserted": 0,
        "dim_rules_upserted": 0,
        "dim_date_insert_attempted": 0,
        "fact_quality_checks_insert_attempted": 0,
        "fact_quality_scores_insert_attempted": 0,
    }

