# DE2 Handoff Guide: How to Use DE1 ETL Output

## 1. Why this document exists
DE2 needs reliable analytics-ready tables/views to build the Streamlit dashboard.
This guide explains:
1. Which DE1 files are core and should be used.
2. Which temporary files should be ignored.
3. How to run ETL and verify data is ready for dashboard work.
4. Which analytics objects DE2 should query first.

Last validated: 2026-03-10.

## 2. What DE2 needs to start immediately
DE2 can start dashboard work as soon as these are true:
1. Analytics schema exists in Postgres.
2. At least one successful ETL run exists in `etl_batch_runs`.
3. Read access to analytics views is available.

Minimum objects DE2 needs:
1. `vw_dataset_latest_score`
2. `vw_daily_dataset_quality`
3. `vw_rule_failure_summary`
4. `etl_batch_runs` (for pipeline freshness/health status)

## 3. Core files DE2 should use (keep)
These are part of the deliverable and should be relied on.

1. `data-engineering/sql/analytics_schema.sql`
Purpose:
Defines analytics tables, constraints, indexes, and dashboard-friendly views.

2. `data-engineering/sql/seed_dim_date.sql`
Purpose:
Seeds `dim_date` so time-series queries always have date dimension support.

3. `data-engineering/pipeline/etl_pipeline.py`
Purpose:
Main ETL orchestration class (`ETLPipeline`) with:
1. watermark logic
2. batch run tracking (`etl_batch_runs`)
3. extract -> transform -> load execution
4. failure capture and logging

4. `data-engineering/pipeline/extract/extract_quality_metrics.py`
Purpose:
Reads source tables (`datasets`, `validation_rules`, `check_results`, `quality_scores`) and applies watermark filtering.

5. `data-engineering/pipeline/transform/transform_quality_metrics.py`
Purpose:
Builds analytics-ready payloads:
1. `dim_datasets`
2. `dim_rules`
3. `dim_date`
4. `fact_quality_checks`
5. `fact_quality_scores`

6. `data-engineering/pipeline/load/load_quality_metrics.py`
Purpose:
Loads transformed payload with idempotent write behavior:
1. upsert dimensions
2. insert facts by source lineage IDs (`ON CONFLICT DO NOTHING`)

7. `data-engineering/pipeline/airflow_dags/quality_metrics_etl_dag.py`
Purpose:
Airflow DAG orchestration with:
1. upload-aware short-circuit check
2. retries and timeout controls
3. email and Slack alerts on task failure

8. `data-engineering/docs/analytics_schema_data_dictionary.md`
Purpose:
Column-level definitions and business meaning for analytics objects.

## 4. Temporary/debug files to ignore (not part of DE2 contract)
These files were created only to validate ETL in a separate local Airflow stack and should not be used as dashboard dependencies.

1. `data-engineering/tmp/airflow/airflow-env.override.yml`
Why ignore:
Local container override for one troubleshooting environment.
Not a stable project contract file.

2. `data-engineering/tmp/airflow/quality_metrics_etl_wrapper.py`
Why ignore:
Temporary DAG wrapper to load DAG in a different container layout.
Not needed when using repository DAG path directly.

3. `data-engineering/tmp/airflow/quality_airflowignore.txt`
Why ignore:
Temporary ignore pattern used to avoid duplicate DAG-ID loading during troubleshooting.

4. `data-engineering/tmp/sql/source_min_tables.sql`
Why ignore:
Temporary bootstrap script to create missing source tables in an external local DB.
Not required when backend source schema already exists.

5. `data-engineering/tmp/sql/source_required_columns.sql`
Why ignore:
Temporary ALTER script to patch missing source columns in that same local troubleshooting DB.

6. `data-engineering/tmp/runtime/test.db`
Why ignore:
Local sqlite artifact, not part of analytics deployment.

7. `data-engineering/tmp/runtime/uploads/`
Why ignore:
Local runtime artifact from app upload flow, not an analytics schema dependency.

