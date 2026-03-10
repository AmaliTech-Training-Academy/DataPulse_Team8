# DataPulse Deployment Guide

This document covers the prerequisites, configuration, and steps required to deploy and run the DataPulse system.

## Prerequisites

- **Docker & Docker Compose**: Ensure you have Docker (20.10+) and Docker Compose (v2.0+) installed.
- **Python 3.11+**: Required for local development and running scripts outside of Docker.
- **Git**: For cloning the repository.

## Environment Variables

The following environment variables are used to configure the system. You can set them in a `.env` file in the root directory.

| Variable | Description | Default / Example |
|----------|-------------|-------------------|
| `DATABASE_URL` | Main application database connection string | `postgresql://datapulse:datapulse123@db:5432/datapulse` |
| `TEST_DATABASE_URL` | Database URL for running tests | `sqlite:///./test_datapulse.db` |
| `SECRET_KEY` | Secret key for JWT token generation | `change-me-in-production` |
| `SOURCE_DB_URL` | ETL source database connection string | Same as `DATABASE_URL` |
| `TARGET_DB_URL` | ETL target database connection string | Same as `DATABASE_URL` |

## Local Development vs. Production

### Local Development (with Docker)

To start the full system (DB, Backend, and Pipeline) for local development:

```bash
docker-compose up --build
```

- **Backend API**: [http://localhost:8000](http://localhost:8000)
- **API Documentation**: [http://localhost:8000/docs](http://localhost:8000/docs)
- **PgAdmin**: [http://localhost:5050](http://localhost:5050) (Login: `admin@datapulse.com` / `admin123`)

### Production

In production, ensure you:
1. Change the `SECRET_KEY` to a secure, random string.
2. Update `DATABASE_URL` to point to a managed database instance if not using the containerized Postgres.
3. Use a reverse proxy (like Nginx) for SSL termination.

## Running the ETL Pipeline Manually

The ETL pipeline runs automatically when the container starts, but you can trigger it manually while the system is running:

```bash
docker exec datapulse-pipeline python pipeline/etl_pipeline.py
```

## Accessing the Streamlit Dashboard

The Streamlit dashboard provides visualizations of the data quality metrics.

1. **Install dependencies**:
   ```bash
   pip install streamlit plotly pandas sqlalchemy psycopg2-binary
   ```

2. **Run the dashboard**:
   ```bash
   streamlit run data-engineering/dashboards/quality_dashboard.py
   ```

3. **Access**: By default, it will be available at [http://localhost:8501](http://localhost:8501).

*Note: The dashboard is currently a stub and may require further implementation of the visualization logic.*

## Running Tests

### Using Docker (Against Postgres)

```bash
docker-compose -f docker-compose.test.yml up --build --exit-code-from api_test
```

### Locally (Against SQLite)

```bash
cd backend
pytest tests/
```
