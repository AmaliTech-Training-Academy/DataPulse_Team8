"""All Plotly chart builders."""

from __future__ import annotations

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

from config import COLORS, PLOTLY_BASE, score_band


def _layout(**overrides) -> dict:
    d = dict(PLOTLY_BASE)
    d.update(overrides)
    return d


# ── Score Gauge ───────────────────────────────────────────────────────────────

def score_gauge(avg_score: float) -> go.Figure:
    band  = score_band(avg_score)
    color = band["color"]
    
    # Delta logic (dummy comparison to 75% for visual indicator)
    delta_val = avg_score - 75
    delta_color = COLORS["excellent"] if delta_val >= 0 else COLORS["critical"]
    delta_symbol = "▲" if delta_val >= 0 else "▼"
    
    fig = go.Figure(go.Indicator(
        mode="gauge",
        value=avg_score,
        gauge={
            "axis": {
                "range": [0, 100], 
                "tickwidth": 1, 
                "tickcolor": "#475569",
                "tickvals": [0, 60, 75, 90, 100],
                "tickfont": dict(size=12, color="#94a3b8")
            },
            "bar": {"color": color, "thickness": 0.25},
            "bgcolor": "rgba(30, 41, 59, 0.4)",
            "borderwidth": 0,
            "steps": [
                {"range": [0,  60],  "color": "rgba(239, 68, 68, 0.08)"},
                {"range": [60, 75],  "color": "rgba(245, 158, 11, 0.08)"},
                {"range": [75, 90],  "color": "rgba(59, 130, 246, 0.08)"},
                {"range": [90, 100], "color": "rgba(34, 197, 94, 0.08)"},
            ],
            "threshold": {"line": {"color": color, "width": 3},
                          "thickness": 0.8, "value": avg_score},
        },
    ))
    
    fig.update_layout(
        height=400,
        annotations=[
            # Large Score Text
            dict(
                text=f"<b style='color:{color};'>{avg_score:.0f}%</b>",
                x=0.5, y=0.35, xref="paper", yref="paper",
                showarrow=False,
                font=dict(size=44, family="Inter")
            ),
            # Delta Text
            dict(
                text=f"<b style='color:{delta_color};'>{delta_symbol} {abs(delta_val):.0f}</b>",
                x=0.5, y=0.18, xref="paper", yref="paper",
                showarrow=False,
                font=dict(size=16, family="Inter")
            ),
            # Band Label
            dict(
                text=f"<b>{band['label'].upper()}</b>",
                x=0.5, y=0.0, xref="paper", yref="paper",
                showarrow=False,
                font=dict(size=12, color=color, family="Inter")
            )
        ],
        **_layout(margin=dict(l=40, r=40, t=10, b=40)),
    )
    return fig


# ── Trend Line ────────────────────────────────────────────────────────────────

def trend_line(df: pd.DataFrame) -> go.Figure:
    # 1. Individual points for each dataset result (No lines)
    fig = px.scatter(
        df, x="full_date", y="avg_score", color="dataset_name",
        labels={"avg_score": "Quality Score (%)", "full_date": "Date", "dataset_name": "Dataset"},
        color_discrete_sequence=px.colors.qualitative.Vivid,
    )

    # 2. Global "Wave" (Average across all datasets)
    global_avg = df.groupby("full_date")["avg_score"].mean().reset_index()
    fig.add_trace(go.Scatter(
        x=global_avg["full_date"],
        y=global_avg["avg_score"],
        name="Global Trend",
        line=dict(color="rgba(255,255,255,0.4)", width=5, shape="spline"),
        mode="lines+markers",
        marker=dict(size=10, symbol="circle", color="rgba(255,255,255,0.6)"),
        connectgaps=True,
        hovertemplate="<b>Global Average</b>: %{y:.1f}%<extra></extra>"
    ))

    # 3. Zones & Thresholds
    fig.add_hrect(y0=90, y1=100, fillcolor="rgba(34,197,94,.05)", line_width=0,
                  annotation_text="Excellent zone", annotation_position="top right",
                  annotation_font=dict(size=10, color="#22c55e"))
    fig.add_hrect(y0=0, y1=60,  fillcolor="rgba(239,68,68,.05)",  line_width=0,
                  annotation_text="Critical zone",  annotation_position="bottom right",
                  annotation_font=dict(size=10, color="#ef4444"))
    fig.add_hline(y=75, line_dash="dot", line_color="#f59e0b", line_width=1,
                  annotation_text="Minimum acceptable (75%)",
                  annotation_position="right", annotation_font=dict(size=10))

    # 4. Global Styling
    fig.update_traces(
        selector=dict(mode="markers"),
        marker=dict(size=8, line=dict(width=1.5, color="white"))
    )

    fig.update_layout(
        yaxis=dict(range=[0, 105], gridcolor="#1e293b", tickfont=dict(size=10)),
        xaxis=dict(gridcolor="#1e293b", tickfont=dict(size=10)),
        **_layout(
            margin=dict(l=10, r=10, t=20, b=100),
            legend=dict(
                orientation="h",
                yanchor="top",
                y=-0.28,
                xanchor="center",
                x=0.5,
                font=dict(size=11),
                itemwidth=40,
                itemsizing="constant"
            )
        ),
    )
    return fig


