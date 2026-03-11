"""All database queries for the dashboard, with 60s caching."""

from __future__ import annotations

import logging
import os
from datetime import datetime, timedelta, timezone
from pathlib import Path

import pandas as pd
import streamlit as st
from dotenv import load_dotenv
from sqlalchemy import create_engine, text
from sqlalchemy.exc import OperationalError, ProgrammingError

from config import DEFAULT_DB_URL

# ── Logging ───────────────────────────────────────────────────────────────────
LOG_DIR = Path(__file__).resolve().parent / "logs"
LOG_DIR.mkdir(parents=True, exist_ok=True)
LOG_FILE = LOG_DIR / f"dashboard_{datetime.now(timezone.utc).strftime('%Y%m%d')}.log"

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)-8s %(name)s  %(message)s",
    handlers=[
        logging.FileHandler(LOG_FILE, encoding="utf-8"),
        logging.StreamHandler(),
    ],
)
LOGGER = logging.getLogger("datapulse.dashboard")

# ── Load env ──────────────────────────────────────────────────────────────────
load_dotenv(Path(__file__).resolve().parents[2] / ".env")
load_dotenv(Path(__file__).resolve().parent / ".env")
DATABASE_URL = os.getenv("DATABASE_URL", DEFAULT_DB_URL)


# ── Engine ────────────────────────────────────────────────────────────────────
@st.cache_resource(show_spinner=False)
def get_engine():
    LOGGER.info("Creating DB engine → %s", DATABASE_URL.split("@")[-1])
    return create_engine(DATABASE_URL, pool_pre_ping=True,
                         connect_args={"connect_timeout": 10})


def _query(engine, sql: str, params: dict | None = None) -> pd.DataFrame:
    """Internal: execute SQL, return DataFrame, never raise to caller."""
    try:
        with engine.connect() as conn:
            r = conn.execute(text(sql), params or {})
            df = pd.DataFrame(r.fetchall(), columns=r.keys())
            LOGGER.info("SQL OK rows=%d sql=%.100s", len(df), sql.strip())
            return df
    except (OperationalError, ProgrammingError) as exc:
        LOGGER.error("SQL FAILED sql=%.100s error=%s", sql.strip(), exc)
        return pd.DataFrame()


# ── Cached loaders ────────────────────────────────────────────────────────────

@st.cache_data(ttl=60, show_spinner=False)
def load_all_datasets(_engine) -> pd.DataFrame:
    return _query(_engine, "SELECT id, name FROM dim_datasets ORDER BY name")


@st.cache_data(ttl=60, show_spinner=False)
def load_latest_scores(_engine, dataset_ids: list[int]) -> pd.DataFrame:
    where = "WHERE dataset_id = ANY(:ids)" if dataset_ids else ""
    params = {"ids": dataset_ids} if dataset_ids else {}
    return _query(
        _engine,
        f"""
        SELECT dataset_id, dataset_name, score,
               total_rules, passed_rules, failed_rules, checked_at
        FROM   vw_dataset_latest_score
        {where}
        ORDER  BY score DESC
        """,
        params,
    )


@st.cache_data(ttl=60, show_spinner=False)
def load_daily_trend(_engine, dataset_ids: list[int], days: int = 30) -> pd.DataFrame:
    where = "AND dataset_id = ANY(:ids)" if dataset_ids else ""
    params: dict = {"cutoff": datetime.now(timezone.utc) - timedelta(days=days)}
    if dataset_ids:
        params["ids"] = dataset_ids
    return _query(
        _engine,
        f"""
        SELECT dataset_id, dataset_name, full_date,
               avg_score, min_score, max_score, runs_count
        FROM   vw_daily_dataset_quality
        WHERE  full_date >= :cutoff
        {where}
        ORDER  BY full_date, dataset_name
        """,
        params,
    )


@st.cache_data(ttl=60, show_spinner=False)
def load_rule_failures(_engine, dataset_ids: list[int]) -> pd.DataFrame:
    if dataset_ids:
        sql = """
            SELECT r.rule_id, r.rule_name, r.rule_type, r.severity,
                   r.checks_count, r.failed_checks_count,
                   r.failed_rows_sum, r.check_failure_rate
            FROM   vw_rule_failure_summary r
            WHERE  EXISTS (
                SELECT 1 FROM fact_quality_checks fqc
                WHERE fqc.rule_id = r.rule_id
                  AND fqc.dataset_id = ANY(:ids)
            )
            ORDER BY r.failed_checks_count DESC
        """
        return _query(_engine, sql, {"ids": dataset_ids})
    return _query(
        _engine,
        """
        SELECT rule_id, rule_name, rule_type, severity,
               checks_count, failed_checks_count,
               failed_rows_sum, check_failure_rate
        FROM   vw_rule_failure_summary
        ORDER  BY failed_checks_count DESC
        """,
    )


@st.cache_data(ttl=60, show_spinner=False)
def load_etl_health(_engine, limit: int = 15) -> pd.DataFrame:
    return _query(
        _engine,
        """
        SELECT id, pipeline_name, status, started_at, finished_at,
               rows_extracted, rows_loaded, error_message,
               EXTRACT(EPOCH FROM (finished_at - started_at))::INT AS duration_s
        FROM   etl_batch_runs
        ORDER  BY started_at DESC
        LIMIT  :lim
        """,
        {"lim": limit},
    )
