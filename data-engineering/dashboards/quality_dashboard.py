"""DataPulse Quality Dashboard — main entrypoint.

Run:
    streamlit run data-engineering/dashboards/quality_dashboard.py

The app is split into focused modules:
    config.py               — thresholds, colours, constants
    styles.py               — all custom CSS
    data/loaders.py         — SQL queries + caching + logging
    components/kpi_cards.py — KPI strip + health banner
    components/charts.py    — Plotly chart builders
    components/sidebar.py   — sidebar filters
    components/dataset_cards.py — dataset card grid + insights
    components/etl_health.py    — ETL health section
"""

from __future__ import annotations

import sys
from pathlib import Path

import streamlit as st
from sqlalchemy.exc import OperationalError

# Allow local imports from dashboards/
sys.path.insert(0, str(Path(__file__).resolve().parent))

import styles
from components import charts, dataset_cards, etl_health, kpi_cards, sidebar
from data import loaders

# ── Page config ───────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="DataPulse | Quality Dashboard",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded",
)
styles.inject()


def section(title: str, subtitle: str = "") -> None:
    sub_html = f'<span class="dp-section-sub"> — {subtitle}</span>' if subtitle else ""
    st.markdown(
        f"""
<div class="dp-section">
  <div class="dp-section-bar"></div>
  <span class="dp-section-title">{title}{sub_html}</span>
</div>
        """,
        unsafe_allow_html=True,
    )


def empty(icon: str, title: str, sub: str = "") -> None:
    st.markdown(
        f"""
<div class="dp-empty">
  <span class="dp-empty-icon">{icon}</span>
  <div class="dp-empty-title">{title}</div>
  <div class="dp-empty-sub">{sub}</div>
</div>
        """,
        unsafe_allow_html=True,
    )


# ── Main ──────────────────────────────────────────────────────────────────────
def main() -> None:
    # DB connection
    try:
        engine = loaders.get_engine()
        with engine.connect():
            pass
    except OperationalError as exc:
        st.error(
            "Cannot connect to the database.\n\n"
            "Make sure Docker is running and the database container is healthy.\n\n"
            f"```\n{exc}\n```"
        )
        loaders.LOGGER.critical("DB connection failed: %s", exc)
        st.stop()

    # Sidebar
    selected_ids, day_window = sidebar.render(engine)

    # Hero banner
    st.markdown(
        """
<div class="dp-hero">
  <h1>Data Quality Intelligence</h1>
  <p>Real-time monitoring for your production data pipeline · Powered by DataPulse ETL</p>
</div>
        """,
        unsafe_allow_html=True,
    )

    # Load all data
    latest_df  = loaders.load_latest_scores(engine, selected_ids)
    trend_df   = loaders.load_daily_trend(engine, selected_ids, day_window)
    failure_df = loaders.load_rule_failures(engine, selected_ids)
    etl_df     = loaders.load_etl_health(engine)

    # ── Plain-English health banner ───────────────────────────────────────────
    kpi_cards.render_health_banner(latest_df)

    # ── KPI cards ─────────────────────────────────────────────────────────────
    section("At a Glance", "Key numbers")
    kpi_cards.render_kpi_row(latest_df, failure_df, etl_df)

    st.write("")

    # ── Gauge + Trend ─────────────────────────────────────────────────────────
    section("Quality Score Trend", f"Last {day_window} days")
    col_gauge, col_trend = st.columns([1, 3])

    with col_gauge:
        if not latest_df.empty:
            avg_score = float(latest_df["score"].mean())
            st.plotly_chart(charts.score_gauge(avg_score), use_container_width=True)
        else:
            empty("", "No score data yet")

    with col_trend:
        if not trend_df.empty:
            st.plotly_chart(charts.trend_line(trend_df), use_container_width=True)
        else:
            empty(
                "", "No trend data yet",
                "Upload a dataset → create validation rules → run a check to generate scores.",
            )

    # ── Dataset cards ─────────────────────────────────────────────────────────
    col_cards, col_insights = st.columns([2, 1])

    with col_cards:
        section("Dataset Health", "Per-dataset quality scores")
        dataset_cards.render_dataset_cards(latest_df)

    with col_insights:
        section("What Does This Mean?", "Plain-English summary")
        st.write("")
        dataset_cards.render_insights(failure_df, latest_df)

    # ── Rule failures ─────────────────────────────────────────────────────────
    has_failures = not failure_df.empty and failure_df["failed_checks_count"].sum() > 0
    section("Rule Failure Analysis", "What's going wrong and why")

    col_bar, col_donut = st.columns([2, 1])

    with col_bar:
        if has_failures:
            st.plotly_chart(charts.rule_failure_bar(failure_df), use_container_width=True)
        else:
            empty("", "System Health Stable", "All validation checks are currently passing.")

    with col_donut:
        if has_failures:
            st.plotly_chart(charts.severity_donut(failure_df), use_container_width=True)
        else:
            empty("", "Global Check Health")

    # Detailed failure table
    if has_failures:
        with st.expander("Detailed Rule Failure Table", expanded=False):
            tbl = failure_df.copy()
            tbl["Failure Rate"]  = tbl["check_failure_rate"].map(lambda r: f"{r*100:.1f}%")
            tbl["Severity"] = tbl["severity"].map(
                lambda s: {"HIGH": "HIGH", "MEDIUM": "MEDIUM", "LOW": "LOW"}.get(s, s)
            )
            st.dataframe(
                tbl[["rule_name", "rule_type", "Severity",
                     "checks_count", "failed_checks_count",
                     "failed_rows_sum", "Failure Rate"]].rename(columns={
                    "rule_name": "Rule Name",
                    "rule_type": "Rule Type",
                    "checks_count": "Total Checks",
                    "failed_checks_count": "Failed",
                    "failed_rows_sum": "Rows Affected",
                }),
                use_container_width=True,
                hide_index=True,
            )

    # ── ETL pipeline health ───────────────────────────────────────────────────
    section("Pipeline Health", "How the data processing engine is performing")
    etl_health.render_etl_health(etl_df)

    # ── Footer ────────────────────────────────────────────────────────────────
    st.divider()
    st.markdown(
        f"<div style='text-align:center;font-size:.75rem;color:#334155'>"
        f"DataPulse Quality Dashboard · Team 8 · "
        f"Log: <code>{loaders.LOG_FILE.name}</code>"
        f"</div>",
        unsafe_allow_html=True,
    )
    loaders.LOGGER.info("Dashboard render complete.")


if __name__ == "__main__":
    main()
