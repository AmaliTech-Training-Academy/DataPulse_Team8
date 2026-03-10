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
    checks_frame = transformed.fact_quality_checks.copy()
    scores_frame = transformed.fact_quality_scores.copy()
    if not checks_frame.empty:
        checks_frame["etl_batch_id"] = batch_id
    if not scores_frame.empty:
        scores_frame["etl_batch_id"] = batch_id
    fact_check_records = _to_records(checks_frame)
    fact_score_records = _to_records(scores_frame)

    LOGGER.info(
        (
            "Loading payload batch_id=%s dim_datasets=%s dim_rules=%s "
            "dim_date=%s fact_checks=%s fact_scores=%s"
        ),
        batch_id,
        len(dim_dataset_records),
        len(dim_rule_records),
        len(dim_date_records),
        len(fact_check_records),
        len(fact_score_records),
    )

    with target_engine.begin() as conn:
        if dim_dataset_records:
            conn.execute(
                text(
                    """
                    INSERT INTO dim_datasets (
                        id, name, file_type, row_count, column_count,
                        column_names, uploaded_by, uploaded_at, status,
                        first_seen_at, last_seen_at
                    )
                    VALUES (
                        :id, :name, :file_type, :row_count, :column_count,
                        :column_names, :uploaded_by, :uploaded_at, :status,
                        :first_seen_at, :last_seen_at
                    )
                    ON CONFLICT (id) DO UPDATE SET
                        name = EXCLUDED.name,
                        file_type = EXCLUDED.file_type,
                        row_count = EXCLUDED.row_count,
                        column_count = EXCLUDED.column_count,
                        column_names = EXCLUDED.column_names,
                        uploaded_by = EXCLUDED.uploaded_by,
                        uploaded_at = EXCLUDED.uploaded_at,
                        status = EXCLUDED.status,
                        first_seen_at = COALESCE(dim_datasets.first_seen_at, EXCLUDED.first_seen_at),
                        last_seen_at = EXCLUDED.last_seen_at
                    """
                ),
                dim_dataset_records,
            )

        if dim_rule_records:
            conn.execute(
                text(
                    """
                    INSERT INTO dim_rules (
                        id, name, dataset_type, field_name, rule_type, parameters,
                        severity, is_active, created_by, created_at, first_seen_at, last_seen_at
                    )
                    VALUES (
                        :id, :name, :dataset_type, :field_name, :rule_type, :parameters,
                        :severity, :is_active, :created_by, :created_at, :first_seen_at, :last_seen_at
                    )
                    ON CONFLICT (id) DO UPDATE SET
                        name = EXCLUDED.name,
                        dataset_type = EXCLUDED.dataset_type,
                        field_name = EXCLUDED.field_name,
                        rule_type = EXCLUDED.rule_type,
                        parameters = EXCLUDED.parameters,
                        severity = EXCLUDED.severity,
                        is_active = EXCLUDED.is_active,
                        created_by = EXCLUDED.created_by,
                        created_at = EXCLUDED.created_at,
                        first_seen_at = COALESCE(dim_rules.first_seen_at, EXCLUDED.first_seen_at),
                        last_seen_at = EXCLUDED.last_seen_at
                    """
                ),
                dim_rule_records,
            )

        if dim_date_records:
            conn.execute(
                text(
                    """
                    INSERT INTO dim_date (
                        date_key, full_date, day_of_week, day_of_month, day_of_year,
                        week_of_year, month, month_name, quarter, year, is_weekend
                    )
                    VALUES (
                        :date_key, :full_date, :day_of_week, :day_of_month, :day_of_year,
                        :week_of_year, :month, :month_name, :quarter, :year, :is_weekend
                    )
                    ON CONFLICT (date_key) DO NOTHING
                    """
                ),
                dim_date_records,
            )

    loaded = {
        "rows_loaded": 0,
        "dim_datasets_upserted": len(dim_dataset_records),
        "dim_rules_upserted": len(dim_rule_records),
        "dim_date_insert_attempted": len(dim_date_records),
        "fact_quality_checks_insert_attempted": 0,
        "fact_quality_scores_insert_attempted": 0,
    }
    LOGGER.info("Dimension load complete: %s", loaded)
    return loaded
