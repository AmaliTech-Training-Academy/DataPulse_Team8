"""ETL Pipeline for DataPulse analytics."""

import os
from datetime import datetime
from dotenv import load_dotenv
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
import pandas as pd

load_dotenv()


class ETLPipeline:
    def __init__(self, source_url=None, target_url=None):
        self.source_url = source_url or os.getenv("SOURCE_DB_URL",
            "postgresql://datapulse:datapulse@localhost:5432/datapulse")
        self.target_url = target_url or os.getenv("TARGET_DB_URL",
            self.source_url)
        self.source_engine = create_engine(self.source_url)
        self.target_engine = create_engine(self.target_url)
        self.raw_data = None
        self.transformed_data = None

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
                "target_watermark": effective_watermark,
                "load_stats": load_stats,
            }
            LOGGER.info("ETL completed successfully: %s", summary)
            return summary
        except Exception as error:
            self._finish_batch_failure(batch_id=batch_id, rows_extracted=rows_extracted, error=error)
            LOGGER.exception("ETL failed at batch_id=%s", batch_id)
            raise


if __name__ == "__main__":
    pipeline = ETLPipeline()
    pipeline.run()
