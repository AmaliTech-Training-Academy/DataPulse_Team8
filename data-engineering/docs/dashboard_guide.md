# DataPulse Quality Dashboard Guide

A production-standard, modular Streamlit dashboard for monitoring data quality and ETL pipeline health.

## 🚀 Overview

The DataPulse Dashboard provides a professional, high-fidelity interface for both technical and non-technical stakeholders to monitor the health of the organization's data assets.

### Key Features

- **Data Quality Scorecards**: Real-time scores for individual datasets.
- **Trend Analysis**: Daily quality trends to identify regressions over time.
- **Rule Failure Breakdown**: Deep dive into specific validation failures (Null checks, Regex, etc.).
- **ETL Pipeline Health**: Monitoring of Airflow/ETL batch runs, success rates, and row counts.
- **Customizable Time Windows**: View data trends for the last 7, 14, 30, or 90 days.

---

## 🏗️ Architecture

The dashboard is built with a modular approach to ensure scalability and ease of maintenance:

- **`quality_dashboard.py`**: The thin entrypoint orchestrating all components.
- **`config.py`**: Centralized configuration for quality thresholds, score bands, and brand colors.
- **`styles.py`**: Custom premium CSS implementing glassmorphism, responsive grids, and professional typography.
- **`data/loaders.py`**: Database abstraction layer with logic for fetching metrics and handling 60-second caching.
- **`components/`**:
  - `kpi_cards.py`: The top-level metric strip and health banner.
  - `charts.py`: All Plotly visualizations (Gauges, Trends, Bar charts).
  - `dataset_cards.py`: The interactive grid showing individual dataset performance.
  - `etl_health.py`: Dedicated section for pipeline monitoring.
  - `sidebar.py`: Global filters and dashboard controls.

---

## 🛠️ Setup & Usage

### Prerequisites

- Python 3.9+
- Access to the `datapulse` PostgreSQL database.
- Environment variables configured (usually in root `.env`).

### Installation

From the project root:

```bash
pip install streamlit plotly pandas sqlalchemy psycopg2-binary
```

### Running the Dashboard

```bash
streamlit run data-engineering/dashboards/quality_dashboard.py
```

---

## 📊 Interpreting the Metrics

### Quality Score Bands

- **90% - 100%**: **Excellent** (Green) - Data is highly reliable.
- **75% - 89%**: **Good** (Blue) - Minor inconsistencies detected, but acceptable for most use cases.
- **60% - 74%**: **Needs Review** (Orange) - Significant quality issues; investigate specific rule failures.
- **< 60%**: **Critical** (Red) - High risk! Data should not be used for production decision-making.

### "What Does This Mean?" Section

For non-technical users, the dashboard generates a natural language summary located next to the dataset cards. It highlights:

- The highest and lowest-performing datasets.
- The most common failing validation rule.
- High-severity issues that require immediate attention.

---

## 📝 Logging

The dashboard maintains detailed logs for every session:

- **Location**: `data-engineering/dashboards/logs/`
- **Format**: `dashboard_YYYYMMDD.log`
- Contains: Database connection status, query execution times, and render events.
