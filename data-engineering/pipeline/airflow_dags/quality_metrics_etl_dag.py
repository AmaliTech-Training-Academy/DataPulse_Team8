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


def notify_pipeline_failure(context: dict) -> None:
    """Notify email and Slack with exact task failure details."""

    task_instance = context.get("task_instance")
    dag_id = task_instance.dag_id if task_instance else "unknown_dag"
    task_id = task_instance.task_id if task_instance else "unknown_task"
    run_id = context.get("run_id", "unknown_run_id")
    logical_date = context.get("logical_date")
    exception = context.get("exception")
    log_url = task_instance.log_url if task_instance else "N/A"

    failure_message = (
        "DataPulse ETL failure detected.\n"
        f"DAG: {dag_id}\n"
        f"Task: {task_id}\n"
        f"Run ID: {run_id}\n"
        f"Logical Date: {logical_date}\n"
        f"Error: {exception}\n"
        f"Log URL: {log_url}"
    )
    LOGGER.error(failure_message)

    email_targets = _variable_or_env("DE_ALERT_EMAILS", "de_alert_emails")
    if email_targets:
        recipients = [email.strip() for email in email_targets.split(",") if email.strip()]
        if recipients:
            try:
                send_email(
                    to=recipients,
                    subject=f"[DataPulse][Airflow] Failure in {dag_id}.{task_id}",
                    html_content=failure_message.replace("\n", "<br>"),
                )
                LOGGER.info("Email failure alert sent to %s", recipients)
            except Exception as email_error:
                LOGGER.exception("Email alert failed: %s", email_error)

    slack_webhook = _variable_or_env("SLACK_WEBHOOK_URL", "slack_webhook_url")
    if slack_webhook:
        try:
            _send_slack_alert(slack_webhook, failure_message)
        except Exception as slack_error:
            LOGGER.exception("Slack alert failed: %s", slack_error)
