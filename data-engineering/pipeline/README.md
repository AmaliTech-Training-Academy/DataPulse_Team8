# Data Engineering (Data Engineer 1 Focus)

## Objective
Own the analytics data model for DataPulse so reports and trends are fast, correct, and stable.

## Day 1 Focus (Setup and Foundation)
1. Finalize analytics schema with constraints and indexes.
2. Add ETL batch metadata tables for observability.
3. Define source-to-analytics schema contract.
4. Seed date dimension for trend analytics.
5. Confirm SQLAlchemy models align with the finalized schema.

## What Was Designed Today
The analytics schema in `sql/analytics_schema.sql` now includes:
1. `etl_batch_runs` for ETL run tracking and watermarks.
2. `dim_datasets` and `dim_rules` with strict quality constraints.
   1. Includes backend-aligned lineage fields:
      1. `dim_datasets.column_names`
      2. `dim_datasets.uploaded_by`
      3. `dim_rules.parameters`
      4. `dim_rules.created_by`
3. `dim_date` with full calendar attributes.
4. `fact_quality_checks` at rule-check granularity.
5. `fact_quality_scores` at dataset-run granularity.
6. Query-optimized indexes and convenience views:
   1. `vw_dataset_latest_score`
   2. `vw_daily_dataset_quality`
   3. `vw_rule_failure_summary`

Full table-by-table documentation is in:
`docs/analytics_schema_data_dictionary.md`

## Schema Contract

### Source Tables (owned by backend)
1. `datasets`
2. `validation_rules`
3. `users` (lineage reference for ownership fields)
4. `check_results`
5. `quality_scores`

### Analytics Tables (owned by data engineering)
1. `dim_datasets`
   1. Grain: one row per source dataset (`datasets.id`).
2. `dim_rules`
   1. Grain: one row per source validation rule (`validation_rules.id`).
3. `dim_date`
   1. Grain: one row per calendar date.
4. `fact_quality_checks`
   1. Grain: one row per source check result (`check_results.id`).
5. `fact_quality_scores`
   1. Grain: one row per source quality score (`quality_scores.id`).
6. `etl_batch_runs`
   1. Grain: one row per ETL execution batch.

## Why This Is Optimized
1. Trend queries are accelerated with `(dataset_id, checked_at DESC)` indexes.
2. Rule failure analysis is accelerated with `(rule_id, checked_at DESC)` and partial failed-only indexes.
3. Data integrity is enforced via `CHECK`, `FK`, and uniqueness constraints.
4. ETL lineage is preserved using source IDs and `etl_batch_id` references.
5. Ownership/config lineage is retained in dimensions for RBAC-aware analytics.

## Day 1 Execution Steps
1. Install requirements:
   1. `pip install -r data-engineering/requirements.txt`
2. Apply schema:
   1. `psql "$DATABASE_URL" -f data-engineering/sql/analytics_schema.sql`
3. Seed `dim_date`:
   1. `psql "$DATABASE_URL" -f data-engineering/sql/seed_dim_date.sql`
4. Validate objects:
   1. Confirm tables and views are present.
   2. Confirm indexes are created.
5. Run ETL smoke test:
   1. `python data-engineering/pipeline/etl_pipeline.py`

## Setup
`pip install -r requirements.txt`