# ── Rule Failure Bar ──────────────────────────────────────────────────────────

def rule_failure_bar(df: pd.DataFrame) -> go.Figure:
    top = df.nlargest(10, "failed_checks_count").iloc[::-1]
    severity_colors = {"HIGH": "#ef4444", "MEDIUM": "#f59e0b", "LOW": "#3b82f6"}
    colors = [severity_colors.get(s, "#6366f1") for s in top["severity"]]

    fig = go.Figure(go.Bar(
        x=top["failed_checks_count"],
        y=top["rule_name"],
        orientation="h",
        marker_color=colors,
        marker_line_width=0,
        text=top["check_failure_rate"].map(lambda r: f"{r*100:.0f}% fail rate"),
        textposition="outside",
        textfont=dict(size=11),
        hovertemplate=(
            "<b>%{y}</b><br>"
            "Failed checks: %{x}<br>"
            "<extra></extra>"
        ),
    ))
    fig.update_layout(
        xaxis_title="Number of Failed Checks",
        yaxis=dict(autorange="reversed", tickfont=dict(size=10)),
        **_layout(margin=dict(l=10, r=40, t=10, b=40)),
    )
    return fig


# ── Severity Donut ────────────────────────────────────────────────────────────

def severity_donut(df: pd.DataFrame) -> go.Figure:
    g = df.groupby("severity")["failed_checks_count"].sum().reset_index()
    color_map = {"HIGH": "#ef4444", "MEDIUM": "#f59e0b", "LOW": "#3b82f6"}
    colors = [color_map.get(s, "#6366f1") for s in g["severity"]]

    fig = go.Figure(go.Pie(
        labels=g["severity"],
        values=g["failed_checks_count"],
        hole=0.6,
        marker_colors=colors,
        textinfo="percent+label",
        hovertemplate="<b>%{label}</b><br>Failed: %{value}<br>%{percent}<extra></extra>",
        pull=[0.04] * len(g),
    ))
    fig.update_layout(
        annotations=[dict(text="<b>Failures<br>by Severity</b>", x=0.5, y=0.5,
                          font_size=11, showarrow=False, font_color="#94a3b8")],
        showlegend=True,
        **_layout(
            height=280, 
            margin=dict(l=5, r=5, t=10, b=30),
            legend=dict(orientation="h", yanchor="bottom", y=-0.4, xanchor="center", x=0.5, font=dict(size=9))
        ),
    )
    return fig


# ── ETL Timeline ──────────────────────────────────────────────────────────────

def etl_timeline(df: pd.DataFrame) -> go.Figure:
    status_colors = {"SUCCESS": "#22c55e", "FAILED": "#ef4444", "RUNNING": "#3b82f6"}
    df2 = df.copy()
    df2["started_at"] = pd.to_datetime(df2["started_at"])
    df2["color"] = df2["status"].map(lambda s: status_colors.get(s, "#64748b"))
    df2["label"] = df2.apply(
        lambda r: f"Batch #{r['id']} — {r['status']}<br>Rows: {r['rows_extracted']}", axis=1
    )

    fig = go.Figure()
    for _, row in df2.iterrows():
        fig.add_trace(go.Scatter(
            x=[row["started_at"]],
            y=[row["pipeline_name"]],
            mode="markers",
            marker=dict(size=16, color=row["color"], symbol="circle",
                        line=dict(width=2, color="rgba(255,255,255,.2)")),
            text=row["label"],
            hoverinfo="text",
            showlegend=False,
        ))

    fig.update_layout(
        xaxis_title="Run Time",
        yaxis_title="",
        height=180,
        **_layout(margin=dict(l=10, r=10, t=20, b=10)),
    )
    return fig
