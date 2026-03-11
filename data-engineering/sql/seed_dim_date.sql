-- Seed dim_date for analytics trends.
-- Adjust range if your historical/future window changes.

INSERT INTO dim_date (
    date_key,
    full_date,
    day_of_week,
    day_of_month,
    day_of_year,
    week_of_year,
    month,
    month_name,
    quarter,
    year,
    is_weekend
)
SELECT
    TO_CHAR(d::date, 'YYYYMMDD')::INTEGER AS date_key,
    d::date AS full_date,
    EXTRACT(ISODOW FROM d)::SMALLINT AS day_of_week,
    EXTRACT(DAY FROM d)::SMALLINT AS day_of_month,
    EXTRACT(DOY FROM d)::SMALLINT AS day_of_year,
    EXTRACT(WEEK FROM d)::SMALLINT AS week_of_year,
    EXTRACT(MONTH FROM d)::SMALLINT AS month,
    TO_CHAR(d::date, 'FMMonth')::VARCHAR(12) AS month_name,
    EXTRACT(QUARTER FROM d)::SMALLINT AS quarter,
    EXTRACT(YEAR FROM d)::SMALLINT AS year,
    CASE WHEN EXTRACT(ISODOW FROM d) IN (6, 7) THEN TRUE ELSE FALSE END AS is_weekend
FROM generate_series('2020-01-01'::date, '2035-12-31'::date, interval '1 day') AS d
ON CONFLICT (date_key) DO NOTHING;
