"""KPI card components — non-technical-friendly."""

from __future__ import annotations

import pandas as pd
import streamlit as st

from config import score_band


def _card(label: str, value: str, sub: str, tier: str) -> str:
    badge_labels = {
        "excellent": "Healthy",
        "good":      "On Track",
        "warning":   "Needs Attention",
        "critical":  "Action Required",
        "neutral":   "Info",
    }
    return f"""
<div class="kpi-card kpi-{tier}">
  <div class="kpi-label">{label}</div>
  <div class="kpi-value">{value}</div>
  <div class="kpi-sub">{sub}</div>
  <span class="kpi-badge badge-{tier}">{badge_labels.get(tier, '')}</span>
</div>
"""


def render_kpi_row(
    latest_df: pd.DataFrame,
    failure_df: pd.DataFrame,
    etl_df: pd.DataFrame,
) -> None:
    """Render the 5-card KPI strip."""
    avg_score = float(latest_df["score"].mean()) if not latest_df.empty else 0.0
    total_ds  = len(latest_df)
    failing   = int((latest_df["score"] < 60).sum()) if not latest_df.empty else 0
    total_checks  = int(failure_df["checks_count"].sum())     if not failure_df.empty else 0
    failed_checks = int(failure_df["failed_checks_count"].sum()) if not failure_df.empty else 0
    pass_pct  = f"{(1-failed_checks/total_checks)*100:.0f}% pass rate" if total_checks else "No runs yet"

    band = score_band(avg_score)
    tier = {
        "Excellent":   "excellent",
        "Good":        "good",
        "Needs Review":"warning",
        "Critical":    "critical",
    }.get(band["label"], "neutral")

    etl_status  = etl_df["status"].iloc[0] if not etl_df.empty else "N/A"
    etl_tier    = {"SUCCESS": "excellent", "RUNNING": "good", "FAILED": "critical"}.get(etl_status, "warning")
    last_run    = pd.to_datetime(etl_df["started_at"].max()).strftime("%H:%M UTC") if not etl_df.empty else "N/A"

    c1, c2, c3, c4, c5 = st.columns(5)
    cards = [
        (c1, ("Overall Data Quality", f"{avg_score:.0f}%", f"Across {total_ds} dataset(s)", tier)),
        (c2, ("Datasets Tracked", str(total_ds), "Actively monitored", "neutral")),
        (c3, ("Datasets Needing Help", str(failing), "Score below 60%", "critical" if failing else "excellent")),
        (c4, ("Checks Completed", f"{total_checks:,}", pass_pct, "good")),
        (c5, ("Pipeline Last Ran", last_run, f"Status: {etl_status}", etl_tier)),
    ]
    for col, (label, value, sub, t) in cards:
        with col:
            st.markdown(_card(label, value, sub, t), unsafe_allow_html=True)


def render_health_banner(latest_df: pd.DataFrame) -> None:
    """A plain-English summary banner at the top."""
    if latest_df.empty:
        return

    avg_score = float(latest_df["score"].mean())
    band = score_band(avg_score)
    tier = {
        "Excellent":   "excellent",
        "Good":        "good",
        "Needs Review":"warning",
        "Critical":    "critical",
    }.get(band["label"], "neutral")

    messages = {
        "excellent": (
            "Your data looks great!",
            f"All monitored datasets have a quality score above 90%. "
            f"The overall average is <strong>{avg_score:.1f}%</strong>. Keep it up!",
        ),
        "good": (
            "Your data is in good shape.",
            f"Most datasets are performing well with an average quality of <strong>{avg_score:.1f}%</strong>. "
            "A few minor issues may need attention.",
        ),
        "warning": (
            "Some datasets need your attention.",
            f"The average data quality is <strong>{avg_score:.1f}%</strong>. "
            "Please review the failing rules below and take corrective action.",
        ),
        "critical": (
            "Immediate action required!",
            "Several datasets are below acceptable quality thresholds. "
            f"The overall average is <strong>{avg_score:.1f}%</strong>. "
            "Check the failing rules section urgently.",
        ),
    }
    title, body = messages.get(tier, messages["good"])
    st.markdown(
        f"""
<div class="health-banner health-banner-{tier}">
  <div class="health-banner-text">
    <h3>{title}</h3>
    <p>{body}</p>
  </div>
</div>
        """,
        unsafe_allow_html=True,
    )
