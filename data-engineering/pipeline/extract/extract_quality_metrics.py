"""Extraction logic for the quality-metrics ETL pipeline."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Optional

import pandas as pd
from sqlalchemy.engine import Engine


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

    raise NotImplementedError("extract_quality_payload implementation pending.")

