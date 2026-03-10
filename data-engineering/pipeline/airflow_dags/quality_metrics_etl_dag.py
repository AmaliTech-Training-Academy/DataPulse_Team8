"""Airflow DAG for upload-triggered quality-metrics ETL."""

from __future__ import annotations

from datetime import datetime, timedelta
import json
import logging
import os
from pathlib import Path
import sys
from urllib import request

from airflow import DAG
from airflow.models import Variable
from airflow.operators.python import PythonOperator, ShortCircuitOperator
from airflow.utils.email import send_email

PIPELINE_DIR = Path(__file__).resolve().parents[1]
if str(PIPELINE_DIR) not in sys.path:
    sys.path.insert(0, str(PIPELINE_DIR))

from etl_pipeline import ETLPipeline  # noqa: E402

LOGGER = logging.getLogger(__name__)


def _variable_or_env(env_key: str, airflow_var_key: str) -> str:
    """Read config value from env var first, then Airflow Variable."""

    env_value = os.getenv(env_key, "").strip()
    if env_value:
        return env_value
    try:
        return Variable.get(airflow_var_key, default_var="").strip()
    except Exception:
        return ""


def _send_slack_alert(webhook_url: str, message: str) -> None:
    """Send a failure alert to Slack incoming webhook."""

    payload = json.dumps({"text": message}).encode("utf-8")
    req = request.Request(
        webhook_url,
        data=payload,
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    with request.urlopen(req, timeout=10):
        LOGGER.info("Slack failure alert delivered.")
