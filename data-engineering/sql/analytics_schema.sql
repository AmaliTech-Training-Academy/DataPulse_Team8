-- DataPulse Analytics Schema (Day 1 foundation)
-- Target: PostgreSQL 15+
-- Purpose:
--   1) Support fast trend and reporting queries
--   2) Preserve lineage to source application tables
--   3) Enable incremental ETL with batch metadata

BEGIN;

-- Track ETL runs for observability and incremental loading.
CREATE TABLE IF NOT EXISTS etl_batch_runs (
    id BIGSERIAL PRIMARY KEY,
    pipeline_name VARCHAR(100) NOT NULL DEFAULT 'analytics_etl',
    started_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    finished_at TIMESTAMPTZ,
    status VARCHAR(20) NOT NULL CHECK (status IN ('RUNNING', 'SUCCESS', 'FAILED')),
    source_watermark TIMESTAMPTZ,
    target_watermark TIMESTAMPTZ,
    rows_extracted INTEGER NOT NULL DEFAULT 0 CHECK (rows_extracted >= 0),
    rows_loaded INTEGER NOT NULL DEFAULT 0 CHECK (rows_loaded >= 0),
    error_message TEXT
);

CREATE TABLE IF NOT EXISTS dim_datasets (
    -- Same key as source app table: datasets.id
    id INTEGER PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    file_type VARCHAR(10) NOT NULL CHECK (LOWER(file_type) IN ('csv', 'json')),
    row_count INTEGER NOT NULL DEFAULT 0 CHECK (row_count >= 0),
    column_count INTEGER NOT NULL DEFAULT 0 CHECK (column_count >= 0),
    -- Source field from datasets.column_names for schema lineage.
    column_names TEXT,
    -- Source field from datasets.uploaded_by (users.id in app DB).
    uploaded_by INTEGER,
    uploaded_at TIMESTAMPTZ NOT NULL,
    status VARCHAR(20) NOT NULL DEFAULT 'PENDING'
        CHECK (status IN ('PENDING', 'VALIDATED', 'FAILED')),
    first_seen_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    last_seen_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS dim_rules (
    -- Same key as source app table: validation_rules.id
    id INTEGER PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    dataset_type VARCHAR(100) NOT NULL,
    field_name VARCHAR(255) NOT NULL,
    rule_type VARCHAR(20) NOT NULL
        CHECK (rule_type IN ('NOT_NULL', 'DATA_TYPE', 'RANGE', 'UNIQUE', 'REGEX')),
    -- Source field from validation_rules.parameters (JSON string payload).
    parameters TEXT,
    severity VARCHAR(10) NOT NULL
        CHECK (severity IN ('HIGH', 'MEDIUM', 'LOW')),
    is_active BOOLEAN NOT NULL DEFAULT TRUE,
    -- Source field from validation_rules.created_by (users.id in app DB).
    created_by INTEGER,
    created_at TIMESTAMPTZ NOT NULL,
    first_seen_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    last_seen_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- Schema-alignment guardrails for existing environments.
ALTER TABLE dim_datasets
    ADD COLUMN IF NOT EXISTS column_names TEXT;
ALTER TABLE dim_datasets
    ADD COLUMN IF NOT EXISTS uploaded_by INTEGER;
ALTER TABLE dim_rules
    ADD COLUMN IF NOT EXISTS parameters TEXT;
ALTER TABLE dim_rules
    ADD COLUMN IF NOT EXISTS created_by INTEGER;

CREATE TABLE IF NOT EXISTS dim_date (
    -- yyyymmdd integer key, e.g. 20260309
    date_key INTEGER PRIMARY KEY CHECK (date_key BETWEEN 19000101 AND 29991231),
    full_date DATE NOT NULL UNIQUE,
    day_of_week SMALLINT NOT NULL CHECK (day_of_week BETWEEN 1 AND 7),
    day_of_month SMALLINT NOT NULL CHECK (day_of_month BETWEEN 1 AND 31),
    day_of_year SMALLINT NOT NULL CHECK (day_of_year BETWEEN 1 AND 366),
    week_of_year SMALLINT NOT NULL CHECK (week_of_year BETWEEN 1 AND 53),
    month SMALLINT NOT NULL CHECK (month BETWEEN 1 AND 12),
    month_name VARCHAR(12) NOT NULL,
    quarter SMALLINT NOT NULL CHECK (quarter BETWEEN 1 AND 4),
    year SMALLINT NOT NULL CHECK (year BETWEEN 1900 AND 2999),
    is_weekend BOOLEAN NOT NULL
);

-- Fact at rule-check granularity (one row per source check_results record).
CREATE TABLE IF NOT EXISTS fact_quality_checks (
    id BIGSERIAL PRIMARY KEY,
    source_check_result_id INTEGER NOT NULL UNIQUE,
    dataset_id INTEGER NOT NULL REFERENCES dim_datasets(id),
    rule_id INTEGER NOT NULL REFERENCES dim_rules(id),
    rule_type VARCHAR(20) NOT NULL
        CHECK (rule_type IN ('NOT_NULL', 'DATA_TYPE', 'RANGE', 'UNIQUE', 'REGEX')),
    severity VARCHAR(10) NOT NULL
        CHECK (severity IN ('HIGH', 'MEDIUM', 'LOW')),
    passed BOOLEAN NOT NULL,
    failed_rows INTEGER NOT NULL DEFAULT 0 CHECK (failed_rows >= 0),
    total_rows INTEGER NOT NULL DEFAULT 0 CHECK (total_rows >= 0),
    failure_rate NUMERIC(7,4) NOT NULL DEFAULT 0
        CHECK (failure_rate >= 0 AND failure_rate <= 1),
    -- Optional denormalized dataset-level score for easier blended analytics.
    score NUMERIC(5,2) CHECK (score >= 0 AND score <= 100),
    details TEXT,
    checked_at TIMESTAMPTZ NOT NULL,
    date_key INTEGER NOT NULL REFERENCES dim_date(date_key),
    etl_batch_id BIGINT REFERENCES etl_batch_runs(id),
    etl_loaded_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    CHECK (failed_rows <= total_rows)
);

-- Fact at dataset-run granularity (one row per source quality_scores record).
CREATE TABLE IF NOT EXISTS fact_quality_scores (
    id BIGSERIAL PRIMARY KEY,
    source_quality_score_id INTEGER NOT NULL UNIQUE,
    dataset_id INTEGER NOT NULL REFERENCES dim_datasets(id),
    score NUMERIC(5,2) NOT NULL CHECK (score >= 0 AND score <= 100),
    total_rules INTEGER NOT NULL DEFAULT 0 CHECK (total_rules >= 0),
    passed_rules INTEGER NOT NULL DEFAULT 0 CHECK (passed_rules >= 0),
    failed_rules INTEGER NOT NULL DEFAULT 0 CHECK (failed_rules >= 0),
    checked_at TIMESTAMPTZ NOT NULL,
    date_key INTEGER NOT NULL REFERENCES dim_date(date_key),
    etl_batch_id BIGINT REFERENCES etl_batch_runs(id),
    etl_loaded_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    CHECK (passed_rules + failed_rules = total_rules)
);

-- Dimension indexes.
CREATE INDEX IF NOT EXISTS idx_dim_datasets_uploaded_at ON dim_datasets(uploaded_at);
CREATE INDEX IF NOT EXISTS idx_dim_datasets_status ON dim_datasets(status);
CREATE INDEX IF NOT EXISTS idx_dim_datasets_uploaded_by ON dim_datasets(uploaded_by);
CREATE INDEX IF NOT EXISTS idx_dim_rules_type_severity ON dim_rules(rule_type, severity);
CREATE INDEX IF NOT EXISTS idx_dim_rules_created_by ON dim_rules(created_by);
CREATE INDEX IF NOT EXISTS idx_dim_date_full_date ON dim_date(full_date);

-- Fact indexes optimized for trend, latest-score, and issue analysis queries.
CREATE INDEX IF NOT EXISTS idx_fact_checks_dataset_checked_at
    ON fact_quality_checks(dataset_id, checked_at DESC);
CREATE INDEX IF NOT EXISTS idx_fact_checks_rule_checked_at
    ON fact_quality_checks(rule_id, checked_at DESC);
CREATE INDEX IF NOT EXISTS idx_fact_checks_date_key
    ON fact_quality_checks(date_key);
CREATE INDEX IF NOT EXISTS idx_fact_checks_failed_only
    ON fact_quality_checks(dataset_id, rule_id, checked_at DESC)
    WHERE passed = FALSE;

CREATE INDEX IF NOT EXISTS idx_fact_scores_dataset_checked_at
    ON fact_quality_scores(dataset_id, checked_at DESC);
CREATE INDEX IF NOT EXISTS idx_fact_scores_date_key
    ON fact_quality_scores(date_key);
CREATE INDEX IF NOT EXISTS idx_fact_scores_low_quality
    ON fact_quality_scores(dataset_id, checked_at DESC)
    WHERE score < 70;

-- Convenience views for downstream consumers (API/reporting/dashboard).
CREATE OR REPLACE VIEW vw_dataset_latest_score AS
SELECT DISTINCT ON (fqs.dataset_id)
    fqs.dataset_id,
    d.name AS dataset_name,
    fqs.score,
    fqs.total_rules,
    fqs.passed_rules,
    fqs.failed_rules,
    fqs.checked_at,
    fqs.date_key
FROM fact_quality_scores fqs
JOIN dim_datasets d ON d.id = fqs.dataset_id
ORDER BY fqs.dataset_id, fqs.checked_at DESC;

CREATE OR REPLACE VIEW vw_daily_dataset_quality AS
SELECT
    fqs.dataset_id,
    d.name AS dataset_name,
    fqs.date_key,
    dd.full_date,
    AVG(fqs.score)::NUMERIC(5,2) AS avg_score,
    MIN(fqs.score)::NUMERIC(5,2) AS min_score,
    MAX(fqs.score)::NUMERIC(5,2) AS max_score,
    COUNT(*) AS runs_count
FROM fact_quality_scores fqs
JOIN dim_datasets d ON d.id = fqs.dataset_id
JOIN dim_date dd ON dd.date_key = fqs.date_key
GROUP BY fqs.dataset_id, d.name, fqs.date_key, dd.full_date;

CREATE OR REPLACE VIEW vw_rule_failure_summary AS
SELECT
    fqc.rule_id,
    r.name AS rule_name,
    r.rule_type,
    r.severity,
    COUNT(*) AS checks_count,
    SUM(CASE WHEN fqc.passed THEN 0 ELSE 1 END) AS failed_checks_count,
    COALESCE(SUM(fqc.failed_rows), 0) AS failed_rows_sum,
    CASE
        WHEN COUNT(*) = 0 THEN 0
        ELSE ROUND((SUM(CASE WHEN fqc.passed THEN 0 ELSE 1 END)::NUMERIC / COUNT(*)), 4)
    END AS check_failure_rate
FROM fact_quality_checks fqc
JOIN dim_rules r ON r.id = fqc.rule_id
GROUP BY fqc.rule_id, r.name, r.rule_type, r.severity;

COMMIT;
