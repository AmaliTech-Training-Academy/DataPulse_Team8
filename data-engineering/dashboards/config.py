"""Dashboard configuration — thresholds, colours, and constants."""

from __future__ import annotations

# ── Score health bands ────────────────────────────────────────────────────────
SCORE_BANDS = {
    "excellent": {"min": 90,  "label": "Excellent",  "color": "#22c55e"},
    "good":      {"min": 75,  "label": "Good",       "color": "#3b82f6"},
    "warning":   {"min": 60,  "label": "Needs Review","color": "#f59e0b"},
    "critical":  {"min": 0,   "label": "Critical",    "color": "#ef4444"},
}

# ── Brand colours ─────────────────────────────────────────────────────────────
COLORS = {
    "bg_page":       "#0a0f1e",
    "bg_card":       "#111827",
    "bg_card_hover": "#1e293b",
    "border":        "#1e293b",
    "border_accent": "#334155",
    "text_primary":  "#f1f5f9",
    "text_secondary":"#cbd5e1",
    "text_muted":    "#64748b",
    "accent":        "#6366f1",
    "excellent":     "#22c55e",
    "good":          "#3b82f6",
    "warning":       "#f59e0b",
    "critical":      "#ef4444",
}

# ── Default DB URL ────────────────────────────────────────────────────────────
DEFAULT_DB_URL = "postgresql://datapulse:datapulse123@127.0.0.1:5433/datapulse"

# ── Plotly shared layout ──────────────────────────────────────────────────────
PLOTLY_BASE = dict(
    template="plotly_dark",
    paper_bgcolor="rgba(0,0,0,0)",
    plot_bgcolor="rgba(0,0,0,0)",
    font=dict(family="Inter, sans-serif", size=13, color="#cbd5e1"),
    margin=dict(l=16, r=16, t=44, b=16),
    legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
)


def score_band(score: float) -> dict:
    """Return the band dict for a given score."""
    if score >= SCORE_BANDS["excellent"]["min"]:
        return SCORE_BANDS["excellent"]
    if score >= SCORE_BANDS["good"]["min"]:
        return SCORE_BANDS["good"]
    if score >= SCORE_BANDS["warning"]["min"]:
        return SCORE_BANDS["warning"]
    return SCORE_BANDS["critical"]
