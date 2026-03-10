"""Transformation logic for the quality-metrics ETL pipeline."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
import logging

import pandas as pd

from extract.extract_quality_metrics import ExtractedPayload

LOGGER = logging.getLogger(__name__)


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

