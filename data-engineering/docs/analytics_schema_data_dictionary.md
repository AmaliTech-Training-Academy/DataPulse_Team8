# DataPulse Analytics Schema and Data Dictionary

## Document Metadata
| Field | Value |
|---|---|
| Project | DataPulse |
| Domain | Data Engineering |
| Owner | Data Engineer 1 (Evans Ankomah) |
| Last Updated | 2026-03-09 |
| Scope | Day 1 analytics schema foundation |
| Source DDL | `data-engineering/sql/analytics_schema.sql` |

## Purpose
This document defines the analytics schema contract delivered on Day 1:
1. Logical data model and table grain.
2. Full data dictionary for analytics tables.
3. View definitions for backend/report consumption.
4. Index strategy for performance.
5. Source-to-analytics lineage.

## Logical Model
| Entity | Type | Grain | Primary Key | Notes |
|---|---|---|---|---|
| `etl_batch_runs` | Control | One row per ETL execution | `id` | ETL lineage, watermarks, run status |
| `dim_datasets` | Dimension | One row per source dataset | `id` | Mirrors `datasets.id` |
| `dim_rules` | Dimension | One row per source rule | `id` | Mirrors `validation_rules.id` |
| `dim_date` | Dimension | One row per calendar date | `date_key` | Shared date conformed dimension |
| `fact_quality_checks` | Fact | One row per source check result | `id` | Rule-level quality outcome |
| `fact_quality_scores` | Fact | One row per source quality score | `id` | Dataset-run quality summary |

## Source-to-Target Mapping Contract
| Source System Table | Target Analytics Object | Mapping Key |
|---|---|---|
| `datasets` | `dim_datasets` | `datasets.id -> dim_datasets.id` |
| `validation_rules` | `dim_rules` | `validation_rules.id -> dim_rules.id` |
| `check_results` | `fact_quality_checks` | `check_results.id -> source_check_result_id` |
| `quality_scores` | `fact_quality_scores` | `quality_scores.id -> source_quality_score_id` |

## Data Dictionary

### Table: `etl_batch_runs`
| Column | Data Type | Nullable | Key/Constraint | Description |
|---|---|---|---|---|
| `id` | `BIGSERIAL` | No | PK | Unique ETL batch identifier |
| `pipeline_name` | `VARCHAR(100)` | No | Default `'analytics_etl'` | Pipeline name |
| `started_at` | `TIMESTAMPTZ` | No | Default `NOW()` | Batch start timestamp |
| `finished_at` | `TIMESTAMPTZ` | Yes |  | Batch finish timestamp |
| `status` | `VARCHAR(20)` | No | Check in `RUNNING/SUCCESS/FAILED` | Batch state |
| `source_watermark` | `TIMESTAMPTZ` | Yes |  | Max source timestamp considered |
| `target_watermark` | `TIMESTAMPTZ` | Yes |  | Max target timestamp loaded |
| `rows_extracted` | `INTEGER` | No | Check `>= 0` | Count of extracted rows |
| `rows_loaded` | `INTEGER` | No | Check `>= 0` | Count of loaded rows |
| `error_message` | `TEXT` | Yes |  | Failure details if status is `FAILED` |

### Table: `dim_datasets`
| Column | Data Type | Nullable | Key/Constraint | Description |
|---|---|---|---|---|
| `id` | `INTEGER` | No | PK | Dataset business key from app DB |
| `name` | `VARCHAR(255)` | No |  | Dataset name |
| `file_type` | `VARCHAR(10)` | No | Check lower in `csv/json` | Uploaded file type |
| `row_count` | `INTEGER` | No | Default `0`, check `>= 0` | Dataset row count |
| `column_count` | `INTEGER` | No | Default `0`, check `>= 0` | Dataset column count |
| `uploaded_at` | `TIMESTAMPTZ` | No |  | Original upload timestamp |
| `status` | `VARCHAR(20)` | No | Check in `PENDING/VALIDATED/FAILED` | Dataset quality status |
| `first_seen_at` | `TIMESTAMPTZ` | No | Default `NOW()` | First observed in ETL |
| `last_seen_at` | `TIMESTAMPTZ` | No | Default `NOW()` | Last refreshed in ETL |

