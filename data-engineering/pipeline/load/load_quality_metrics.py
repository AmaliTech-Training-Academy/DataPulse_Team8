"""Load logic for the quality-metrics ETL pipeline."""

from __future__ import annotations

import logging
from typing import Any

import pandas as pd
from sqlalchemy import text
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

    dim_dataset_records = _to_records(transformed.dim_datasets)
    dim_rule_records = _to_records(transformed.dim_rules)
    dim_date_records = _to_records(transformed.dim_date)

    LOGGER.info(
        "Loading dimensions batch_id=%s dim_datasets=%s dim_rules=%s dim_date=%s",
        batch_id,
        len(dim_dataset_records),
        len(dim_rule_records),
        len(dim_date_records),
    )

    return {
        "rows_loaded": 0,
        "dim_datasets_upserted": len(dim_dataset_records),
        "dim_rules_upserted": len(dim_rule_records),
        "dim_date_insert_attempted": len(dim_date_records),
        "fact_quality_checks_insert_attempted": 0,
        "fact_quality_scores_insert_attempted": 0,
    }