8. `data-engineering/docs/reviews/PR41_REVIEW_COMMENTS.md`
Why ignore:
Review notes artifact, unrelated to ETL runtime or dashboard data contract.

## 5. ETL data contract for DE2 dashboard

### Source tables read by ETL
1. `datasets`
2. `validation_rules`
3. `check_results`
4. `quality_scores`

### Target analytics tables loaded by ETL
1. `dim_datasets`
2. `dim_rules`
3. `dim_date`
4. `fact_quality_checks`
5. `fact_quality_scores`
6. `etl_batch_runs` (run metadata)

### Recommended stable query layer for Streamlit
Use views first to reduce dashboard query complexity:
1. `vw_dataset_latest_score`
2. `vw_daily_dataset_quality`
3. `vw_rule_failure_summary`

## 6. Quick start for DE2

### Step A: Apply schema and seed date dimension
```bash
psql "$DATABASE_URL" -f data-engineering/sql/analytics_schema.sql
psql "$DATABASE_URL" -f data-engineering/sql/seed_dim_date.sql
```

### Step B: Run ETL once (local smoke run)
```bash
python data-engineering/pipeline/etl_pipeline.py
```

### Step C: Validate ETL produced/updated data
```sql
SELECT id, pipeline_name, status, started_at, finished_at, rows_extracted, rows_loaded
FROM etl_batch_runs
ORDER BY id DESC
LIMIT 5;
```

Expected:
1. Latest batch has `status = 'SUCCESS'`.
2. `rows_extracted` and `rows_loaded` are non-negative.

### Step D: Streamlit-ready checks
```sql
SELECT COUNT(*) FROM vw_dataset_latest_score;
SELECT COUNT(*) FROM vw_daily_dataset_quality;
SELECT COUNT(*) FROM vw_rule_failure_summary;
```

If these return rows (or expected empty when no source data yet), DE2 can proceed with dashboard UI implementation.

## 7. Suggested dashboard query map for DE2

1. KPI cards:
```sql
SELECT COUNT(*) AS dataset_count FROM dim_datasets;
SELECT AVG(score) AS avg_latest_score FROM vw_dataset_latest_score;
SELECT COUNT(*) FILTER (WHERE score < 70) AS low_quality_datasets
FROM vw_dataset_latest_score;
```

2. Quality trend chart:
```sql
SELECT full_date, dataset_name, avg_score
FROM vw_daily_dataset_quality
ORDER BY full_date, dataset_name;
```

3. Rule failure chart:
```sql
SELECT rule_name, rule_type, severity, failed_checks_count, check_failure_rate
FROM vw_rule_failure_summary
ORDER BY failed_checks_count DESC
LIMIT 20;
```

4. Pipeline health widget:
```sql
SELECT pipeline_name, status, started_at, finished_at, error_message
FROM etl_batch_runs
ORDER BY id DESC
LIMIT 10;
```

## 8. Airflow usage notes for DE2
DAG file:
`data-engineering/pipeline/airflow_dags/quality_metrics_etl_dag.py`

What it does:
1. Polls for new source data using watermark logic.
2. Executes ETL only when new data exists.
3. Uses retries with exponential backoff.
4. Sends failure details to:
- email (`DE_ALERT_EMAILS` or Airflow variable `de_alert_emails`)
- Slack webhook (`SLACK_WEBHOOK_URL` or Airflow variable `slack_webhook_url`)

## 9. What DE2 should not block on
DE2 does not need to wait for every team to finish.
DE2 can start once this contract is available:
1. schema is applied
2. ETL runs successfully at least once
3. views return data structure expected by dashboard queries

Even if source tables are still sparse, DE2 can build UI/components with empty-state handling against the same analytics views.

## 10. Final checklist before DE2 starts dashboard coding
1. Schema applied with no SQL errors.
2. `etl_batch_runs` has at least one `SUCCESS`.
3. Dashboard views are queryable.
4. DE2 has DB read credentials.
5. Temporary/debug files listed in section 4 are not used as dependencies.
