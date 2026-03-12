"""ETL Pipeline for DataPulse analytics."""

from __future__ import annotations

import logging
import os
from datetime import datetime, timezone
from typing import Optional

from dotenv import load_dotenv
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker

from extract.extract_quality_metrics import extract_quality_payload
from transform.transform_quality_metrics import transform_quality_payload
from load.load_quality_metrics import load_quality_payload

load_dotenv()

LOGGER = logging.getLogger(__name__)


class ETLPipeline:
    pipeline_name = "analytics_etl"

    def __init__(self, source_url=None, target_url=None):
        self.source_url = source_url or os.getenv(
            "SOURCE_DB_URL",
            "postgresql://datapulse:datapulse@localhost:5432/datapulse",
        )
        self.target_url = target_url or os.getenv("TARGET_DB_URL", self.source_url)
        self.source_engine = create_engine(self.source_url)
        self.target_engine = create_engine(self.target_url)
        self._Session = sessionmaker(bind=self.target_engine)

    # ── Watermark helpers ────────────────────────────────────────────────────

    def get_last_success_watermark(self) -> Optional[datetime]:
        """Return the target_watermark of the last successful batch run, or None."""
        sql = text(
            """
            SELECT target_watermark
            FROM etl_batch_runs
            WHERE pipeline_name = :name AND status = 'SUCCESS'
            ORDER BY finished_at DESC
            LIMIT 1
            """
        )
        with self.target_engine.connect() as conn:
            row = conn.execute(sql, {"name": self.pipeline_name}).fetchone()
        return row[0] if row else None

    def has_new_data_since_watermark(self, watermark: Optional[datetime]) -> bool:
        """Return True if check_results or quality_scores have rows newer than watermark."""
        if watermark is None:
            # No previous run — always process
            return True
        sql = text(
            """
            SELECT 1
            FROM (
                SELECT checked_at FROM check_results  WHERE checked_at > :wm
                UNION ALL
                SELECT checked_at FROM quality_scores WHERE checked_at > :wm
            ) src
            LIMIT 1
            """
        )
        with self.source_engine.connect() as conn:
            row = conn.execute(sql, {"wm": watermark}).fetchone()
        return row is not None

    # ── Batch tracking helpers ───────────────────────────────────────────────

    def _start_batch_run(self, watermark: Optional[datetime]) -> int:
        sql = text(
            """
            INSERT INTO etl_batch_runs
                (pipeline_name, started_at, status, source_watermark, rows_extracted, rows_loaded)
            VALUES
                (:name, :started_at, 'RUNNING', :wm, 0, 0)
            RETURNING id
            """
        )
        with self.target_engine.begin() as conn:
            row = conn.execute(
                sql,
                {
                    "name": self.pipeline_name,
                    "started_at": datetime.now(timezone.utc),
                    "wm": watermark,
                },
            ).fetchone()
        return row[0]

    def _finish_batch_success(
        self,
        batch_id: int,
        target_watermark: datetime,
        rows_extracted: int,
        rows_loaded: int,
    ) -> None:
        sql = text(
            """
            UPDATE etl_batch_runs
            SET status = 'SUCCESS',
                finished_at = :finished_at,
                target_watermark = :wm,
                rows_extracted = :extracted,
                rows_loaded = :loaded
            WHERE id = :id
            """
        )
        with self.target_engine.begin() as conn:
            conn.execute(
                sql,
                {
                    "finished_at": datetime.now(timezone.utc),
                    "wm": target_watermark,
                    "extracted": rows_extracted,
                    "loaded": rows_loaded,
                    "id": batch_id,
                },
            )

    def _finish_batch_failure(
        self, batch_id: int, rows_extracted: int, error: Exception
    ) -> None:
        sql = text(
            """
            UPDATE etl_batch_runs
            SET status = 'FAILED',
                finished_at = :finished_at,
                rows_extracted = :extracted,
                error_message = :err
            WHERE id = :id
            """
        )
        with self.target_engine.begin() as conn:
            conn.execute(
                sql,
                {
                    "finished_at": datetime.now(timezone.utc),
                    "extracted": rows_extracted,
                    "err": str(error)[:2000],
                    "id": batch_id,
                },
            )

    # ── Main run ─────────────────────────────────────────────────────────────

    def run(self, skip_if_no_new_data: bool = True) -> dict:
        """Extract, transform, and load quality metrics incrementally."""
        watermark = self.get_last_success_watermark()
        LOGGER.info("ETL run started. pipeline=%s watermark=%s", self.pipeline_name, watermark)

        if skip_if_no_new_data and not self.has_new_data_since_watermark(watermark):
            LOGGER.info("No new source data found after watermark. Skipping run.")
            return {"status": "SKIPPED", "watermark": watermark, "rows_extracted": 0, "rows_loaded": 0}

        batch_id = self._start_batch_run(watermark)
        rows_extracted = 0
        try:
            extracted = extract_quality_payload(self.source_engine, watermark)
            transformed = transform_quality_payload(extracted)
            rows_extracted = transformed.rows_extracted
            load_stats = load_quality_payload(self.target_engine, transformed, batch_id)
            rows_loaded = int(load_stats.get("rows_loaded", 0))

            effective_watermark = (
                transformed.target_watermark
                or watermark
                or datetime.now(timezone.utc)
            )
            self._finish_batch_success(
                batch_id=batch_id,
                target_watermark=effective_watermark,
                rows_extracted=rows_extracted,
                rows_loaded=rows_loaded,
            )
            summary = {
                "status": "SUCCESS",
                "batch_id": batch_id,
                "rows_extracted": rows_extracted,
                "rows_loaded": rows_loaded,
                "target_watermark": str(effective_watermark),
                "load_stats": load_stats,
            }
            LOGGER.info("ETL completed successfully: %s", summary)
            return summary
        except Exception as error:
            self._finish_batch_failure(
                batch_id=batch_id, rows_extracted=rows_extracted, error=error
            )
            LOGGER.exception("ETL failed at batch_id=%s", batch_id)
            raise


if __name__ == "__main__":
    pipeline = ETLPipeline()
    pipeline.run()