### Table: `dim_rules`
| Column | Data Type | Nullable | Key/Constraint | Description |
|---|---|---|---|---|
| `id` | `INTEGER` | No | PK | Rule business key from app DB |
| `name` | `VARCHAR(255)` | No |  | Rule name |
| `dataset_type` | `VARCHAR(100)` | No |  | Rule scope/group from source |
| `field_name` | `VARCHAR(255)` | No |  | Dataset field validated |
| `rule_type` | `VARCHAR(20)` | No | Check in `NOT_NULL/DATA_TYPE/RANGE/UNIQUE/REGEX` | Rule behavior class |
| `severity` | `VARCHAR(10)` | No | Check in `HIGH/MEDIUM/LOW` | Rule severity |
| `is_active` | `BOOLEAN` | No | Default `TRUE` | Active/inactive flag |
| `created_at` | `TIMESTAMPTZ` | No |  | Rule creation time in source |
| `first_seen_at` | `TIMESTAMPTZ` | No | Default `NOW()` | First observed in ETL |
| `last_seen_at` | `TIMESTAMPTZ` | No | Default `NOW()` | Last refreshed in ETL |

### Table: `dim_date`
| Column | Data Type | Nullable | Key/Constraint | Description |
|---|---|---|---|---|
| `date_key` | `INTEGER` | No | PK, check range | Surrogate key in `YYYYMMDD` format |
| `full_date` | `DATE` | No | Unique | Calendar date |
| `day_of_week` | `SMALLINT` | No | Check `1..7` | ISO day of week |
| `day_of_month` | `SMALLINT` | No | Check `1..31` | Day number in month |
| `day_of_year` | `SMALLINT` | No | Check `1..366` | Day number in year |
| `week_of_year` | `SMALLINT` | No | Check `1..53` | ISO week number |
| `month` | `SMALLINT` | No | Check `1..12` | Month number |
| `month_name` | `VARCHAR(12)` | No |  | Month name |
| `quarter` | `SMALLINT` | No | Check `1..4` | Quarter number |
| `year` | `SMALLINT` | No | Check `1900..2999` | Calendar year |
| `is_weekend` | `BOOLEAN` | No |  | Weekend indicator |

### Table: `fact_quality_checks`
| Column | Data Type | Nullable | Key/Constraint | Description |
|---|---|---|---|---|
| `id` | `BIGSERIAL` | No | PK | Fact row identifier |
| `source_check_result_id` | `INTEGER` | No | Unique | Source lineage to `check_results.id` |
| `dataset_id` | `INTEGER` | No | FK -> `dim_datasets.id` | Dataset dimension link |
| `rule_id` | `INTEGER` | No | FK -> `dim_rules.id` | Rule dimension link |
| `rule_type` | `VARCHAR(20)` | No | Check allowed rule types | Rule type snapshot |
| `severity` | `VARCHAR(10)` | No | Check `HIGH/MEDIUM/LOW` | Severity snapshot |
| `passed` | `BOOLEAN` | No |  | Rule pass/fail outcome |
| `failed_rows` | `INTEGER` | No | Default `0`, check `>= 0` | Count of failed rows |
| `total_rows` | `INTEGER` | No | Default `0`, check `>= 0` | Total rows evaluated |
| `failure_rate` | `NUMERIC(7,4)` | No | Check `0..1` | `failed_rows/total_rows` normalized |
| `score` | `NUMERIC(5,2)` | Yes | Check `0..100` | Optional dataset-level score snapshot |
| `details` | `TEXT` | Yes |  | Serialized diagnostic details |
| `checked_at` | `TIMESTAMPTZ` | No |  | Validation execution time |
| `date_key` | `INTEGER` | No | FK -> `dim_date.date_key` | Date dimension link |
| `etl_batch_id` | `BIGINT` | Yes | FK -> `etl_batch_runs.id` | ETL batch lineage |
| `etl_loaded_at` | `TIMESTAMPTZ` | No | Default `NOW()` | Load timestamp |

Additional row-level check constraints:
| Constraint | Rule |
|---|---|
| `failed_rows <= total_rows` | Prevent impossible row counts |

### Table: `fact_quality_scores`
| Column | Data Type | Nullable | Key/Constraint | Description |
|---|---|---|---|---|
| `id` | `BIGSERIAL` | No | PK | Fact row identifier |
| `source_quality_score_id` | `INTEGER` | No | Unique | Source lineage to `quality_scores.id` |
| `dataset_id` | `INTEGER` | No | FK -> `dim_datasets.id` | Dataset dimension link |
| `score` | `NUMERIC(5,2)` | No | Check `0..100` | Dataset quality score |
| `total_rules` | `INTEGER` | No | Default `0`, check `>= 0` | Rules considered in run |
| `passed_rules` | `INTEGER` | No | Default `0`, check `>= 0` | Rules passed |
| `failed_rules` | `INTEGER` | No | Default `0`, check `>= 0` | Rules failed |
| `checked_at` | `TIMESTAMPTZ` | No |  | Score execution time |
| `date_key` | `INTEGER` | No | FK -> `dim_date.date_key` | Date dimension link |
| `etl_batch_id` | `BIGINT` | Yes | FK -> `etl_batch_runs.id` | ETL batch lineage |
| `etl_loaded_at` | `TIMESTAMPTZ` | No | Default `NOW()` | Load timestamp |

