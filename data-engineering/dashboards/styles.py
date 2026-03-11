"""Custom CSS injected into the Streamlit app - Premium Overhaul."""

import streamlit as st


def inject() -> None:
    st.markdown(
        """
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800&display=swap');

html, body, [class*="css"] {
    font-family: 'Inter', sans-serif !important;
}

/* ── Page background ─────────────────────────────────────── */
.stApp { background: #0a0b10; }
.block-container { padding: 1.5rem 2rem 2rem; max-width: 1400px; }

/* ── Hero banner ─────────────────────────────────────────── */
.dp-hero {
    background: linear-gradient(135deg, #1e1b4b 0%, #0a0b10 100%);
    border: 1px solid rgba(255, 255, 255, 0.05);
    border-radius: 16px;
    padding: 32px 40px;
    margin-top: 24px;
    margin-bottom: 32px;
    position: relative;
    overflow: hidden;
    backdrop-filter: blur(10px);
}
.dp-hero::after {
    content: '';
    position: absolute;
    top: -50px; right: -50px;
    width: 250px; height: 250px;
    border-radius: 50%;
    background: radial-gradient(circle, rgba(99,102,241,0.15) 0%, transparent 75%);
}
.dp-hero h1 {
    font-size: 2rem; font-weight: 800;
    letter-spacing: -0.02em;
    color: #ffffff; margin: 0 0 8px;
}
.dp-hero p  { color: #64748b; font-size: 0.95rem; margin: 0; font-weight: 400; }

/* ── KPI cards ───────────────────────────────────────────── */
.kpi-card {
    background: rgba(17, 24, 39, 0.6);
    border: 1px solid rgba(255, 255, 255, 0.05);
    border-radius: 12px;
    padding: 24px;
    position: relative; overflow: hidden;
    transition: all 0.2s ease;
    height: 100%;
    cursor: default;
    box-shadow: 0 4px 12px rgba(0, 0, 0, 0.2);
}
.kpi-card:hover { 
    transform: translateY(-4px); 
    border-color: rgba(99, 102, 241, 0.3);
    box-shadow: 0 12px 24px rgba(0, 0, 0, 0.4);
}
.kpi-card::before {
    content: ''; position: absolute;
    top: 0; left: 0; right: 0; height: 2px;
}
.kpi-excellent::before { background: #22c55e; }
.kpi-good::before      { background: #3b82f6; }
.kpi-warning::before   { background: #f59e0b; }
.kpi-critical::before  { background: #ef4444; }
.kpi-neutral::before   { background: #6366f1; }

.kpi-label  { font-size: 0.7rem; font-weight: 600; letter-spacing: 0.08em;
               text-transform: uppercase; color: #64748b; margin-bottom: 8px; }
.kpi-value  { font-size: 2.25rem; font-weight: 800; color: #f8fafc; line-height: 1; letter-spacing: -0.03em; }
.kpi-sub    { font-size: 0.8rem; color: #475569; margin-top: 10px; font-weight: 500; }
.kpi-badge  {
    display: inline-block; padding: 4px 12px;
    border-radius: 6px; font-size: 0.65rem; font-weight: 700;
    margin-top: 12px;
    text-transform: uppercase;
    letter-spacing: 0.05em;
}
.badge-excellent { background: rgba(34,197,94,0.1);  color: #4ade80; }
.badge-good      { background: rgba(59,130,246,0.1);  color: #60a5fa; }
.badge-warning   { background: rgba(245,158,11,0.1);  color: #fbbf24; }
.badge-critical  { background: rgba(239,68,68,0.1);   color: #f87171; }
.badge-neutral   { background: rgba(99,102,241,0.1);  color: #818cf8; }

/* ── Section headers ─────────────────────────────────────── */
.dp-section {
    display: flex; align-items: baseline; gap: 12px;
    margin: 40px 0 20px;
}
.dp-section-bar {
    width: 3px; height: 18px; border-radius: 1px;
    background: #6366f1;
}
.dp-section-title {
    font-size: 1.15rem; font-weight: 700; color: #f1f5f9; letter-spacing: -0.01em;
}
.dp-section-sub { font-size: 0.85rem; color: #475569; font-weight: 400; }

/* ── Health summary banner ───────────────────────────────── */
.health-banner {
    border-radius: 12px; padding: 20px 24px;
    margin-bottom: 24px;
    border: 1px solid;
    display: flex; align-items: flex-start; gap: 16px;
}
.health-banner-excellent { background: rgba(34,197,94,0.04);  border-color: rgba(34,197,94,0.2); }
.health-banner-good      { background: rgba(59,130,246,0.04);  border-color: rgba(59,130,246,0.2); }
.health-banner-warning   { background: rgba(245,158,11,0.04);  border-color: rgba(245,158,11,0.2); }
.health-banner-critical  { background: rgba(239,68,68,0.04);   border-color: rgba(239,68,68,0.2); }

.health-banner-text h3 { margin: 0 0 4px; font-size: 1.05rem; font-weight: 700; color: #f1f5f9; }
.health-banner-text p  { margin: 0; font-size: 0.875rem; color: #94a3b8; line-height: 1.6; }

/* ── Dataset cards (grid) ────────────────────────────────── */
.ds-card {
    background: rgba(17, 24, 39, 0.4); border: 1px solid rgba(255, 255, 255, 0.05);
    border-radius: 12px; padding: 24px;
    margin-bottom: 16px;
    transition: all 0.2s ease;
}
.ds-card:hover { border-color: rgba(255, 255, 255, 0.1); background: rgba(17, 24, 39, 0.6); }
.ds-name { font-size: 1rem; font-weight: 700; color: #f1f5f9; letter-spacing: -0.01em; }
.ds-meta { font-size: 0.75rem; color: #475569; margin-top: 4px; }
.ds-score-wrap { display: flex; align-items: center; gap: 12px; margin-top: 20px; }
.ds-score-bar-bg {
    flex: 1; height: 6px; border-radius: 3px;
    background: rgba(31, 41, 55, 0.5);
}
.ds-score-bar-fill { height: 6px; border-radius: 3px; transition: width 0.6s cubic-bezier(0.16, 1, 0.3, 1); }
.ds-score-val { font-size: 0.9rem; font-weight: 700; color: #f8fafc; }

/* ── Plain English insight box ───────────────────────────── */
.insight-box {
    background: rgba(17, 24, 39, 0.4); border: 1px solid rgba(255, 255, 255, 0.05);
    border-radius: 12px; padding: 24px;
}
.insight-box h4 { margin: 0 0 16px; font-size: 0.75rem; font-weight: 700;
                   color: #64748b; text-transform: uppercase; letter-spacing: 0.1em; }
.insight-item { display: flex; align-items: flex-start; gap: 12px; margin-bottom: 14px; }
.insight-item:last-child { margin-bottom: 0; }
.insight-bullet { width: 4px; height: 16px; background: #6366f1; border-radius: 2px; flex-shrink: 0; margin-top: 4px; }
.insight-text { font-size: 0.875rem; color: #cbd5e1; line-height: 1.6; }

/* ── Empty state ─────────────────────────────────────────── */
.dp-empty {
    background: rgba(17, 24, 39, 0.2); border: 1px dashed rgba(255, 255, 255, 0.05);
    border-radius: 12px; padding: 48px 32px;
    text-align: center;
}
.dp-empty-title { font-size: 0.95rem; font-weight: 600; color: #475569; }
.dp-empty-sub   { font-size: 0.85rem; margin-top: 6px; color: #334155; }

/* ── Sidebar ─────────────────────────────────────────────── */
[data-testid="stSidebar"] {
    background: #06070a !important;
    border-right: 1px solid rgba(255, 255, 255, 0.05);
}
[data-testid="stSidebar"] label { color: #64748b !important; font-size: 0.75rem !important; font-weight: 600 !important; }

/* ── Dataframe / table ───────────────────────────────────── */
[data-testid="stDataFrame"] { 
    border: 1px solid rgba(255, 255, 255, 0.05);
    border-radius: 8px; 
}

/* ── Divider ─────────────────────────────────────────────── */
hr  { border-color: rgba(255, 255, 255, 0.05) !important; }
</style>
        """,
        unsafe_allow_html=True,
    )
