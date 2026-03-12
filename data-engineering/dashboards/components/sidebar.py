"""Sidebar component — filters and controls."""

from __future__ import annotations

from datetime import datetime, timezone

import pandas as pd
import streamlit as st

from data.loaders import LOG_FILE, load_all_datasets


def render(engine) -> tuple[list[int], int]:
    """Render sidebar, return (selected_dataset_ids, day_window)."""
    with st.sidebar:
        # Brand
        st.markdown(
            """
<div style="padding:16px 4px 8px;">
  <div style="font-size:1.1rem;font-weight:700;color:#f1f5f9;letter-spacing:-0.01em;">DATAPULSE</div>
  <div style="font-size:.7rem;color:#475569;margin-top:2px;text-transform:uppercase;letter-spacing:0.05em;">Analytics Intelligence</div>
</div>
            """,
            unsafe_allow_html=True,
        )
        st.divider()

        # Dataset filter
        datasets_df = load_all_datasets(engine)
        selected_ids: list[int] = []

        if datasets_df.empty:
            st.warning("No datasets found yet.")
        else:
            choices = datasets_df.set_index("name")["id"].to_dict()
            st.markdown(
                "<div style='font-size:.7rem;font-weight:700;color:#64748b;"
                "text-transform:uppercase;letter-spacing:.08em;margin-bottom:6px'>"
                "Filter by Dataset</div>",
                unsafe_allow_html=True,
            )
            selected_names = st.multiselect(
                "Datasets",
                options=list(choices.keys()),
                default=list(choices.keys()),
                label_visibility="collapsed",
            )
            selected_ids = [choices[n] for n in selected_names]

        st.divider()

        # Time window
        st.markdown(
            "<div style='font-size:.7rem;font-weight:700;color:#64748b;"
            "text-transform:uppercase;letter-spacing:.08em;margin-bottom:6px'>"
            "Trend Window</div>",
            unsafe_allow_html=True,
        )
        day_window = st.selectbox(
            "Time window",
            options=[7, 14, 30, 90],
            index=2,
            format_func=lambda d: f"Last {d} days",
            label_visibility="collapsed",
        )

        st.divider()

        

        # Footer meta
        st.markdown(
            f"""
<div style="font-size:.7rem;color:#475569;line-height:1.8">
  {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M UTC')}<br>
  Log: <code>{LOG_FILE.name}</code><br>
  Auto-refresh every 60s
</div>
            """,
            unsafe_allow_html=True,
        )

    return selected_ids, int(day_window)
