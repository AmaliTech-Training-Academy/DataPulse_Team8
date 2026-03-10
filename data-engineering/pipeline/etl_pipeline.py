"""ETL Pipeline for DataPulse analytics."""

from __future__ import annotations

import os
from datetime import datetime, timezone
import logging
from typing import Optional

from dotenv import load_dotenv
from sqlalchemy import create_engine, text
import pandas as pd
from sqlalchemy.engine import Engine

from extract.extract_quality_metrics import extract_quality_payload
from load.load_quality_metrics import load_quality_payload
from transform.transform_quality_metrics import transform_quality_payload

load_dotenv()

LOGGER = logging.getLogger(__name__)


class ETLPipeline:
    def __init__(
        self,
        source_url: Optional[str] = None,
        target_url: Optional[str] = None,
        pipeline_name: str = "quality_metrics_airflow_etl",
    ) -> None:
        self.source_url = source_url or os.getenv(
            "SOURCE_DB_URL", "postgresql://datapulse:datapulse@localhost:5432/datapulse"
        )
        self.target_url = target_url or os.getenv("TARGET_DB_URL", self.source_url)
        self.pipeline_name = pipeline_name
        self.source_engine: Engine = create_engine(self.source_url, pool_pre_ping=True)
        self.target_engine: Engine = create_engine(self.target_url, pool_pre_ping=True)
        self.raw_data = None
        self.transformed_data = None

    def get_last_success_watermark(self) -> Optional[datetime]:
        """Read last successful target watermark for incremental extraction."""

        query = text(
            """
            SELECT MAX(target_watermark) AS last_watermark
            FROM etl_batch_runs
            WHERE pipeline_name = :pipeline_name
              AND status = 'SUCCESS'
            """
        )
        with self.target_engine.connect() as conn:
            watermark = conn.execute(query, {"pipeline_name": self.pipeline_name}).scalar()
        return watermark

    def has_new_data_since_watermark(self, watermark: Optional[datetime]) -> bool:
        """Check whether source data exists after a given watermark."""

        if watermark is None:
            return True

        query = text(
            """
            SELECT
                EXISTS (SELECT 1 FROM datasets WHERE uploaded_at > :watermark) OR
                EXISTS (SELECT 1 FROM validation_rules WHERE created_at > :watermark) OR
                EXISTS (SELECT 1 FROM check_results WHERE checked_at > :watermark) OR
                EXISTS (SELECT 1 FROM quality_scores WHERE checked_at > :watermark)
                AS has_new_data
            """
        )
        with self.source_engine.connect() as conn:
            has_new_data = conn.execute(query, {"watermark": watermark}).scalar()
        return bool(has_new_data)

    def _start_batch_run(self, source_watermark: Optional[datetime]) -> int:
        """Create RUNNING batch metadata row and return batch id."""

        query = text(
            """
            INSERT INTO etl_batch_runs (
                pipeline_name, started_at, status, source_watermark, rows_extracted, rows_loaded
            )
            VALUES (:pipeline_name, :started_at, 'RUNNING', :source_watermark, 0, 0)
            RETURNING id
            """
        )
        with self.target_engine.begin() as conn:
            batch_id = conn.execute(
                query,
                {
                    "pipeline_name": self.pipeline_name,
                    "started_at": datetime.now(timezone.utc),
                    "source_watermark": source_watermark,
                },
            ).scalar_one()
        return int(batch_id)

    def _finish_batch_success(
        self,
        batch_id: int,
        target_watermark: Optional[datetime],
        rows_extracted: int,
        rows_loaded: int,
    ) -> None:
        """Mark a batch as SUCCESS."""

        query = text(
            """
            UPDATE etl_batch_runs
            SET
                finished_at = :finished_at,
                status = 'SUCCESS',
                target_watermark = :target_watermark,
                rows_extracted = :rows_extracted,
                rows_loaded = :rows_loaded,
                error_message = NULL
            WHERE id = :batch_id
            """
        )
        with self.target_engine.begin() as conn:
            conn.execute(
                query,
                {
                    "finished_at": datetime.now(timezone.utc),
                    "target_watermark": target_watermark,
                    "rows_extracted": rows_extracted,
                    "rows_loaded": rows_loaded,
                    "batch_id": batch_id,
                },
            )

    def _finish_batch_failure(self, batch_id: int, rows_extracted: int, error: Exception) -> None:
        """Mark a batch as FAILED and persist error detail."""

        query = text(
            """
            UPDATE etl_batch_runs
            SET
                finished_at = :finished_at,
                status = 'FAILED',
                rows_extracted = :rows_extracted,
                error_message = :error_message
            WHERE id = :batch_id
            """
        )
        with self.target_engine.begin() as conn:
            conn.execute(
                query,
                {
                    "finished_at": datetime.now(timezone.utc),
                    "rows_extracted": rows_extracted,
                    "error_message": str(error)[:4000],
                    "batch_id": batch_id,
                },
            )

    def extract(self):
        """Extract check results from app DB - IMPLEMENTED."""
        query = """
            SELECT cr.id, cr.dataset_id, cr.rule_id, cr.passed,
                   cr.failed_rows, cr.total_rows, cr.checked_at,
                   vr.rule_type, vr.severity, d.name as dataset_name
            FROM check_results cr
            JOIN validation_rules vr ON cr.rule_id = vr.id
            JOIN datasets d ON cr.dataset_id = d.id
        """
        self.raw_data = pd.read_sql(query, self.source_engine)
        print(f"Extracted {len(self.raw_data)} records")
        return self.raw_data

    def transform(self):
        """Transform extracted data - TODO: Implement.

        Steps:
        1. Aggregate results by dataset_id
        2. Compute daily quality trends
        3. Calculate pass rates by rule_type
        4. Build dimension table data
        5. Store in self.transformed_data
        """
        # TODO: Implement transformation logic
        if self.raw_data is None:
            print("No data to transform. Run extract() first.")
            return None
        self.transformed_data = self.raw_data.copy()
        print("Transform: TODO - implement aggregation logic")
        return self.transformed_data

    def load(self):
        """Load transformed data into analytics tables - TODO: Implement.

        Steps:
        1. Upsert dim_datasets from unique datasets
        2. Upsert dim_rules from unique rules
        3. Populate dim_date with date range
        4. Insert fact_quality_checks records
        """
        # TODO: Implement load logic
        if self.transformed_data is None:
            print("No data to load. Run transform() first.")
            return
        print("Load: TODO - implement insert into analytics tables")

    def run(self, skip_if_no_new_data: bool = True) -> dict:
        """Run extract, transform, and load for quality metrics aggregation."""

        watermark = self.get_last_success_watermark()
        LOGGER.info("ETL run started. pipeline=%s watermark=%s", self.pipeline_name, watermark)

        if skip_if_no_new_data and not self.has_new_data_since_watermark(watermark):
            LOGGER.info("No new source data found after watermark. Skipping run.")
            return {
                "status": "SKIPPED",
                "pipeline_name": self.pipeline_name,
                "watermark": watermark,
                "rows_extracted": 0,
                "rows_loaded": 0,
            }

        batch_id = self._start_batch_run(watermark)
        rows_extracted = 0
        try:
            extracted = extract_quality_payload(self.source_engine, watermark)
            transformed = transform_quality_payload(extracted)
            rows_extracted = transformed.rows_extracted
            load_stats = load_quality_payload(self.target_engine, transformed, batch_id)
            rows_loaded = int(load_stats.get("rows_loaded", 0))

            self._finish_batch_success(
                batch_id=batch_id,
                target_watermark=transformed.target_watermark or watermark,
                rows_extracted=rows_extracted,
                rows_loaded=rows_loaded,
            )
            summary = {
                "status": "SUCCESS",
                "pipeline_name": self.pipeline_name,
                "batch_id": batch_id,
                "rows_extracted": rows_extracted,
                "rows_loaded": rows_loaded,
                "target_watermark": transformed.target_watermark,
                "load_stats": load_stats,
            }
            LOGGER.info("ETL completed successfully: %s", summary)
            return summary
        except Exception as error:
            self._finish_batch_failure(batch_id=batch_id, rows_extracted=rows_extracted, error=error)
            LOGGER.exception("ETL failed at batch_id=%s", batch_id)
            raise


if __name__ == "__main__":
    logging.basicConfig(
        level=os.getenv("ETL_LOG_LEVEL", "INFO"),
        format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
    )
    pipeline = ETLPipeline()
    result = pipeline.run(skip_if_no_new_data=False)
    LOGGER.info("Pipeline result: %s", result)
