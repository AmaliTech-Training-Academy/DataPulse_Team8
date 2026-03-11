CREATE TABLE IF NOT EXISTS datasets (
    id SERIAL PRIMARY KEY,
    uploaded_at TIMESTAMPTZ
);

CREATE TABLE IF NOT EXISTS validation_rules (
    id SERIAL PRIMARY KEY,
    created_at TIMESTAMPTZ
);

CREATE TABLE IF NOT EXISTS check_results (
    id SERIAL PRIMARY KEY,
    checked_at TIMESTAMPTZ
);

CREATE TABLE IF NOT EXISTS quality_scores (
    id SERIAL PRIMARY KEY,
    checked_at TIMESTAMPTZ
);

