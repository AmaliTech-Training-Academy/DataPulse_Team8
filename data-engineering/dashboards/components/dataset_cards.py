"""Dataset cards grid — non-technical-friendly progress bars."""

from __future__ import annotations

import pandas as pd
import streamlit as st

from config import score_band


def render_dataset_cards(latest_df: pd.DataFrame) -> None:
    """Show each dataset as a card with a coloured progress bar."""
    if latest_df.empty:
        st.markdown(
            """
<div class="dp-empty">
  <span class="dp-empty-icon"></span>
  <div class="dp-empty-title">No datasets analysed yet</div>
  <div class="dp-empty-sub">Upload a file via the backend API and run a quality check to see results here.</div>
</div>
            """,
            unsafe_allow_html=True,
        )
        return

    cols_per_row = 2
    rows = [latest_df.iloc[i:i+cols_per_row] for i in range(0, len(latest_df), cols_per_row)]

    for row_df in rows:
        cols = st.columns(cols_per_row)
        for col, (_, r) in zip(cols, row_df.iterrows()):
            band  = score_band(float(r["score"]))
            color = band["color"]
            pct   = float(r["score"])
            pass_pct = int(r["passed_rules"] / r["total_rules"] * 100) if r["total_rules"] else 0
            checked = pd.to_datetime(r["checked_at"]).strftime("%d %b %Y, %H:%M")

            with col:
                st.markdown(
                    f"""
<div class="ds-card">
  <div style="display:flex;justify-content:space-between;align-items:flex-start">
    <div>
      <div class="ds-name">{r['dataset_name']}</div>
      <div class="ds-meta">Last checked: {checked}</div>
    </div>
    <div style="text-align:right">
      <div style="font-size:1.4rem;font-weight:800;color:{color}">{pct:.0f}%</div>
      <div style="font-size:.7rem;color:#64748b">{band['label']}</div>
    </div>
  </div>
  <div class="ds-score-wrap" style="margin-top:14px">
    <div class="ds-score-bar-bg" style="flex:1">
      <div class="ds-score-bar-fill" style="width:{pct}%;background:{color}"></div>
    </div>
  </div>
  <div style="display:flex;gap:16px;margin-top:10px">
    <div style="font-size:.75rem;color:#94a3b8">
      Processed: <strong style="color:#22c55e">{int(r['passed_rules'])}</strong> passed
    </div>
    <div style="font-size:.75rem;color:#94a3b8">
      Errors: <strong style="color:#ef4444">{int(r['failed_rules'])}</strong> failed
    </div>
    <div style="font-size:.75rem;color:#94a3b8">
      Rules: <strong style="color:#cbd5e1">{int(r['total_rules'])}</strong> total
    </div>
  </div>
</div>
                    """,
                    unsafe_allow_html=True,
                )


def render_insights(failure_df: pd.DataFrame, latest_df: pd.DataFrame) -> None:
    """Generate plain-English insights a non-technical user can understand."""
    items = []

    if not latest_df.empty:
        best = latest_df.loc[latest_df["score"].idxmax()]
        worst = latest_df.loc[latest_df["score"].idxmin()]
        items.append(("•", f"<b>{best['dataset_name']}</b> is your highest quality dataset with a score of <b>{best['score']:.0f}%</b>."))
        if float(worst["score"]) < 90:
            items.append(("•", f"<b>{worst['dataset_name']}</b> has the lowest score (<b>{worst['score']:.0f}%</b>) and may need attention."))

    if not failure_df.empty:
        top_fail = failure_df.iloc[0]
        items.append(("•", f"The most common issue is the rule <b>'{top_fail['rule_name']}'</b> which failed <b>{int(top_fail['failed_checks_count'])}</b> time(s)."))
        high_sev = failure_df[failure_df["severity"] == "HIGH"]
        if not high_sev.empty:
            items.append(("•", f"There are <b>{len(high_sev)}</b> HIGH severity rule(s) failing — these should be fixed as a priority."))

    if not items:
        items.append(("•", "No insights available yet. Upload datasets and run checks to see recommendations here."))

    bullets = "".join(
        f'<div class="insight-item"><span class="insight-bullet"></span><span class="insight-text">{t}</span></div>'
        for _, t in items
    )
    st.markdown(
        f"""
<div class="insight-box">
  <h4>What does this mean?</h4>
  {bullets}
</div>
        """,
        unsafe_allow_html=True,
    )
