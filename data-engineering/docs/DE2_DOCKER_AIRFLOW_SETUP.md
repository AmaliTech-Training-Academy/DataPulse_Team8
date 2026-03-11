# DE2 Setup Guide: Run ETL + Airflow via Docker Compose

## Goal
Run the DE1 ETL pipeline and monitor DAGs from Airflow UI on DE2 machine, using the project `docker-compose.yml` without affecting teammates who do not need Airflow.

## Important Design Choice
Airflow was added under a Docker Compose profile named `de`.

This means:
1. Normal team startup is unchanged:
`docker compose up -d`
2. DE-specific startup includes Airflow:
`docker compose --profile de up -d ...`

So other team members are not affected unless they explicitly enable profile `de`.

## Prerequisites
1. Docker Desktop running.
2. You are inside the repo root:
`DataPulse_Team8/`
3. Branch includes DE sync changes (transform/load/airflow files).

## Services Added for DE
1. `airflow-init` (one-time bootstrap)
2. `airflow-webserver` (UI on host port `8088`)
3. `airflow-scheduler` (runs DAGs)

Airflow DAG path mounted:
`./data-engineering/pipeline -> /opt/airflow/dags/pipeline`

## One-Time Initialization (first run on a machine)

### 1. Start shared dependencies
```bash
docker compose up -d db backend
```

### 2. Initialize Airflow metadata DB and admin user
```bash
docker compose --profile de run --rm airflow-init
```

This creates Airflow tables and admin user:
1. username: `admin`
2. password: `admin`

## Start Airflow Runtime
```bash
docker compose --profile de up -d airflow-webserver airflow-scheduler
```

Open Airflow UI:
`http://localhost:8088`

## Apply Analytics Schema (required for ETL tables/views)

Run from host if `psql` is installed:
```bash
psql "postgresql://datapulse:datapulse123@localhost:5432/datapulse" -f data-engineering/sql/analytics_schema.sql
psql "postgresql://datapulse:datapulse123@localhost:5432/datapulse" -f data-engineering/sql/seed_dim_date.sql
```

Or run via db container:
```bash
docker compose exec -T db psql -U datapulse -d datapulse < data-engineering/sql/analytics_schema.sql
docker compose exec -T db psql -U datapulse -d datapulse < data-engineering/sql/seed_dim_date.sql
```

## Run and Monitor DAG

### 1. Confirm DAG appears
In UI, search for:
`quality_metrics_etl_on_upload`

### 2. Unpause DAG
Toggle DAG from paused -> active.

### 3. Trigger run
Use Airflow UI "Trigger DAG" button.

### 4. Monitor tasks
Watch:
1. `wait_for_new_upload_data`
2. `execute_quality_metrics_etl`

## CLI Checks (optional)

List DAGs:
```bash
docker compose --profile de exec airflow-scheduler airflow dags list
```

Trigger DAG:
```bash
docker compose --profile de exec airflow-scheduler airflow dags trigger quality_metrics_etl_on_upload
```

List runs:
```bash
docker compose --profile de exec airflow-scheduler airflow dags list-runs -d quality_metrics_etl_on_upload
```

## Verify ETL Output for Dashboard
Check these objects in DB:
1. `etl_batch_runs`
2. `vw_dataset_latest_score`
3. `vw_daily_dataset_quality`
4. `vw_rule_failure_summary`

Example query:
```sql
SELECT id, pipeline_name, status, started_at, finished_at, rows_extracted, rows_loaded
FROM etl_batch_runs
ORDER BY id DESC
LIMIT 10;
```

## Configure Alerts (optional)
Airflow DAG supports failure notifications using:
1. `DE_ALERT_EMAILS`
2. `SLACK_WEBHOOK_URL`

Currently these are blank defaults in compose.
Set them in `docker-compose.yml` before startup if needed.

## Troubleshooting

1. Airflow UI not opening:
   1. Check service status:
   `docker compose --profile de ps`
   2. Check webserver logs:
   `docker compose --profile de logs --tail=200 airflow-webserver`

2. DAG not visible:
   1. Confirm files exist in branch:
   `data-engineering/pipeline/airflow_dags/quality_metrics_etl_dag.py`
   2. Restart scheduler/webserver:
   `docker compose --profile de restart airflow-scheduler airflow-webserver`

3. DB connection errors:
   1. Ensure `db` is healthy:
   `docker compose ps`
   2. Verify connection URL in compose:
   `postgresql://datapulse:datapulse123@db:5432/datapulse`

4. Existing external Airflow causes confusion:
   1. Stop old Airflow stack first, or
   2. Keep using this compose Airflow at `http://localhost:8088`.

## Stop Services

Stop only Airflow profile services:
```bash
docker compose --profile de stop airflow-webserver airflow-scheduler
```

Stop full stack:
```bash
docker compose down
```

## Team Workflow Recommendation
1. Merge DE sync PR to `developer`.
2. DE2 pulls `developer`.
3. DE2 follows this guide exactly.
4. DE2 builds Streamlit dashboard against analytics views, not raw source tables.
