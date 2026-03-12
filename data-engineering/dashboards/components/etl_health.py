"""ETL pipeline health section."""

from __future__ import annotations

import pandas as pd
import streamlit as st

from components import charts


def render_etl_health(etl_df: pd.DataFrame) -> None:
    if etl_df.empty:
        st.markdown(
            '<div class="dp-empty"><span class="dp-empty-icon"></span>'
            '<div class="dp-empty-title">No pipeline runs recorded yet.</div></div>',
            unsafe_allow_html=True,
        )
        return

    # Summary stats
    success = (etl_df["status"] == "SUCCESS").sum()
    failed  = (etl_df["status"] == "FAILED").sum()
    avg_dur = etl_df["duration_s"].dropna().mean()
    total   = len(etl_df)

    c1, c2, c3 = st.columns(3)
    with c1:
        tier = "excellent" if failed == 0 else ("warning" if failed < 3 else "critical")
        st.markdown(
            f"""
<div class="kpi-card kpi-{tier}" style="padding:16px">
  <div class="kpi-label">Pipeline Success Rate</div>
  <div class="kpi-value" style="font-size:1.6rem">{success}/{total}</div>
  <div class="kpi-sub">Recent runs</div>
</div>
            """, unsafe_allow_html=True,
        )
    with c2:
        tier2 = "critical" if failed else "excellent"
        st.markdown(
            f"""
<div class="kpi-card kpi-{tier2}" style="padding:16px">
  <div class="kpi-label">Failed Runs</div>
  <div class="kpi-value" style="font-size:1.6rem">{failed}</div>
  <div class="kpi-sub">In the last {total} executions</div>
</div>
            """, unsafe_allow_html=True,
        )
    with c3:
        st.markdown(
            f"""
<div class="kpi-card kpi-neutral" style="padding:16px">
  <div class="kpi-label">Avg Pipeline Duration</div>
  <div class="kpi-value" style="font-size:1.6rem">{f"{avg_dur:.0f}s" if not pd.isna(avg_dur) else "N/A"}</div>
  <div class="kpi-sub">Per batch</div>
</div>
            """, unsafe_allow_html=True,
        )

    st.write("")
    # Timeline chart
    st.plotly_chart(charts.etl_timeline(etl_df), use_container_width=True)

    # Readable table
    with st.expander("View Full Run History", expanded=False):
        display = etl_df.copy()
        icon_map = {"SUCCESS": "Success", "FAILED": "Failed", "RUNNING": "Running"}
        display["Status"]       = display["status"].map(lambda s: icon_map.get(s, s))
        display["Started At"]   = pd.to_datetime(display["started_at"]).dt.strftime("%Y-%m-%d %H:%M")
        display["Rows Processed"] = display["rows_extracted"].map(lambda r: f"{r:,}")
        display["Duration"]     = display["duration_s"].map(lambda d: f"{d}s" if pd.notna(d) else "—")
        display["Error"]        = display["error_message"].fillna("—")

        st.dataframe(
            display[["id", "Status", "Started At", "Rows Processed", "Duration", "Error"]].rename(
                columns={"id": "Batch ID"}
            ),
            use_container_width=True,
            hide_index=True,
        )