Additional row-level check constraints:
| Constraint | Rule |
|---|---|
| `passed_rules + failed_rules = total_rules` | Enforce internal score consistency |

## Analytics Views

### View: `vw_dataset_latest_score`
| Output Column | Meaning |
|---|---|
| `dataset_id` | Dataset key |
| `dataset_name` | Dataset name |
| `score` | Latest known score for the dataset |
| `total_rules` | Total rules in latest run |
| `passed_rules` | Passed rules in latest run |
| `failed_rules` | Failed rules in latest run |
| `checked_at` | Timestamp of latest run |
| `date_key` | Date key of latest run |

Primary use: backend endpoint for latest dashboard cards and summary APIs.

### View: `vw_daily_dataset_quality`
| Output Column | Meaning |
|---|---|
| `dataset_id` | Dataset key |
| `dataset_name` | Dataset name |
| `date_key` | Date key |
| `full_date` | Calendar date |
| `avg_score` | Average score for that dataset/day |
| `min_score` | Minimum score for that dataset/day |
| `max_score` | Maximum score for that dataset/day |
| `runs_count` | Number of scoring runs that day |

Primary use: trend charts over time.

### View: `vw_rule_failure_summary`
| Output Column | Meaning |
|---|---|
| `rule_id` | Rule key |
| `rule_name` | Rule name |
| `rule_type` | Rule type |
| `severity` | Rule severity |
| `checks_count` | Number of checks observed |
| `failed_checks_count` | Number of failed checks |
| `failed_rows_sum` | Total failed rows across all checks |
| `check_failure_rate` | Failed checks divided by checks count |

Primary use: issue distribution and hotspot analysis.

## Index Catalog
| Index Name | Object | Key/Predicate | Purpose |
|---|---|---|---|
| `idx_dim_datasets_uploaded_at` | `dim_datasets` | `(uploaded_at)` | Time filtering on datasets |
| `idx_dim_datasets_status` | `dim_datasets` | `(status)` | Status filtering |
| `idx_dim_rules_type_severity` | `dim_rules` | `(rule_type, severity)` | Rule diagnostics |
| `idx_dim_date_full_date` | `dim_date` | `(full_date)` | Date joins/lookups |
| `idx_fact_checks_dataset_checked_at` | `fact_quality_checks` | `(dataset_id, checked_at DESC)` | Dataset trend scans |
| `idx_fact_checks_rule_checked_at` | `fact_quality_checks` | `(rule_id, checked_at DESC)` | Rule trend scans |
| `idx_fact_checks_date_key` | `fact_quality_checks` | `(date_key)` | Date aggregation |
| `idx_fact_checks_failed_only` | `fact_quality_checks` | Partial `WHERE passed = FALSE` | Fast failed-rule analysis |
| `idx_fact_scores_dataset_checked_at` | `fact_quality_scores` | `(dataset_id, checked_at DESC)` | Latest score retrieval |
| `idx_fact_scores_date_key` | `fact_quality_scores` | `(date_key)` | Daily trend aggregation |
| `idx_fact_scores_low_quality` | `fact_quality_scores` | Partial `WHERE score < 70` | Alert/threshold queries |

## Data Quality and Governance Rules
| Rule Category | Rule |
|---|---|
| Domain constraints | `rule_type`, `severity`, `status`, and `file_type` are constrained |
| Numeric validity | Scores and rates are bounded (`0..100`, `0..1`) |
| Count consistency | `failed_rows <= total_rows` and `passed_rules + failed_rules = total_rules` |
| Lineage integrity | Source IDs are stored uniquely in facts |
| Time consistency | All facts include `checked_at`, `date_key`, and `etl_loaded_at` |

## Refresh and SLA Contract
| Item | Contract |
|---|---|
| Load mode | Incremental-capable via source IDs and ETL watermarks |
| Freshness target | Near-real-time or scheduled batch, depending on orchestration |
| Late-arriving handling | Upsert dimensions; idempotent insert-by-source-id for facts |
| Consumer impact | Views should be treated as stable query interfaces for backend/reporting |

## Notes for Backend and QA
| Consumer | What to rely on |
|---|---|
| Backend | Use views for latest score, daily trend, and rule-failure summaries |
| QA | Validate metric logic using source-to-target ID lineage |
| DevOps | Track ETL health from `etl_batch_runs` |

## Change Log
| Date | Change |
|---|---|
| 2026-03-09 | Initial Day 1 schema documentation and full analytics data dictionary |
