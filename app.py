import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import date, datetime, timedelta
import hashlib
import time
import database as db
import gold_rate as gr
import stock_price as sp
import seed_data

# --- Init ---
db.init_db()
seed_data.seed()


# ======================== PIN LOGIN ========================
def _hash_pin(pin):
    return hashlib.sha256(pin.encode()).hexdigest()


def _check_auth():
    """Return True if user is authenticated."""
    pin_hash = st.secrets.get("PIN_HASH", "")
    if not pin_hash:
        return True  # No PIN set, skip auth
    return st.session_state.get("authenticated", False)


def _show_login():
    """Render the 4-digit PIN login screen."""
    st.markdown("""
    <style>
        [data-testid="stSidebar"] { display: none !important; }
        section.main > div { display: flex; justify-content: center; align-items: center; min-height: 80vh; }
    </style>
    """, unsafe_allow_html=True)

    col_l, col_c, col_r = st.columns([1, 1.2, 1])
    with col_c:
        st.markdown(
            '<div style="text-align:center;padding:40px 30px;background:white;border-radius:20px;'
            'box-shadow:0 8px 30px rgba(0,0,0,0.08);border:1px solid #E2E8F0;">'
            '<div style="font-size:2.5rem;margin-bottom:8px;">\U0001f4b0</div>'
            '<div style="font-size:1.4rem;font-weight:800;color:#0F172A;margin-bottom:4px;">'
            'Finance Tracker</div>'
            '<div style="font-size:0.85rem;color:#64748B;margin-bottom:28px;">'
            'Enter your 4-digit PIN to continue</div>'
            '</div>',
            unsafe_allow_html=True,
        )

        pin = st.text_input(
            "PIN", type="password", max_chars=4, placeholder="Enter PIN",
            label_visibility="collapsed",
        )

        # --- Lockout logic ---
        max_attempts = 5
        lockout_seconds = 900  # 15 minutes
        if "login_attempts" not in st.session_state:
            st.session_state["login_attempts"] = 0
        if "lockout_until" not in st.session_state:
            st.session_state["lockout_until"] = 0

        locked = st.session_state["lockout_until"] > time.time()
        if locked:
            remaining = int(st.session_state["lockout_until"] - time.time())
            mins, secs = divmod(remaining, 60)
            st.error(f"Too many failed attempts. Try again in {mins}m {secs}s.")
        elif st.button("Unlock", type="primary", use_container_width=True):
            if not pin or len(pin) != 4 or not pin.isdigit():
                st.error("Please enter a 4-digit PIN")
            elif _hash_pin(pin) == st.secrets.get("PIN_HASH", ""):
                st.session_state["authenticated"] = True
                st.session_state["login_attempts"] = 0
                st.rerun()
            else:
                st.session_state["login_attempts"] += 1
                remaining_tries = max_attempts - st.session_state["login_attempts"]
                if remaining_tries <= 0:
                    st.session_state["lockout_until"] = time.time() + lockout_seconds
                    st.session_state["login_attempts"] = 0
                    st.error("Too many failed attempts. Locked for 15 minutes.")
                else:
                    st.error(f"Incorrect PIN. {remaining_tries} attempt(s) left.")


# --- Auth gate ---
if not _check_auth():
    _show_login()
    st.stop()

# --- Color Palette (Light Professional) ---
COLORS = {
    "primary": "#1E40AF",
    "primary_light": "#3B82F6",
    "accent": "#2563EB",
    "accent_hover": "#1D4ED8",
    "success": "#059669",
    "success_light": "#D1FAE5",
    "warning": "#D97706",
    "warning_light": "#FEF3C7",
    "danger": "#DC2626",
    "danger_light": "#FEE2E2",
    "gold": "#B45309",
    "gold_light": "#FDE68A",
    "gold_accent": "#F59E0B",
    "surface": "#F8FAFC",
    "surface2": "#F1F5F9",
    "card": "#FFFFFF",
    "card_border": "#E2E8F0",
    "card_shadow": "0 1px 3px rgba(0,0,0,0.06), 0 1px 2px rgba(0,0,0,0.04)",
    "text": "#0F172A",
    "text_secondary": "#334155",
    "text_muted": "#64748B",
    "bg": "#F1F5F9",
    "white": "#FFFFFF",
}

CHART_COLORS = ["#2563EB", "#059669", "#D97706", "#DC2626", "#7C3AED",
                "#DB2777", "#0D9488", "#EA580C", "#4F46E5", "#65A30D"]

st.set_page_config(
    page_title="Finance Tracker",
    page_icon="https://em-content.zobj.net/source/apple/391/chart-increasing_1f4c8.png",
    layout="wide",
    initial_sidebar_state="expanded",
)

# --- Professional CSS (Light) ---
st.markdown(f"""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&display=swap');

    .stApp {{
        background: {COLORS["bg"]};
        font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif;
    }}

    /* Sidebar */
    section[data-testid="stSidebar"] {{
        background: linear-gradient(180deg, #0F172A 0%, #1E293B 100%);
        border-right: none;
    }}
    section[data-testid="stSidebar"] [data-testid="stRadio"] {{
        display: none;
    }}
    section[data-testid="stSidebar"] hr {{
        border-color: rgba(255,255,255,0.08) !important;
    }}
    /* Sidebar button styling */
    section[data-testid="stSidebar"] button[kind="secondary"] {{
        background: transparent !important;
        border: 1px solid transparent !important;
        box-shadow: none !important;
        color: rgba(255,255,255,0.7) !important;
        font-size: 0.84rem !important;
        font-weight: 500 !important;
        padding: 10px 14px !important;
        border-radius: 10px !important;
        text-align: left !important;
        justify-content: flex-start !important;
        transition: all 0.2s ease !important;
    }}
    section[data-testid="stSidebar"] button[kind="secondary"]:hover {{
        background: rgba(255,255,255,0.06) !important;
        color: #F8FAFC !important;
        border-color: transparent !important;
    }}
    section[data-testid="stSidebar"] button[kind="primary"] {{
        background: linear-gradient(135deg, rgba(59,130,246,0.2), rgba(99,102,241,0.15)) !important;
        border: 1px solid rgba(96,165,250,0.25) !important;
        box-shadow: none !important;
        color: #60A5FA !important;
        font-size: 0.84rem !important;
        font-weight: 600 !important;
        padding: 10px 14px !important;
        border-radius: 10px !important;
        text-align: left !important;
        justify-content: flex-start !important;
    }}
    section[data-testid="stSidebar"] button[kind="primary"]:hover {{
        background: linear-gradient(135deg, rgba(59,130,246,0.25), rgba(99,102,241,0.2)) !important;
        transform: none !important;
        box-shadow: none !important;
    }}
    section[data-testid="stSidebar"] .stElementContainer {{
        margin-bottom: -8px;
    }}

    #MainMenu, footer {{visibility: hidden;}}
    .stDeployButton {{display: none;}}

    /* Sidebar collapse/expand button - always visible */
    button[data-testid="stBaseButton-header"],
    button[data-testid="baseButton-header"] {{
        color: white !important;
        background: rgba(255,255,255,0.08) !important;
        border: 1px solid rgba(255,255,255,0.12) !important;
        border-radius: 8px !important;
    }}
    button[data-testid="stBaseButton-header"]:hover,
    button[data-testid="baseButton-header"]:hover {{
        background: rgba(255,255,255,0.15) !important;
    }}
    /* Collapsed state - show expand button clearly */
    [data-testid="stSidebarCollapsedControl"] button {{
        color: {COLORS["text"]} !important;
        background: {COLORS["card"]} !important;
        border: 1px solid {COLORS["card_border"]} !important;
        border-radius: 10px !important;
        box-shadow: 0 2px 8px rgba(0,0,0,0.1) !important;
    }}
    [data-testid="stSidebarCollapsedControl"] button:hover {{
        background: {COLORS["surface2"]} !important;
    }}
    [data-testid="stSidebarCollapsedControl"] {{
        top: 12px !important;
        left: 12px !important;
    }}

    /* ===== Metric Cards ===== */
    .metric-row {{
        display: flex;
        gap: 16px;
        margin-bottom: 24px;
    }}
    .metric-card {{
        flex: 1;
        padding: 22px 20px;
        border-radius: 14px;
        background: {COLORS["card"]};
        border: 1px solid {COLORS["card_border"]};
        box-shadow: {COLORS["card_shadow"]};
        position: relative;
        overflow: hidden;
    }}
    .metric-card::before {{
        content: '';
        position: absolute;
        top: 0; left: 0; right: 0;
        height: 3px;
    }}
    .metric-card.blue::before {{ background: linear-gradient(90deg, #1E40AF, #3B82F6); }}
    .metric-card.green::before {{ background: linear-gradient(90deg, #047857, #10B981); }}
    .metric-card.amber::before {{ background: linear-gradient(90deg, #B45309, #F59E0B); }}
    .metric-card.purple::before {{ background: linear-gradient(90deg, #6D28D9, #8B5CF6); }}
    .metric-card.gold::before {{ background: linear-gradient(90deg, #92400E, #F59E0B); }}

    .metric-label {{
        font-size: 0.72rem;
        font-weight: 600;
        text-transform: uppercase;
        letter-spacing: 0.07em;
        color: {COLORS["text_muted"]};
        margin-bottom: 6px;
    }}
    .metric-value {{
        font-size: 1.55rem;
        font-weight: 800;
        color: {COLORS["text"]};
        line-height: 1.2;
    }}
    .metric-words {{
        font-size: 0.78rem;
        font-weight: 500;
        color: {COLORS["text_secondary"]};
        margin-top: 2px;
        font-style: italic;
    }}
    .metric-sub {{
        font-size: 0.78rem;
        color: {COLORS["text_muted"]};
        margin-top: 5px;
    }}
    .metric-icon {{
        position: absolute;
        top: 16px; right: 16px;
        font-size: 1.5rem;
        opacity: 0.18;
    }}

    /* ===== Section Headers ===== */
    .section-header {{
        font-size: 1.05rem;
        font-weight: 700;
        color: {COLORS["text"]};
        margin: 28px 0 14px 0;
        padding-bottom: 10px;
        border-bottom: 2px solid {COLORS["card_border"]};
        display: flex;
        align-items: center;
        gap: 8px;
    }}
    .section-header .icon {{ font-size: 1.1rem; }}

    /* ===== Page Title ===== */
    .page-title {{
        font-size: 1.65rem;
        font-weight: 800;
        color: {COLORS["text"]};
        margin-bottom: 2px;
    }}
    .page-subtitle {{
        font-size: 0.88rem;
        color: {COLORS["text_muted"]};
        margin-bottom: 20px;
    }}

    /* ===== Card Container ===== */
    .card-container {{
        background: {COLORS["card"]};
        border: 1px solid {COLORS["card_border"]};
        border-radius: 14px;
        padding: 24px;
        margin-bottom: 16px;
        box-shadow: {COLORS["card_shadow"]};
    }}

    /* ===== Table ===== */
    .styled-table {{
        width: 100%;
        border-collapse: separate;
        border-spacing: 0;
        border-radius: 12px;
        overflow: hidden;
        border: 1px solid {COLORS["card_border"]};
        font-size: 0.84rem;
        background: {COLORS["card"]};
    }}
    .styled-table thead th {{
        background: {COLORS["surface2"]};
        color: {COLORS["text_muted"]};
        font-weight: 600;
        font-size: 0.72rem;
        text-transform: uppercase;
        letter-spacing: 0.06em;
        padding: 11px 14px;
        text-align: left;
        border-bottom: 1px solid {COLORS["card_border"]};
    }}
    .styled-table tbody td {{
        padding: 10px 14px;
        border-bottom: 1px solid {COLORS["card_border"]};
        color: {COLORS["text_secondary"]};
    }}
    .styled-table tbody tr:last-child td {{ border-bottom: none; }}
    .styled-table tbody tr:hover {{ background: #F8FAFC; }}

    .badge {{
        display: inline-block;
        padding: 3px 10px;
        border-radius: 20px;
        font-size: 0.7rem;
        font-weight: 600;
    }}
    .badge-liquid {{
        background: {COLORS["success_light"]};
        color: {COLORS["success"]};
    }}
    .badge-nonliquid {{
        background: {COLORS["warning_light"]};
        color: {COLORS["warning"]};
    }}
    .amount {{
        font-weight: 600;
        font-variant-numeric: tabular-nums;
        color: {COLORS["text"]};
    }}
    .amount-positive {{ color: {COLORS["success"]}; }}
    .amount-negative {{ color: {COLORS["danger"]}; }}

    /* ===== Dashboard Enhancements ===== */
    .dash-kpi-grid {{
        display: grid;
        grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
        gap: 14px;
        margin-bottom: 20px;
    }}
    .dash-kpi {{
        padding: 18px 16px;
        border-radius: 12px;
        background: {COLORS["card"]};
        border: 1px solid {COLORS["card_border"]};
        box-shadow: {COLORS["card_shadow"]};
    }}
    .dash-kpi-label {{
        font-size: 0.68rem;
        font-weight: 600;
        text-transform: uppercase;
        letter-spacing: 0.06em;
        color: {COLORS["text_muted"]};
        margin-bottom: 4px;
    }}
    .dash-kpi-value {{
        font-size: 1.25rem;
        font-weight: 800;
        color: {COLORS["text"]};
    }}
    .dash-kpi-sub {{
        font-size: 0.75rem;
        color: {COLORS["text_muted"]};
        margin-top: 3px;
    }}
    .dash-insight-card {{
        background: {COLORS["card"]};
        border: 1px solid {COLORS["card_border"]};
        border-radius: 14px;
        padding: 20px;
        box-shadow: {COLORS["card_shadow"]};
        margin-bottom: 16px;
    }}
    .dash-insight-title {{
        font-size: 0.72rem;
        font-weight: 700;
        text-transform: uppercase;
        letter-spacing: 0.06em;
        color: {COLORS["text_muted"]};
        margin-bottom: 12px;
        padding-bottom: 8px;
        border-bottom: 1px solid {COLORS["card_border"]};
    }}
    .dash-bar-row {{
        display: flex;
        align-items: center;
        gap: 10px;
        padding: 6px 0;
    }}
    .dash-bar-label {{
        font-size: 0.82rem;
        font-weight: 500;
        color: {COLORS["text_secondary"]};
        min-width: 130px;
    }}
    .dash-bar-track {{
        flex: 1;
        height: 8px;
        background: {COLORS["surface2"]};
        border-radius: 4px;
        overflow: hidden;
    }}
    .dash-bar-fill {{
        height: 100%;
        border-radius: 4px;
        transition: width 0.5s ease;
    }}
    .dash-bar-amount {{
        font-size: 0.78rem;
        font-weight: 600;
        color: {COLORS["text"]};
        min-width: 100px;
        text-align: right;
        font-variant-numeric: tabular-nums;
    }}
    .dash-score-ring {{
        width: 120px;
        height: 120px;
        border-radius: 50%;
        display: flex;
        align-items: center;
        justify-content: center;
        flex-direction: column;
        margin: 0 auto 12px auto;
    }}
    .dash-score-value {{
        font-size: 2rem;
        font-weight: 800;
        line-height: 1;
    }}
    .dash-score-label {{
        font-size: 0.65rem;
        font-weight: 600;
        text-transform: uppercase;
        letter-spacing: 0.05em;
        margin-top: 2px;
    }}
    .dash-change-positive {{
        color: {COLORS["success"]};
        font-weight: 600;
    }}
    .dash-change-negative {{
        color: {COLORS["danger"]};
        font-weight: 600;
    }}

    /* ===== Sidebar Brand ===== */
    .nav-brand {{
        font-size: 1.2rem;
        font-weight: 800;
        color: #F8FAFC;
        padding: 4px 0 18px 0;
        letter-spacing: -0.02em;
        border-bottom: 1px solid rgba(255,255,255,0.08);
        margin-bottom: 16px;
    }}
    .nav-brand .accent {{ color: #60A5FA; }}

    /* ===== Sidebar Nav Buttons ===== */
    .sb-section {{
        font-size: 0.6rem;
        font-weight: 700;
        text-transform: uppercase;
        letter-spacing: 0.1em;
        color: rgba(255,255,255,0.35);
        padding: 14px 12px 6px 12px;
    }}
    .sb-nav {{
        display: flex;
        flex-direction: column;
        gap: 3px;
    }}
    .sb-btn {{
        display: flex;
        align-items: center;
        gap: 10px;
        padding: 10px 14px;
        border-radius: 10px;
        color: rgba(255,255,255,0.7);
        font-size: 0.84rem;
        font-weight: 500;
        cursor: pointer;
        transition: all 0.2s ease;
        text-decoration: none;
        border: 1px solid transparent;
    }}
    .sb-btn:hover {{
        background: rgba(255,255,255,0.06);
        color: #F8FAFC;
    }}
    .sb-btn.active {{
        background: linear-gradient(135deg, rgba(59,130,246,0.2), rgba(99,102,241,0.15));
        color: #60A5FA;
        font-weight: 600;
        border-color: rgba(96,165,250,0.25);
    }}
    .sb-btn .sb-icon {{
        width: 28px;
        height: 28px;
        border-radius: 8px;
        display: flex;
        align-items: center;
        justify-content: center;
        font-size: 0.95rem;
        flex-shrink: 0;
    }}
    .sb-btn.active .sb-icon {{
        background: rgba(59,130,246,0.15);
    }}

    /* ===== Streamlit Overrides ===== */
    div[data-testid="stMetric"] {{
        background: {COLORS["card"]};
        border: 1px solid {COLORS["card_border"]};
        border-radius: 12px;
        padding: 16px;
        box-shadow: {COLORS["card_shadow"]};
    }}
    div[data-testid="stMetric"] label {{
        color: {COLORS["text_muted"]} !important;
        font-weight: 600;
        font-size: 0.72rem;
        text-transform: uppercase;
        letter-spacing: 0.06em;
    }}
    div[data-testid="stMetric"] [data-testid="stMetricValue"] {{
        color: {COLORS["text"]} !important;
        font-weight: 700;
    }}

    .stTextInput > div > div > input,
    .stNumberInput > div > div > input,
    .stSelectbox > div > div {{
        background: {COLORS["white"]} !important;
        border-color: {COLORS["card_border"]} !important;
        color: {COLORS["text"]} !important;
        border-radius: 10px !important;
    }}
    .stDateInput > div > div > input {{
        background: {COLORS["white"]} !important;
        border-color: {COLORS["card_border"]} !important;
        color: {COLORS["text"]} !important;
        border-radius: 10px !important;
    }}

    /* Form field labels - ensure visibility */
    .stTextInput > label,
    .stNumberInput > label,
    .stSelectbox > label,
    .stDateInput > label,
    .stTextArea > label,
    .stRadio > label,
    .stCheckbox > label,
    .stMultiSelect > label {{
        color: {COLORS["text_secondary"]} !important;
        font-size: 0.85rem !important;
        font-weight: 600 !important;
        margin-bottom: 4px !important;
        letter-spacing: 0.01em;
    }}
    /* Form field labels inside forms */
    [data-testid="stForm"] label p {{
        color: {COLORS["text_secondary"]} !important;
        font-size: 0.85rem !important;
        font-weight: 600 !important;
    }}

    button[kind="primary"] {{
        background: linear-gradient(135deg, {COLORS["accent"]}, {COLORS["primary"]}) !important;
        border: none !important;
        border-radius: 10px !important;
        font-weight: 600 !important;
        padding: 8px 24px !important;
        color: white !important;
        transition: all 0.2s ease !important;
    }}
    button[kind="primary"]:hover {{
        transform: translateY(-1px);
        box-shadow: 0 4px 14px rgba(37, 99, 235, 0.3) !important;
    }}

    .stExpander {{
        background: {COLORS["card"]};
        border: 1px solid {COLORS["card_border"]} !important;
        border-radius: 12px !important;
        box-shadow: {COLORS["card_shadow"]};
    }}
    div[data-testid="stExpander"] details {{ border: none !important; }}
    div[data-testid="stExpander"] summary {{
        color: {COLORS["text_secondary"]} !important;
    }}
    div[data-testid="stExpander"] summary span,
    div[data-testid="stExpander"] summary p,
    div[data-testid="stExpander"] [data-testid="stMarkdownContainer"] p {{
        color: {COLORS["text_secondary"]} !important;
        font-weight: 600 !important;
    }}
    div[data-testid="stExpander"] details[open] summary {{
        border-bottom: 1px solid {COLORS["card_border"]};
        margin-bottom: 8px;
        padding-bottom: 10px;
    }}

    /* Tabs */
    .stTabs [data-baseweb="tab-list"] {{
        gap: 6px;
        background: linear-gradient(135deg, {COLORS["surface2"]}, #eef2f7);
        border-radius: 14px;
        padding: 5px 6px;
        border: 1px solid {COLORS["card_border"]};
    }}
    .stTabs [data-baseweb="tab"] {{
        border-radius: 10px;
        color: {COLORS["text_muted"]};
        font-weight: 600;
        font-size: 0.84rem;
        padding: 10px 20px;
        transition: all 0.25s ease;
        letter-spacing: 0.01em;
    }}
    .stTabs [data-baseweb="tab"]:hover {{
        background: rgba(99, 102, 241, 0.06);
        color: {COLORS["text_secondary"]};
    }}
    .stTabs [aria-selected="true"] {{
        background: {COLORS["card"]} !important;
        color: {COLORS["accent"]} !important;
        box-shadow: 0 2px 8px rgba(99,102,241,0.13), {COLORS["card_shadow"]};
        border-bottom: 2px solid {COLORS["accent"]} !important;
    }}
    .stTabs [data-baseweb="tab-highlight"] {{
        display: none;
    }}
    .stTabs [data-baseweb="tab-border"] {{
        display: none;
    }}

    /* Info box in sidebar */
    .sidebar-info {{
        padding: 14px;
        background: rgba(255,255,255,0.04);
        border-radius: 12px;
        border: 1px solid rgba(255,255,255,0.08);
        margin-top: 12px;
    }}
    .sidebar-info-label {{
        font-size: 0.62rem;
        text-transform: uppercase;
        letter-spacing: 0.1em;
        color: rgba(255,255,255,0.4);
        margin-bottom: 4px;
    }}
    .sidebar-info-value {{
        font-size: 0.88rem;
        font-weight: 600;
        color: #F8FAFC;
    }}
    .sb-footer {{
        margin-top: 20px;
        padding-top: 16px;
        border-top: 1px solid rgba(255,255,255,0.06);
    }}
    .sb-avatar {{
        display: flex;
        align-items: center;
        gap: 10px;
        padding: 10px 12px;
        border-radius: 10px;
        background: rgba(255,255,255,0.04);
        border: 1px solid rgba(255,255,255,0.06);
    }}
    .sb-avatar-circle {{
        width: 34px; height: 34px;
        border-radius: 50%;
        background: linear-gradient(135deg, #3B82F6, #8B5CF6);
        display: flex;
        align-items: center;
        justify-content: center;
        color: white;
        font-weight: 700;
        font-size: 0.85rem;
    }}
    .sb-avatar-name {{
        font-size: 0.82rem;
        font-weight: 600;
        color: #F8FAFC;
    }}
    .sb-avatar-role {{
        font-size: 0.65rem;
        color: rgba(255,255,255,0.45);
    }}

    /* ===== Dashboard v2 ===== */
    .db-hero {{
        background: linear-gradient(135deg, #0F172A 0%, #1E3A5F 40%, #1E40AF 100%);
        border-radius: 20px;
        padding: 32px 36px 28px 36px;
        margin-bottom: 24px;
        position: relative;
        overflow: hidden;
        color: white;
    }}
    .db-hero-bg {{
        position: absolute;
        top: 0; left: 0; width: 100%; height: 100%;
        pointer-events: none;
        opacity: 0.12;
    }}
    .db-hero-label {{
        font-size: 0.7rem;
        font-weight: 600;
        text-transform: uppercase;
        letter-spacing: 0.1em;
        color: rgba(255,255,255,0.6);
        margin-bottom: 6px;
    }}
    .db-hero-value {{
        font-size: 2.4rem;
        font-weight: 800;
        letter-spacing: -0.02em;
        line-height: 1.1;
    }}
    .db-hero-words {{
        font-size: 0.95rem;
        font-weight: 500;
        color: rgba(255,255,255,0.7);
        margin-top: 4px;
        font-style: italic;
    }}
    .db-hero-pills {{
        display: flex;
        gap: 12px;
        margin-top: 18px;
        flex-wrap: wrap;
    }}
    .db-hero-pill {{
        background: rgba(255,255,255,0.1);
        backdrop-filter: blur(8px);
        border: 1px solid rgba(255,255,255,0.12);
        border-radius: 12px;
        padding: 12px 18px;
        min-width: 140px;
    }}
    .db-hero-pill-label {{
        font-size: 0.65rem;
        font-weight: 600;
        text-transform: uppercase;
        letter-spacing: 0.08em;
        color: rgba(255,255,255,0.55);
        margin-bottom: 4px;
    }}
    .db-hero-pill-value {{
        font-size: 1.15rem;
        font-weight: 700;
    }}
    .db-hero-pill-sub {{
        font-size: 0.72rem;
        color: rgba(255,255,255,0.5);
        margin-top: 2px;
    }}

    .db-click-card {{
        background: {COLORS["card"]};
        border: 1px solid {COLORS["card_border"]};
        border-radius: 14px;
        padding: 20px;
        box-shadow: {COLORS["card_shadow"]};
        cursor: pointer;
        transition: all 0.25s ease;
        position: relative;
        overflow: hidden;
    }}
    .db-click-card:hover {{
        transform: translateY(-3px);
        box-shadow: 0 8px 25px rgba(0,0,0,0.08);
        border-color: {COLORS["accent"]};
    }}
    .db-click-card::after {{
        content: '\u2192';
        position: absolute;
        top: 14px; right: 16px;
        font-size: 1rem;
        color: {COLORS["text_muted"]};
        opacity: 0;
        transition: opacity 0.2s ease;
    }}
    .db-click-card:hover::after {{ opacity: 1; }}

    .db-card-icon {{
        width: 42px; height: 42px;
        border-radius: 12px;
        display: flex;
        align-items: center;
        justify-content: center;
        font-size: 1.3rem;
        margin-bottom: 12px;
    }}
    .db-card-label {{
        font-size: 0.68rem;
        font-weight: 600;
        text-transform: uppercase;
        letter-spacing: 0.06em;
        color: {COLORS["text_muted"]};
        margin-bottom: 4px;
    }}
    .db-card-value {{
        font-size: 1.35rem;
        font-weight: 800;
        color: {COLORS["text"]};
        line-height: 1.2;
    }}
    .db-card-sub {{
        font-size: 0.75rem;
        color: {COLORS["text_muted"]};
        margin-top: 4px;
    }}
    .db-card-change {{
        display: inline-flex;
        align-items: center;
        gap: 3px;
        font-size: 0.72rem;
        font-weight: 600;
        padding: 2px 8px;
        border-radius: 8px;
        margin-top: 6px;
    }}
    .db-card-change.up {{
        background: {COLORS["success_light"]};
        color: {COLORS["success"]};
    }}
    .db-card-change.down {{
        background: {COLORS["danger_light"]};
        color: {COLORS["danger"]};
    }}

    .db-ai-card {{
        background: linear-gradient(135deg, #EEF2FF, #E0E7FF);
        border: 1px solid #C7D2FE;
        border-radius: 16px;
        padding: 24px;
        margin: 20px 0;
    }}
    .db-ai-badge {{
        display: inline-flex;
        align-items: center;
        gap: 6px;
        background: linear-gradient(135deg, {COLORS["accent"]}, #7C3AED);
        color: white;
        font-size: 0.68rem;
        font-weight: 700;
        text-transform: uppercase;
        letter-spacing: 0.08em;
        padding: 4px 12px;
        border-radius: 8px;
        margin-bottom: 14px;
    }}
    .db-ai-item {{
        display: flex;
        gap: 12px;
        padding: 10px 0;
        border-bottom: 1px solid rgba(99,102,241,0.12);
        align-items: flex-start;
    }}
    .db-ai-item:last-child {{ border-bottom: none; }}
    .db-ai-icon {{
        width: 28px; height: 28px;
        border-radius: 8px;
        display: flex;
        align-items: center;
        justify-content: center;
        font-size: 0.85rem;
        flex-shrink: 0;
        margin-top: 2px;
    }}
    .db-ai-text {{
        font-size: 0.88rem;
        color: {COLORS["text_secondary"]};
        line-height: 1.5;
    }}
    .db-ai-text strong {{
        color: {COLORS["text"]};
    }}

    .db-goal-track {{
        height: 8px;
        background: {COLORS["surface2"]};
        border-radius: 4px;
        overflow: hidden;
        margin-top: 8px;
    }}
    .db-goal-fill {{
        height: 100%;
        border-radius: 4px;
        transition: width 0.6s ease;
    }}

    /* ===== MOBILE RESPONSIVE ===== */
    @media (max-width: 768px) {{
        /* Base layout */
        .stApp > header {{ height: 2.5rem !important; }}
        section.main > div {{ padding: 0.5rem 0.8rem !important; }}

        /* Hero banner */
        .db-hero {{
            padding: 20px 16px 18px 16px;
            border-radius: 14px;
            margin-bottom: 16px;
        }}
        .db-hero-value {{
            font-size: 1.6rem;
        }}
        .db-hero-words {{
            font-size: 0.8rem;
        }}
        .db-hero-pills {{
            flex-direction: column;
            gap: 8px;
        }}
        .db-hero-pill {{
            padding: 10px 14px;
            min-width: unset;
        }}
        .db-hero-pill-value {{
            font-size: 1rem;
        }}

        /* Metric cards */
        .metric-row {{
            flex-direction: column;
            gap: 10px;
            margin-bottom: 16px;
        }}
        .metric-card {{
            padding: 16px 14px;
            border-radius: 12px;
        }}
        .metric-value {{
            font-size: 1.2rem;
        }}
        .metric-label {{
            font-size: 0.65rem;
        }}

        /* KPI tiles */
        .dash-kpi-grid {{
            grid-template-columns: repeat(2, 1fr);
            gap: 8px;
        }}
        .dash-kpi {{
            padding: 14px 12px;
        }}
        .dash-kpi-value {{
            font-size: 1.05rem;
        }}

        /* Click cards */
        .db-click-card {{
            padding: 16px 14px;
            border-radius: 12px;
        }}
        .db-card-value {{
            font-size: 1.1rem;
        }}
        .db-card-icon {{
            width: 36px;
            height: 36px;
            margin-bottom: 8px;
        }}

        /* AI card */
        .db-ai-card {{
            padding: 16px;
            border-radius: 12px;
        }}
        .db-ai-item {{
            gap: 8px;
            padding: 8px 0;
        }}
        .db-ai-text {{
            font-size: 0.82rem;
        }}

        /* Composition bars */
        .dash-bar-row {{
            flex-wrap: wrap;
            gap: 4px;
        }}
        .dash-bar-label {{
            min-width: 100px;
            font-size: 0.75rem;
        }}
        .dash-bar-amount {{
            min-width: 80px;
            font-size: 0.72rem;
        }}

        /* Health score */
        .dash-score-ring {{
            width: 100px;
            height: 100px;
        }}
        .dash-score-value {{
            font-size: 1.6rem;
        }}
        .dash-insight-card {{
            padding: 16px;
        }}

        /* Tables */
        .styled-table {{
            font-size: 0.75rem;
            display: block;
            overflow-x: auto;
            -webkit-overflow-scrolling: touch;
        }}
        .styled-table thead th {{
            font-size: 0.65rem;
            padding: 8px 10px;
            white-space: nowrap;
        }}
        .styled-table tbody td {{
            padding: 8px 10px;
            white-space: nowrap;
        }}

        /* Section headers */
        .section-header {{
            font-size: 0.92rem;
            margin: 18px 0 10px 0;
        }}
        .page-title {{
            font-size: 1.25rem;
        }}

        /* Tabs */
        .stTabs [data-baseweb="tab-list"] {{
            padding: 3px 4px;
            gap: 2px;
        }}
        .stTabs [data-baseweb="tab"] {{
            font-size: 0.76rem;
            padding: 8px 12px;
        }}

        /* Cards & containers */
        .card-container {{
            padding: 16px;
            border-radius: 12px;
        }}

        /* Expanders */
        .stExpander {{
            border-radius: 10px !important;
        }}

        /* Chart sizing */
        .js-plotly-plot {{
            max-width: 100% !important;
        }}

        /* Streamlit columns on mobile - stack */
        [data-testid="stHorizontalBlock"] {{
            flex-wrap: wrap;
        }}
        [data-testid="stHorizontalBlock"] > [data-testid="stColumn"] {{
            min-width: 100% !important;
            flex: 1 1 100% !important;
        }}

        /* Buttons */
        button {{
            font-size: 0.82rem !important;
            padding: 8px 14px !important;
        }}

        /* Forms */
        .stTextInput > div > div > input,
        .stNumberInput > div > div > input,
        .stSelectbox > div > div,
        .stDateInput > div > div > input {{
            font-size: 16px !important; /* prevents iOS zoom on focus */
        }}
    }}

    /* Tablet */
    @media (min-width: 769px) and (max-width: 1024px) {{
        .db-hero-pills {{
            flex-wrap: wrap;
        }}
        .dash-kpi-grid {{
            grid-template-columns: repeat(3, 1fr);
        }}
        .metric-value {{
            font-size: 1.3rem;
        }}
    }}
</style>
""", unsafe_allow_html=True)


# --- Chart Theme ---
def apply_chart_theme(fig, height=400, **overrides):
    """Apply consistent chart theme. Pass any layout overrides as kwargs."""
    base = dict(
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        font=dict(family="Inter, -apple-system, sans-serif", color=COLORS["text_muted"], size=12),
        margin=dict(t=24, b=40, l=48, r=16),
        xaxis=dict(gridcolor="#E2E8F0", gridwidth=1, zeroline=False, linecolor=COLORS["card_border"]),
        yaxis=dict(gridcolor="#E2E8F0", gridwidth=1, zeroline=False, linecolor=COLORS["card_border"]),
        legend=dict(
            bgcolor="rgba(0,0,0,0)", font=dict(size=11, color=COLORS["text_secondary"]),
            orientation="h", yanchor="bottom", y=1.02, xanchor="left", x=0,
        ),
        hovermode="x unified",
        hoverlabel=dict(bgcolor=COLORS["white"], font_size=12, font_color=COLORS["text"],
                        bordercolor=COLORS["card_border"]),
        height=height,
    )
    # Merge overrides: for nested dicts like xaxis/yaxis/legend, update rather than replace
    for key, val in overrides.items():
        if key in base and isinstance(base[key], dict) and isinstance(val, dict):
            base[key].update(val)
        else:
            base[key] = val
    fig.update_layout(**base)
    return fig


def fmt_inr(amount):
    if amount is None:
        return "N/A"
    sign = "-" if amount < 0 else ""
    amount = abs(amount)
    if amount >= 10000000:
        return f"{sign}{amount/10000000:.2f} Cr"
    elif amount >= 100000:
        return f"{sign}{amount/100000:.2f} L"
    elif amount >= 1000:
        return f"{sign}{amount/1000:.2f} K"
    return f"{sign}{amount:,.2f}"


def fmt_inr_full(amount):
    if amount is None:
        return "N/A"
    s = f"{amount:,.2f}"
    return f"Rs. {s}"


def fmt_inr_words(amount):
    """Convert amount to Indian words: Crore, Lakh, Thousand."""
    if amount is None:
        return ""
    sign = "Minus " if amount < 0 else ""
    amount = abs(amount)
    if amount >= 10000000:
        cr = amount / 10000000
        return f"{sign}{cr:.2f} Crore"
    elif amount >= 100000:
        lakh = amount / 100000
        return f"{sign}{lakh:.2f} Lakh"
    elif amount >= 1000:
        k = amount / 1000
        return f"{sign}{k:.2f} Thousand"
    return f"{sign}{amount:.2f}"


def render_metric_card(label, value, sub="", style="blue", icon=""):
    sub_html = f'<div class="metric-sub">{sub}</div>' if sub else ''
    # Auto-detect if value looks like a rupee amount and add words
    words_html = ''
    if value and value.startswith("Rs."):
        try:
            num = float(value.replace("Rs.", "").replace(",", "").strip())
            if abs(num) >= 1000:
                words_html = f'<div class="metric-words">{fmt_inr_words(num)}</div>'
        except ValueError:
            pass
    return (
        f'<div class="metric-card {style}">'
        f'<div class="metric-icon">{icon}</div>'
        f'<div class="metric-label">{label}</div>'
        f'<div class="metric-value">{value}</div>'
        f'{words_html}'
        f'{sub_html}'
        f'</div>'
    )


def metric_row(*cards):
    """Render a row of metric cards. Each card is a tuple: (label, value, sub, style, icon)."""
    html = '<div class="metric-row">'
    for card in cards:
        html += render_metric_card(*card)
    html += '</div>'
    st.markdown(html, unsafe_allow_html=True)


def section_header(text, icon=""):
    st.markdown(f'<div class="section-header"><span class="icon">{icon}</span> {text}</div>', unsafe_allow_html=True)


def page_title(title, subtitle=""):
    st.markdown(f'<div class="page-title">{title}</div>', unsafe_allow_html=True)
    if subtitle:
        st.markdown(f'<div class="page-subtitle">{subtitle}</div>', unsafe_allow_html=True)


def insight_box(items, title="Financial Insights"):
    """Render a styled insight box with bullet points. Each item is a string."""
    bullets = "".join(f'<li style="padding:5px 0;font-size:0.88rem;color:{COLORS["text_secondary"]};line-height:1.5">{i}</li>' for i in items)
    st.markdown(f"""
    <div style="background:linear-gradient(135deg,{COLORS['surface']},%23f0f4ff);border:1px solid {COLORS['card_border']};
        border-radius:14px;padding:20px 24px;margin:16px 0;border-left:4px solid {COLORS['accent']}">
        <div style="font-size:0.72rem;font-weight:700;text-transform:uppercase;letter-spacing:0.06em;
            color:{COLORS['accent']};margin-bottom:10px">{title}</div>
        <ul style="margin:0;padding-left:20px;list-style:none">{bullets}</ul>
    </div>
    """, unsafe_allow_html=True)


# --- Sidebar ---
_nav_pages = ["Dashboard", "Bank Update", "Digital Wallet", "Manage Sources", "History & Analytics", "Gold Portfolio", "Gold Schemes", "Shares & Stock", "SIP & MF Portfolio", "Policies", "Lent Out"]

# Handle programmatic navigation from dashboard cards
if "nav_page" in st.session_state and st.session_state["nav_page"] in _nav_pages:
    if "sb_active" not in st.session_state or st.session_state["sb_active"] != st.session_state["nav_page"]:
        st.session_state["sb_active"] = st.session_state["nav_page"]
    del st.session_state["nav_page"]

if "sb_active" not in st.session_state:
    st.session_state["sb_active"] = "Dashboard"

# --- Sidebar nav items grouped ---
_nav_groups = [
    ("", [("Dashboard", "\U0001f3e0")]),
    ("BANKING", [("Bank Update", "\U0001f3e6"), ("Digital Wallet", "\U0001f4f1")]),
    ("INVESTMENTS", [
        ("Gold Portfolio", "\u2728"), ("Gold Schemes", "\U0001f48e"),
        ("Shares & Stock", "\U0001f4ca"), ("SIP & MF Portfolio", "\U0001f4c8"),
        ("Policies", "\U0001f6e1"),
    ]),
    ("OTHER", [
        ("Lent Out", "\U0001f91d"), ("History & Analytics", "\U0001f4c5"),
        ("Manage Sources", "\u2699"),
    ]),
]

st.sidebar.markdown(
    '<div class="nav-brand">\U0001f4b0 <span class="accent">Finance</span> Tracker</div>',
    unsafe_allow_html=True,
)

for section_label, items in _nav_groups:
    if section_label:
        st.sidebar.markdown(f'<div class="sb-section">{section_label}</div>', unsafe_allow_html=True)
    for pg_name, icon in items:
        is_active = (st.session_state["sb_active"] == pg_name)
        btn_label = f"{icon}  {pg_name}"
        if st.sidebar.button(btn_label, key=f"sb_{pg_name}", use_container_width=True,
                             type="primary" if is_active else "secondary"):
            st.session_state["sb_active"] = pg_name
            st.rerun()

page = st.session_state["sb_active"]

# Footer
st.sidebar.markdown(
    '<div class="sb-footer">'
    '<div class="sidebar-info">'
    f'<div class="sidebar-info-label">Last Updated</div>'
    f'<div class="sidebar-info-value">{date.today().strftime("%d %B %Y")}</div>'
    '</div>'
    '<div style="height:10px"></div>'
    '<div class="sb-avatar">'
    '<div class="sb-avatar-circle">G</div>'
    '<div><div class="sb-avatar-name">My Finance</div>'
    '<div class="sb-avatar-role">Personal Portfolio</div></div>'
    '</div>'
    '</div>',
    unsafe_allow_html=True,
)


# ===========================
# DASHBOARD PAGE
# ===========================
if page == "Dashboard":
    # Auto-sync balances from individual trackers on dashboard load
    _rate_row = db.get_latest_exchange_rate()
    _usd_rate = _rate_row["rate"] if _rate_row else None
    db.sync_balances_from_trackers(usd_inr_rate=_usd_rate)

    # --- Date selector ---
    col_date, _ = st.columns([1, 4])
    with col_date:
        view_date = st.date_input("View as of", value=date.today(), max_value=date.today(), label_visibility="collapsed")

    snapshot = db.get_snapshot_on_date(view_date.isoformat())
    df = pd.DataFrame([dict(r) for r in snapshot])

    if df.empty:
        st.warning("No data available. Go to 'Bank Update' to add entries.")
        st.stop()

    total = df["balance"].sum()
    liquid = df[df["liquidity"] == "Liquid"]["balance"].sum()
    non_liquid = df[df["liquidity"] == "Non-Liquid"]["balance"].sum()
    active_sources = len(df[df["balance"] > 0])
    liquid_pct = (liquid / total * 100) if total > 0 else 0

    # --- Category totals ---
    cat_totals = df.groupby("category")["balance"].sum().to_dict()
    bank_total = cat_totals.get("Bank Account", 0)
    fd_rd_total = cat_totals.get("Fixed Deposit/RD", 0)
    mf_total = cat_totals.get("Mutual Funds", 0)
    equity_total = cat_totals.get("Equity", 0)
    gold_total = cat_totals.get("Gold", 0)
    insurance_total = cat_totals.get("Insurance", 0)
    receivables_total = cat_totals.get("Receivables", 0)
    wallet_total = cat_totals.get("Digital Wallet", 0)

    bar_colors = {
        "Gold": "#F59E0B", "Bank Account": "#2563EB", "Insurance": "#8B5CF6",
        "Mutual Funds": "#10B981", "Fixed Deposit/RD": "#0EA5E9", "Equity": "#EC4899",
        "Digital Wallet": "#F97316", "Receivables": "#6366F1",
    }

    # --- Month-over-month change ---
    monthly = db.get_monthly_summary()
    mom_change = 0
    mom_pct = 0
    if monthly and len(monthly) >= 2:
        prev_month_total = monthly[-2]["total"]
        current_month_total = monthly[-1]["total"]
        mom_change = current_month_total - prev_month_total
        mom_pct = (mom_change / prev_month_total * 100) if prev_month_total > 0 else 0

    # --- Growth data ---
    daily = db.get_daily_totals()
    first_total = 0
    last_total = total
    overall_growth = 0
    overall_growth_pct = 0
    if daily:
        trend_df = pd.DataFrame([dict(r) for r in daily])
        trend_df["update_date"] = pd.to_datetime(trend_df["update_date"])
        first_total = trend_df["total"].iloc[0] if len(trend_df) > 0 else 0
        last_total = trend_df["total"].iloc[-1] if len(trend_df) > 0 else total
        overall_growth = last_total - first_total
        overall_growth_pct = (overall_growth / first_total * 100) if first_total > 0 else 0

    # --- Navigation helper ---
    _dash_nav_map = {
        "Bank Account": "Bank Update", "Fixed Deposit/RD": "Bank Update",
        "Mutual Funds": "SIP & MF Portfolio", "Equity": "Shares & Stock",
        "Gold": "Gold Portfolio", "Insurance": "Policies",
        "Receivables": "Lent Out", "Digital Wallet": "Digital Wallet",
    }

    # ============================================================
    # HERO BANNER — Net Worth Command Centre
    # ============================================================
    mom_arrow = "+" if mom_change >= 0 else ""
    mom_color_cls = "up" if mom_change >= 0 else "down"
    growth_arrow = "+" if overall_growth >= 0 else ""

    _hero_svg = (
        '<svg class="db-hero-bg" viewBox="0 0 800 260" xmlns="http://www.w3.org/2000/svg">'
        '<defs>'
        '<linearGradient id="hg1" x1="0" y1="0" x2="1" y2="1">'
        '<stop offset="0%" stop-color="#3B82F6" stop-opacity="0.3"/>'
        '<stop offset="100%" stop-color="#8B5CF6" stop-opacity="0.1"/>'
        '</linearGradient>'
        '<linearGradient id="hg2" x1="0" y1="1" x2="1" y2="0">'
        '<stop offset="0%" stop-color="#06B6D4" stop-opacity="0.25"/>'
        '<stop offset="100%" stop-color="#3B82F6" stop-opacity="0.05"/>'
        '</linearGradient>'
        '</defs>'
        '<circle cx="720" cy="40" r="140" fill="url(#hg1)"/>'
        '<circle cx="650" cy="200" r="80" fill="url(#hg2)"/>'
        '<circle cx="80" cy="220" r="100" fill="url(#hg1)" opacity="0.5"/>'
        '<path d="M0 200 Q200 120 400 170 T800 130 L800 260 L0 260Z" fill="rgba(59,130,246,0.08)"/>'
        '<path d="M0 230 Q150 180 350 210 T800 180 L800 260 L0 260Z" fill="rgba(139,92,246,0.06)"/>'
        '<line x1="100" y1="60" x2="250" y2="60" stroke="rgba(255,255,255,0.06)" stroke-width="1"/>'
        '<line x1="500" y1="30" x2="700" y2="30" stroke="rgba(255,255,255,0.04)" stroke-width="1"/>'
        '<rect x="680" y="80" width="40" height="50" rx="4" fill="rgba(96,165,250,0.15)"/>'
        '<rect x="725" y="60" width="40" height="70" rx="4" fill="rgba(96,165,250,0.1)"/>'
        '<rect x="635" y="95" width="40" height="35" rx="4" fill="rgba(96,165,250,0.1)"/>'
        '</svg>'
    )
    _num_classes = len([c for c, v in cat_totals.items() if v > 0])
    _mom_pill_color = "#6EE7B7" if mom_change >= 0 else "#FCA5A5"
    _nlliq_pct = 100 - liquid_pct

    st.markdown(
        '<div class="db-hero">'
        + _hero_svg +
        '<div style="position:relative;z-index:1;">'
        '<div class="db-hero-label">Total Net Worth</div>'
        f'<div class="db-hero-value">{fmt_inr_full(total)}</div>'
        f'<div class="db-hero-words">{fmt_inr_words(total)}</div>'
        '<div class="db-hero-pills">'
        '<div class="db-hero-pill">'
        '<div class="db-hero-pill-label">Liquid Assets</div>'
        f'<div class="db-hero-pill-value" style="color:#6EE7B7;">{fmt_inr(liquid)}</div>'
        f'<div class="db-hero-pill-sub">{liquid_pct:.1f}% of portfolio</div>'
        '</div>'
        '<div class="db-hero-pill">'
        '<div class="db-hero-pill-label">Non-Liquid Assets</div>'
        f'<div class="db-hero-pill-value" style="color:#FCD34D;">{fmt_inr(non_liquid)}</div>'
        f'<div class="db-hero-pill-sub">{_nlliq_pct:.1f}% of portfolio</div>'
        '</div>'
        '<div class="db-hero-pill">'
        '<div class="db-hero-pill-label">Month-on-Month</div>'
        f'<div class="db-hero-pill-value" style="color:{_mom_pill_color};">{mom_arrow}{fmt_inr(mom_change)}</div>'
        f'<div class="db-hero-pill-sub">{mom_pct:+.1f}% vs last month</div>'
        '</div>'
        '<div class="db-hero-pill">'
        '<div class="db-hero-pill-label">Active Sources</div>'
        f'<div class="db-hero-pill-value">{active_sources}</div>'
        f'<div class="db-hero-pill-sub">across {_num_classes} asset classes</div>'
        '</div>'
        '</div></div></div>',
        unsafe_allow_html=True,
    )

    # ============================================================
    # PORTFOLIO CARDS — Clickable tiles for each asset class
    # ============================================================
    _card_meta = [
        ("Bank Account", "bank_total", bank_total, "#2563EB", "#DBEAFE", "Bank Accounts", "Savings & current accounts"),
        ("Fixed Deposit/RD", "fd_rd_total", fd_rd_total, "#0EA5E9", "#E0F2FE", "FDs & RDs", "Fixed & recurring deposits"),
        ("Mutual Funds", "mf_total", mf_total, "#10B981", "#D1FAE5", "Mutual Funds", "SIPs & lump-sum MFs"),
        ("Equity", "equity_total", equity_total, "#EC4899", "#FCE7F3", "Shares & Stock", "Indian + US markets"),
        ("Gold", "gold_total", gold_total, "#F59E0B", "#FEF3C7", "Gold Holdings", "Physical + Schemes"),
        ("Insurance", "insurance_total", insurance_total, "#8B5CF6", "#EDE9FE", "Insurance", "Policy fund value"),
        ("Digital Wallet", "wallet_total", wallet_total, "#F97316", "#FFF7ED", "Digital Wallet", "Amazon, Airtel, Neo Pay"),
        ("Receivables", "receivables_total", receivables_total, "#6366F1", "#E0E7FF", "Lent Out", "Outstanding receivables"),
    ]
    # Filter to only categories with value
    _active_cards = [c for c in _card_meta if c[2] > 0]

    # Use Streamlit columns for clickable navigation
    card_cols = st.columns(min(len(_active_cards), 4))
    for idx, (cat, _key, amt, color, bg, label, sub) in enumerate(_active_cards):
        col_idx = idx % min(len(_active_cards), 4)
        pct = (amt / total * 100) if total > 0 else 0
        count = len([s for s in snapshot if s["category"] == cat and s["balance"] > 0])
        count_label = f"{count} source{'s' if count != 1 else ''}"
        with card_cols[col_idx]:
            st.markdown(f"""
            <div class="db-click-card">
                <div class="db-card-icon" style="background:{bg};color:{color};">
                    <span style="font-size:1.2rem;">{"&#x1f3e6;" if cat == "Bank Account" else "&#x1f4b3;" if cat == "Fixed Deposit/RD" else "&#x1f4c8;" if cat == "Mutual Funds" else "&#x1f4ca;" if cat == "Equity" else "&#x2728;" if cat == "Gold" else "&#x1f6e1;" if cat == "Insurance" else "&#x1f4f1;" if cat == "Digital Wallet" else "&#x1f91d;"}</span>
                </div>
                <div class="db-card-label">{label}</div>
                <div class="db-card-value">{fmt_inr(amt)}</div>
                <div class="db-card-sub">{count_label} &middot; {pct:.1f}% of portfolio</div>
            </div>
            """, unsafe_allow_html=True)
            target_page = _dash_nav_map.get(cat)
            if target_page:
                if st.button(f"View {label}", key=f"db_nav_{cat}", use_container_width=True):
                    st.session_state["nav_page"] = target_page
                    st.rerun()
        # Start a new row after every 4 cards
        if col_idx == min(len(_active_cards), 4) - 1 and idx < len(_active_cards) - 1:
            card_cols = st.columns(min(len(_active_cards) - idx - 1, 4))

    st.markdown("<div style='height:8px'></div>", unsafe_allow_html=True)

    # ============================================================
    # AI INSIGHTS — Smart financial analysis
    # ============================================================
    categories_with_value = len([c for c, v in cat_totals.items() if v > 0])
    low_risk = bank_total + fd_rd_total + insurance_total
    medium_risk = mf_total + gold_total + wallet_total
    high_risk = equity_total + receivables_total
    risk_total = low_risk + medium_risk + high_risk

    ai_insights = []

    # Diversification insight
    if categories_with_value <= 2:
        ai_insights.append(("&#x26A0;", COLORS["warning_light"], COLORS["warning"],
            "<strong>Low Diversification:</strong> Your wealth is concentrated in only "
            f"{categories_with_value} asset class{'es' if categories_with_value > 1 else ''}. "
            "Consider spreading across 4-5 categories to reduce risk."))
    elif categories_with_value >= 5:
        ai_insights.append(("&#x2705;", COLORS["success_light"], COLORS["success"],
            f"<strong>Well Diversified:</strong> Your portfolio spans {categories_with_value} asset classes. "
            "This is excellent for risk management."))

    # Liquidity insight
    if liquid_pct > 70:
        ai_insights.append(("&#x1f4a1;", "#FEF3C7", COLORS["warning"],
            f"<strong>High Liquidity ({liquid_pct:.0f}%):</strong> "
            "A large portion is in liquid form. Consider moving some into growth assets "
            "(MFs, Gold, Equity) for better long-term returns."))
    elif liquid_pct < 20:
        ai_insights.append(("&#x26A0;", COLORS["danger_light"], COLORS["danger"],
            f"<strong>Low Liquidity ({liquid_pct:.0f}%):</strong> "
            "Your emergency fund may be insufficient. Aim for at least 3-6 months of "
            "expenses in liquid assets."))
    else:
        ai_insights.append(("&#x2705;", COLORS["success_light"], COLORS["success"],
            f"<strong>Healthy Liquidity ({liquid_pct:.0f}%):</strong> "
            "Good balance between liquid and invested assets."))

    # Growth insight
    if mom_change > 0:
        ai_insights.append(("&#x1f4c8;", COLORS["success_light"], COLORS["success"],
            f"<strong>Positive Momentum:</strong> Your net worth grew by {fmt_inr(mom_change)} "
            f"({mom_pct:+.1f}%) this month. {'Great progress!' if mom_pct > 2 else 'Steady growth.'}"))
    elif mom_change < 0:
        ai_insights.append(("&#x1f4c9;", COLORS["danger_light"], COLORS["danger"],
            f"<strong>Decline Alert:</strong> Net worth dropped by {fmt_inr(abs(mom_change))} "
            f"({mom_pct:.1f}%) this month. Review recent transactions to understand the cause."))

    # Risk profile insight
    if risk_total > 0:
        low_pct = low_risk / risk_total * 100
        high_pct = high_risk / risk_total * 100
        if high_pct > 50:
            ai_insights.append(("&#x1f525;", COLORS["danger_light"], COLORS["danger"],
                f"<strong>Aggressive Portfolio ({high_pct:.0f}% high-risk):</strong> "
                "Heavy allocation to stocks and receivables. Ensure you have adequate "
                "safe assets for stability."))
        elif low_pct > 70:
            ai_insights.append(("&#x1f4a1;", "#FEF3C7", COLORS["warning"],
                f"<strong>Conservative Portfolio ({low_pct:.0f}% low-risk):</strong> "
                "Most of your wealth is in safe assets. Consider allocating 15-25% to "
                "growth assets for inflation-beating returns."))

    # Concentration risk — top holding
    if len(df[df["balance"] > 0]) > 0:
        top_source = df[df["balance"] > 0].sort_values("balance", ascending=False).iloc[0]
        top_pct = (top_source["balance"] / total * 100) if total > 0 else 0
        top_name = top_source["name"]
        if top_pct > 40:
            ai_insights.append(("&#x26A0;", "#FEF3C7", COLORS["warning"],
                f"<strong>Concentration Risk:</strong> {top_name} holds {top_pct:.1f}% of your "
                "entire portfolio. Consider rebalancing to avoid overexposure to a single source."))

    # FD maturity / gold opportunity
    if gold_total > 0 and gold_total / total * 100 > 25:
        ai_insights.append(("&#x2728;", COLORS["gold_light"], COLORS["gold"],
            f"<strong>Gold Heavy ({gold_total / total * 100:.0f}%):</strong> "
            "Gold is a solid hedge, but it doesn't generate income. "
            "Balance with dividend-paying or interest-bearing instruments."))

    if fd_rd_total > 0 and bank_total > 0 and bank_total > fd_rd_total * 2:
        ai_insights.append(("&#x1f4a1;", "#DBEAFE", "#2563EB",
            "<strong>Savings Opportunity:</strong> You have significantly more in savings accounts "
            "than FDs. Moving surplus to FDs or liquid MFs could earn better interest."))

    # Render AI insights
    ai_items_html = ""
    for icon, bg, color, text in ai_insights:
        ai_items_html += (
            '<div class="db-ai-item">'
            f'<div class="db-ai-icon" style="background:{bg};color:{color};">{icon}</div>'
            f'<div class="db-ai-text">{text}</div>'
            '</div>'
        )

    st.markdown(
        '<div class="db-ai-card">'
        '<div class="db-ai-badge">&#x2728; AI Financial Advisor</div>'
        + ai_items_html +
        '</div>',
        unsafe_allow_html=True,
    )

    # ============================================================
    # TABS — Overview | Analytics | Deep Dive
    # ============================================================
    db_tab1, db_tab2, db_tab3 = st.tabs(["Overview", "Analytics", "Deep Dive"])

    # ============ TAB 1: OVERVIEW ============
    with db_tab1:
        col_health, col_composition = st.columns([1, 2])

        with col_health:
            # --- Financial Health Score ---
            diversification_score = min(categories_with_value * 12, 40)
            liquidity_score = min(liquid_pct * 0.5, 30)
            savings_score = min(bank_total / max(total, 1) * 100 * 0.3, 15)
            investment_score = min((mf_total + equity_total + gold_total) / max(total, 1) * 100 * 0.2, 15)
            health_score = int(min(diversification_score + liquidity_score + savings_score + investment_score, 100))

            if health_score >= 80:
                score_color, score_bg, score_label = COLORS["success"], COLORS["success_light"], "Excellent"
            elif health_score >= 60:
                score_color, score_bg, score_label = "#2563EB", "#DBEAFE", "Good"
            elif health_score >= 40:
                score_color, score_bg, score_label = COLORS["warning"], COLORS["warning_light"], "Fair"
            else:
                score_color, score_bg, score_label = COLORS["danger"], COLORS["danger_light"], "Needs Work"

            mom_sign = "+" if mom_change >= 0 else ""
            mom_color = COLORS["success"] if mom_change >= 0 else COLORS["danger"]

            st.markdown(f"""
            <div class="dash-insight-card" style="text-align:center;">
                <div class="dash-insight-title">Financial Health Score</div>
                <div class="dash-score-ring" style="background:{score_bg};border:4px solid {score_color};">
                    <div class="dash-score-value" style="color:{score_color};">{health_score}</div>
                    <div class="dash-score-label" style="color:{score_color};">{score_label}</div>
                </div>
                <div style="display:grid;grid-template-columns:1fr 1fr;gap:8px;text-align:left;margin-top:12px;">
                    <div style="font-size:0.75rem;color:{COLORS['text_muted']};">Diversification</div>
                    <div style="font-size:0.75rem;font-weight:600;color:{COLORS['text']};text-align:right;">{categories_with_value} classes</div>
                    <div style="font-size:0.75rem;color:{COLORS['text_muted']};">Liquidity Ratio</div>
                    <div style="font-size:0.75rem;font-weight:600;color:{COLORS['text']};text-align:right;">{liquid_pct:.0f}%</div>
                    <div style="font-size:0.75rem;color:{COLORS['text_muted']};">Active Sources</div>
                    <div style="font-size:0.75rem;font-weight:600;color:{COLORS['text']};text-align:right;">{active_sources} / {len(df)}</div>
                    <div style="font-size:0.75rem;color:{COLORS['text_muted']};">MoM Change</div>
                    <div style="font-size:0.75rem;font-weight:600;color:{mom_color};text-align:right;">
                        {mom_sign}{fmt_inr(mom_change)} ({mom_pct:+.1f}%)
                    </div>
                </div>
            </div>
            """, unsafe_allow_html=True)

        with col_composition:
            st.markdown(f'<div class="dash-insight-card"><div class="dash-insight-title">Portfolio Composition</div>', unsafe_allow_html=True)
            composition_html = ""
            sorted_cats = sorted(cat_totals.items(), key=lambda x: x[1], reverse=True)
            for cat, amt in sorted_cats:
                if amt <= 0:
                    continue
                pct = (amt / total * 100) if total > 0 else 0
                color = bar_colors.get(cat, COLORS["primary"])
                composition_html += f"""
                <div class="dash-bar-row">
                    <div class="dash-bar-label">{cat}</div>
                    <div class="dash-bar-track">
                        <div class="dash-bar-fill" style="width:{pct}%;background:{color};"></div>
                    </div>
                    <div class="dash-bar-amount">{fmt_inr(amt)}</div>
                    <div style="font-size:0.72rem;color:{COLORS['text_muted']};min-width:42px;text-align:right;">{pct:.1f}%</div>
                </div>"""
            st.markdown(f'{composition_html}</div>', unsafe_allow_html=True)

        # --- Asset Allocation + Top Holdings ---
        col_pie, col_top = st.columns([1, 2])

        with col_pie:
            section_header("Asset Allocation", "&#x25CE;")
            pie_cats = df.groupby("category")["balance"].sum().reset_index()
            pie_cats = pie_cats[pie_cats["balance"] > 0].sort_values("balance", ascending=False)
            cat_colors_list = [bar_colors.get(c, COLORS["primary"]) for c in pie_cats["category"]]

            fig = px.pie(pie_cats, values="balance", names="category",
                         color_discrete_sequence=cat_colors_list, hole=0.6)
            fig.update_traces(
                textinfo="percent", textfont=dict(size=12, color=COLORS["text"]),
                marker=dict(line=dict(color=COLORS["white"], width=2)),
                hovertemplate="<b>%{label}</b><br>Rs. %{value:,.0f}<br>%{percent}<extra></extra>",
            )
            nw_label = fmt_inr(total)
            apply_chart_theme(fig, height=360, showlegend=True,
                legend=dict(orientation="h", yanchor="bottom", y=-0.15, xanchor="center", x=0.5,
                            font=dict(size=10, color=COLORS["text_secondary"]), bgcolor="rgba(0,0,0,0)"),
                annotations=[dict(
                    text=f"<b>{nw_label}</b><br><span style='font-size:10px;color:{COLORS['text_muted']}'>Net Worth</span>",
                    x=0.5, y=0.5, font=dict(size=16, color=COLORS["text"]), showarrow=False,
                )],
            )
            st.plotly_chart(fig, use_container_width=True)

        with col_top:
            section_header("Top Holdings", "&#x1f3c6;")
            top_df = df[df["balance"] > 0].sort_values("balance", ascending=False).head(10)
            table_rows = ""
            rank = 1
            for _, row in top_df.iterrows():
                pct = (row["balance"] / total * 100) if total > 0 else 0
                badge_class = "badge-liquid" if row["liquidity"] == "Liquid" else "badge-nonliquid"
                b_color = bar_colors.get(row["category"], COLORS["primary"])
                table_rows += f"""
                <tr>
                    <td style="font-weight:700;color:{COLORS['text_muted']};text-align:center;font-size:0.85rem;">{rank}</td>
                    <td><span style="font-weight:600;color:{COLORS['text']}">{row['name']}</span>
                        <div style="font-size:0.7rem;color:{COLORS['text_muted']}">{row['category']}</div></td>
                    <td><span class="badge {badge_class}">{row['liquidity']}</span></td>
                    <td class="amount">{fmt_inr_full(row['balance'])}</td>
                    <td>
                        <div style="display:flex;align-items:center;gap:6px;">
                            <div style="flex:1;height:6px;background:{COLORS['surface2']};border-radius:3px;overflow:hidden;">
                                <div style="width:{pct}%;height:100%;background:{b_color};border-radius:3px;"></div>
                            </div>
                            <span style="font-size:0.72rem;color:{COLORS['text_muted']};min-width:38px;text-align:right;">{pct:.1f}%</span>
                        </div>
                    </td>
                </tr>"""
                rank += 1

            st.markdown(f"""
            <table class="styled-table">
                <thead><tr><th style="width:40px;">#</th><th>Source</th><th>Type</th><th>Balance</th><th style="min-width:140px;">Share</th></tr></thead>
                <tbody>{table_rows}</tbody>
            </table>
            """, unsafe_allow_html=True)

        # --- Liquidity Split + Risk Profile ---
        col_liq, col_risk = st.columns(2)

        with col_liq:
            section_header("Liquidity Split", "&#x1f4a7;")
            liq_data = pd.DataFrame({"Type": ["Liquid", "Non-Liquid"], "Amount": [liquid, non_liquid]})
            fig = px.pie(liq_data, values="Amount", names="Type",
                         color_discrete_map={"Liquid": COLORS["success"], "Non-Liquid": COLORS["warning"]},
                         hole=0.65)
            fig.update_traces(
                textinfo="percent+label", textfont=dict(size=12, color=COLORS["text"]),
                marker=dict(line=dict(color=COLORS["white"], width=3)),
                hovertemplate="<b>%{label}</b><br>Rs. %{value:,.0f}<br>%{percent}<extra></extra>",
            )
            apply_chart_theme(fig, height=320, showlegend=False,
                annotations=[dict(
                    text=f"<b>{liquid_pct:.0f}%</b><br><span style='font-size:10px'>Liquid</span>",
                    x=0.5, y=0.5, font=dict(size=20, color=COLORS["success"]), showarrow=False,
                )],
            )
            st.plotly_chart(fig, use_container_width=True)

        with col_risk:
            section_header("Risk Profile", "&#x1f6e1;")
            risk_data = pd.DataFrame({
                "Risk Level": ["Low Risk", "Medium Risk", "High Risk"],
                "Amount": [low_risk, medium_risk, high_risk],
            })
            risk_data = risk_data[risk_data["Amount"] > 0]
            risk_colors = {"Low Risk": "#10B981", "Medium Risk": "#F59E0B", "High Risk": "#EF4444"}
            fig = px.bar(risk_data, x="Risk Level", y="Amount",
                         color="Risk Level", color_discrete_map=risk_colors, text="Amount")
            fig.update_traces(
                texttemplate="%{text:,.0f}", textposition="outside",
                textfont=dict(size=11, color=COLORS["text_secondary"]),
                marker=dict(cornerradius=8, line=dict(width=0)),
                hovertemplate="<b>%{x}</b><br>Rs. %{y:,.0f}<extra></extra>",
            )
            apply_chart_theme(fig, height=320, showlegend=False,
                xaxis=dict(title="", tickfont=dict(color=COLORS["text"])),
                yaxis=dict(title="Amount (Rs.)", tickfont=dict(color=COLORS["text"])))
            st.plotly_chart(fig, use_container_width=True)

            if risk_total > 0:
                low_r_pct = low_risk / risk_total * 100
                med_r_pct = medium_risk / risk_total * 100
                high_r_pct = high_risk / risk_total * 100
                st.markdown(f"""
                <div style="display:flex;gap:12px;justify-content:center;margin-top:-10px;">
                    <div style="text-align:center;"><span style="font-size:1.1rem;font-weight:700;color:#10B981">{low_r_pct:.0f}%</span>
                        <div style="font-size:0.68rem;color:{COLORS['text_muted']}">Low Risk</div></div>
                    <div style="text-align:center;"><span style="font-size:1.1rem;font-weight:700;color:#F59E0B">{med_r_pct:.0f}%</span>
                        <div style="font-size:0.68rem;color:{COLORS['text_muted']}">Medium Risk</div></div>
                    <div style="text-align:center;"><span style="font-size:1.1rem;font-weight:700;color:#EF4444">{high_r_pct:.0f}%</span>
                        <div style="font-size:0.68rem;color:{COLORS['text_muted']}">High Risk</div></div>
                </div>
                """, unsafe_allow_html=True)

    # ============ TAB 2: ANALYTICS ============
    with db_tab2:
        # --- Net Worth Trend ---
        section_header("Net Worth Trend", "&#x1f4c8;")
        if daily:
            growth_cols = st.columns(4)
            with growth_cols[0]:
                start_dt = trend_df["update_date"].iloc[0].strftime("%d %b %Y") if len(trend_df) > 0 else "-"
                st.markdown(f"""<div class="dash-kpi" style="border-left:3px solid {COLORS['primary']};">
                    <div class="dash-kpi-label">Starting Value</div>
                    <div class="dash-kpi-value">{fmt_inr(first_total)}</div>
                    <div class="dash-kpi-sub">{start_dt}</div>
                </div>""", unsafe_allow_html=True)
            with growth_cols[1]:
                end_dt = trend_df["update_date"].iloc[-1].strftime("%d %b %Y") if len(trend_df) > 0 else "-"
                st.markdown(f"""<div class="dash-kpi" style="border-left:3px solid {COLORS['success']};">
                    <div class="dash-kpi-label">Current Value</div>
                    <div class="dash-kpi-value">{fmt_inr(last_total)}</div>
                    <div class="dash-kpi-sub">{end_dt}</div>
                </div>""", unsafe_allow_html=True)
            with growth_cols[2]:
                g_color = COLORS["success"] if overall_growth >= 0 else COLORS["danger"]
                g_sign = "+" if overall_growth >= 0 else ""
                st.markdown(f"""<div class="dash-kpi" style="border-left:3px solid {g_color};">
                    <div class="dash-kpi-label">Total Growth</div>
                    <div class="dash-kpi-value" style="color:{g_color}">{g_sign}{fmt_inr(overall_growth)}</div>
                    <div class="dash-kpi-sub">{overall_growth_pct:+.1f}% overall</div>
                </div>""", unsafe_allow_html=True)
            with growth_cols[3]:
                m_color = COLORS["success"] if mom_change >= 0 else COLORS["danger"]
                m_sign = "+" if mom_change >= 0 else ""
                st.markdown(f"""<div class="dash-kpi" style="border-left:3px solid {m_color};">
                    <div class="dash-kpi-label">Month-on-Month</div>
                    <div class="dash-kpi-value" style="color:{m_color}">{m_sign}{fmt_inr(mom_change)}</div>
                    <div class="dash-kpi-sub">{mom_pct:+.1f}% vs last month</div>
                </div>""", unsafe_allow_html=True)

            fig = go.Figure()
            fig.add_trace(go.Scatter(
                x=trend_df["update_date"], y=trend_df["total"],
                mode="lines+markers", name="Total",
                line=dict(color=COLORS["accent"], width=3, shape="spline"),
                marker=dict(size=7, color=COLORS["accent"], line=dict(width=2, color=COLORS["white"])),
                fill="tozeroy", fillcolor="rgba(37,99,235,0.07)",
            ))
            fig.add_trace(go.Scatter(
                x=trend_df["update_date"], y=trend_df["liquid_total"],
                mode="lines", name="Liquid",
                line=dict(color=COLORS["success"], width=2, dash="dot"),
            ))
            fig.add_trace(go.Scatter(
                x=trend_df["update_date"], y=trend_df["non_liquid_total"],
                mode="lines", name="Non-Liquid",
                line=dict(color=COLORS["warning"], width=2, dash="dot"),
            ))
            apply_chart_theme(fig, height=400,
                yaxis=dict(title="Amount (Rs.)", tickfont=dict(color=COLORS["text"])),
                xaxis=dict(title="", tickfont=dict(color=COLORS["text"])))
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("Not enough data yet for trend analysis. Update your portfolios to see trends.")

        # --- Monthly Summary + Category Distribution ---
        col_monthly, col_cat_trend = st.columns(2)

        with col_monthly:
            section_header("Monthly Net Worth", "&#x1f4c5;")
            if monthly:
                m_df = pd.DataFrame([dict(r) for r in monthly])
                m_df["month_label"] = pd.to_datetime(m_df["month"] + "-01").dt.strftime("%b %Y")
                m_df["prev_total"] = m_df["total"].shift(1)
                m_df["change"] = m_df["total"] - m_df["prev_total"]

                fig = go.Figure()
                fig.add_trace(go.Bar(
                    x=m_df["month_label"], y=m_df["total"],
                    marker_color=COLORS["accent"], marker_cornerradius=8,
                    text=[fmt_inr(v) for v in m_df["total"]],
                    textposition="outside",
                    textfont=dict(size=10, color=COLORS["text_secondary"]),
                    hovertemplate="<b>%{x}</b><br>Total: Rs. %{y:,.0f}<extra></extra>",
                ))
                apply_chart_theme(fig, height=360,
                    xaxis=dict(title="", tickfont=dict(color=COLORS["text"])),
                    yaxis=dict(title="Total (Rs.)", tickfont=dict(color=COLORS["text"])))
                st.plotly_chart(fig, use_container_width=True)

        with col_cat_trend:
            section_header("Category Distribution", "&#x2593;")
            cat_data = df.groupby("category")["balance"].sum().reset_index()
            cat_data = cat_data[cat_data["balance"] > 0].sort_values("balance", ascending=True)

            fig = px.bar(cat_data, x="balance", y="category", orientation="h",
                         color="category", color_discrete_map=bar_colors)
            fig.update_traces(
                texttemplate="%{x:,.0f}", textposition="outside",
                textfont=dict(size=10, color=COLORS["text_secondary"]),
                marker=dict(line=dict(width=0), cornerradius=6),
                hovertemplate="<b>%{y}</b><br>Rs. %{x:,.0f}<extra></extra>",
            )
            apply_chart_theme(fig, height=360, showlegend=False,
                xaxis=dict(title="", tickfont=dict(color=COLORS["text"])),
                yaxis=dict(title="", gridcolor="rgba(0,0,0,0)", linecolor="rgba(0,0,0,0)",
                           tickfont=dict(color=COLORS["text"])))
            st.plotly_chart(fig, use_container_width=True)

    # ============ TAB 3: DEEP DIVE ============
    with db_tab3:
        # --- Category Deep Dive selector ---
        section_header("Category Deep Dive", "&#x1f50D;")
        active_cats = [c for c, v in sorted(cat_totals.items(), key=lambda x: x[1], reverse=True) if v > 0]
        selected_cat = st.selectbox("Select a category to explore", active_cats, label_visibility="collapsed")

        if selected_cat:
            cat_sources = df[df["category"] == selected_cat].sort_values("balance", ascending=False)
            cat_total_val = cat_sources["balance"].sum()
            cat_count = len(cat_sources[cat_sources["balance"] > 0])
            cat_pct = (cat_total_val / total * 100) if total > 0 else 0
            cat_color = bar_colors.get(selected_cat, COLORS["primary"])

            c1, c2, c3 = st.columns(3)
            with c1:
                st.markdown(f"""<div class="dash-kpi" style="border-left:3px solid {cat_color};">
                    <div class="dash-kpi-label">Total Value</div>
                    <div class="dash-kpi-value">{fmt_inr(cat_total_val)}</div>
                    <div class="dash-kpi-sub">{fmt_inr_words(cat_total_val)}</div>
                </div>""", unsafe_allow_html=True)
            with c2:
                st.markdown(f"""<div class="dash-kpi" style="border-left:3px solid {cat_color};">
                    <div class="dash-kpi-label">Sources</div>
                    <div class="dash-kpi-value">{cat_count}</div>
                    <div class="dash-kpi-sub">active source{'s' if cat_count != 1 else ''}</div>
                </div>""", unsafe_allow_html=True)
            with c3:
                st.markdown(f"""<div class="dash-kpi" style="border-left:3px solid {cat_color};">
                    <div class="dash-kpi-label">Portfolio Share</div>
                    <div class="dash-kpi-value">{cat_pct:.1f}%</div>
                    <div class="dash-kpi-sub">of net worth</div>
                </div>""", unsafe_allow_html=True)

            # Source breakdown for this category
            if cat_count > 1:
                fig = px.pie(cat_sources[cat_sources["balance"] > 0],
                             values="balance", names="name", hole=0.5)
                fig.update_traces(
                    textinfo="percent+label",
                    textfont=dict(size=11, color=COLORS["text"]),
                    marker=dict(line=dict(color=COLORS["white"], width=2)),
                    hovertemplate="<b>%{label}</b><br>Rs. %{value:,.0f}<br>%{percent}<extra></extra>",
                )
                apply_chart_theme(fig, height=340, showlegend=False)
                st.plotly_chart(fig, use_container_width=True)

            # Detailed table
            detail_rows = ""
            for _, row in cat_sources.iterrows():
                if row["balance"] <= 0:
                    continue
                pct = (row["balance"] / cat_total_val * 100) if cat_total_val > 0 else 0
                badge_class = "badge-liquid" if row["liquidity"] == "Liquid" else "badge-nonliquid"
                detail_rows += f"""
                <tr>
                    <td><span style="font-weight:600;color:{COLORS['text']}">{row['name']}</span></td>
                    <td><span class="badge {badge_class}">{row['liquidity']}</span></td>
                    <td class="amount">{fmt_inr_full(row['balance'])}</td>
                    <td>
                        <div style="display:flex;align-items:center;gap:6px;">
                            <div style="flex:1;height:6px;background:{COLORS['surface2']};border-radius:3px;overflow:hidden;">
                                <div style="width:{pct}%;height:100%;background:{cat_color};border-radius:3px;"></div>
                            </div>
                            <span style="font-size:0.72rem;color:{COLORS['text_muted']};min-width:38px;text-align:right;">{pct:.1f}%</span>
                        </div>
                    </td>
                    <td style="color:{COLORS['text_muted']};font-size:0.8rem;">{row['last_update'] or '-'}</td>
                </tr>"""
            st.markdown(f"""
            <table class="styled-table">
                <thead><tr><th>Source</th><th>Type</th><th>Balance</th><th style="min-width:140px;">Share in {selected_cat}</th><th>Last Updated</th></tr></thead>
                <tbody>{detail_rows}</tbody>
            </table>
            """, unsafe_allow_html=True)

            # Navigate button
            target = _dash_nav_map.get(selected_cat)
            if target:
                if st.button(f"Go to {target} page", key="db_deep_nav", type="primary"):
                    st.session_state["nav_page"] = target
                    st.rerun()

        # --- Complete Portfolio Breakdown ---
        st.markdown("<div style='height:24px'></div>", unsafe_allow_html=True)
        section_header("Complete Portfolio Breakdown", "&#x1f4cb;")

        table_rows = ""
        for _, row in df.sort_values("balance", ascending=False).iterrows():
            if row["balance"] <= 0:
                continue
            badge_class = "badge-liquid" if row["liquidity"] == "Liquid" else "badge-nonliquid"
            pct = (row["balance"] / total * 100) if total > 0 else 0
            b_color = bar_colors.get(row["category"], COLORS["primary"])
            table_rows += f"""
            <tr>
                <td><span style="font-weight:600;color:{COLORS['text']}">{row['name']}</span></td>
                <td><span style="font-size:0.78rem;color:{COLORS['text_muted']}">{row['category']}</span></td>
                <td><span class="badge {badge_class}">{row['liquidity']}</span></td>
                <td class="amount">{fmt_inr_full(row['balance'])}</td>
                <td>
                    <div style="display:flex;align-items:center;gap:6px;">
                        <div style="flex:1;height:6px;background:{COLORS['surface2']};border-radius:3px;overflow:hidden;">
                            <div style="width:{pct}%;height:100%;background:{b_color};border-radius:3px;"></div>
                        </div>
                        <span style="font-size:0.72rem;color:{COLORS['text_muted']};min-width:38px;text-align:right;">{pct:.1f}%</span>
                    </div>
                </td>
                <td style="color:{COLORS['text_muted']};font-size:0.8rem;">{row['last_update'] or '-'}</td>
            </tr>"""

        st.markdown(f"""
        <table class="styled-table">
            <thead><tr><th>Source</th><th>Category</th><th>Type</th><th>Balance</th><th style="min-width:140px;">Share</th><th>Last Updated</th></tr></thead>
            <tbody>{table_rows}</tbody>
        </table>
        """, unsafe_allow_html=True)


# ===========================
# BANK UPDATE PAGE
# ===========================
elif page == "Bank Update":
    page_title("Bank Update", "Manage your savings accounts, fixed deposits & recurring deposits")

    bank_sources = [s for s in db.get_sources() if s["category"] in ("Bank Account", "Fixed Deposit/RD")]
    if not bank_sources:
        st.warning("No bank accounts found. Add bank sources from 'Manage Sources' first.")
        st.stop()

    # Gather all balances upfront
    bk_balances = {}
    for s in bank_sources:
        bk_balances[s["id"]] = db.get_latest_balance(s["id"])

    savings_sources = [s for s in bank_sources if s["category"] == "Bank Account"]
    fd_sources = [s for s in bank_sources if s["category"] == "Fixed Deposit/RD"]
    savings_total = sum(bk_balances[s["id"]] for s in savings_sources)
    fd_total = sum(bk_balances[s["id"]] for s in fd_sources)
    total_bank = savings_total + fd_total

    # Net worth context
    all_src_bk = db.get_sources()
    net_worth_bk = sum(db.get_latest_balance(s["id"]) for s in all_src_bk)
    bank_nw_pct = (total_bank / net_worth_bk * 100) if net_worth_bk > 0 else 0

    # Bank-specific styling
    bk_bank_icons = {"HDFC": "&#x1f3e6;", "ICICI": "&#x1f3e6;", "SBI": "&#x1f3e6;", "Kotak": "&#x1f3e6;",
                     "Axis": "&#x1f3e6;", "FD": "&#x1f512;", "RD": "&#x1f4c8;"}
    def _bank_meta(name, category):
        nl = name.lower()
        if category == "Fixed Deposit/RD":
            if "rd" in nl:
                return ("&#x1f4c8;", "#059669", "linear-gradient(135deg,#059669,#10B981)")
            return ("&#x1f512;", "#7C3AED", "linear-gradient(135deg,#6D28D9,#8B5CF6)")
        if "hdfc" in nl:
            return ("&#x1f3e6;", "#004B87", "linear-gradient(135deg,#004B87,#0066B8)")
        elif "icici" in nl:
            return ("&#x1f3e6;", "#F37021", "linear-gradient(135deg,#E65100,#F37021)")
        elif "kotak" in nl:
            return ("&#x1f3e6;", "#ED1C24", "linear-gradient(135deg,#C62828,#ED1C24)")
        elif "sbi" in nl:
            return ("&#x1f3e6;", "#1A237E", "linear-gradient(135deg,#1A237E,#3949AB)")
        elif "axis" in nl:
            return ("&#x1f3e6;", "#800020", "linear-gradient(135deg,#800020,#A0344F)")
        else:
            return ("&#x1f3e6;", "#2563EB", "linear-gradient(135deg,#1E40AF,#3B82F6)")

    # Hero banner
    st.markdown(
        f'<div style="background:linear-gradient(135deg,#0F172A 0%,#1E293B 40%,#1E3A5F 100%);'
        f'border-radius:18px;padding:28px 32px;margin-bottom:20px;position:relative;overflow:hidden">'
        f'<div style="position:absolute;top:-25px;right:-15px;font-size:7rem;opacity:0.05">&#x1f3e6;</div>'
        f'<div style="display:flex;align-items:center;flex-wrap:wrap;gap:28px">'
        f'<div style="flex:1;min-width:220px">'
        f'<div style="font-size:0.68rem;font-weight:600;text-transform:uppercase;letter-spacing:0.12em;'
        f'color:#94A3B8;margin-bottom:6px">Total Banking</div>'
        f'<div style="font-size:2.1rem;font-weight:900;color:#F8FAFC;letter-spacing:-0.02em">{fmt_inr_full(total_bank)}</div>'
        f'<div style="font-size:0.82rem;color:#CBD5E1;margin-top:4px">{fmt_inr_words(total_bank)}</div></div>'
        f'<div style="display:flex;gap:16px;flex-wrap:wrap">'
        f'<div style="text-align:center;background:rgba(255,255,255,0.07);border-radius:12px;padding:14px 20px">'
        f'<div style="font-size:1.5rem;font-weight:900;color:#60A5FA">{len(savings_sources)}</div>'
        f'<div style="font-size:0.62rem;color:#94A3B8;text-transform:uppercase;letter-spacing:0.5px">Savings</div></div>'
        f'<div style="text-align:center;background:rgba(255,255,255,0.07);border-radius:12px;padding:14px 20px">'
        f'<div style="font-size:1.5rem;font-weight:900;color:#A78BFA">{len(fd_sources)}</div>'
        f'<div style="font-size:0.62rem;color:#94A3B8;text-transform:uppercase;letter-spacing:0.5px">FD / RD</div></div>'
        f'<div style="text-align:center;background:rgba(255,255,255,0.07);border-radius:12px;padding:14px 20px">'
        f'<div style="font-size:1.5rem;font-weight:900;color:#F8FAFC">{bank_nw_pct:.1f}%</div>'
        f'<div style="font-size:0.62rem;color:#94A3B8;text-transform:uppercase;letter-spacing:0.5px">of Net Worth</div></div>'
        f'</div></div></div>',
        unsafe_allow_html=True)

    bk_tabs = st.tabs(["Overview", "Update Balance", "Bulk Update"])

    # ========== OVERVIEW TAB ==========
    with bk_tabs[0]:
        # Savings vs FD/RD split cards
        section_header("Savings vs Fixed Deposits", "&#x1f4ca;")
        sp_cols = st.columns(2)
        with sp_cols[0]:
            sav_pct = (savings_total / total_bank * 100) if total_bank > 0 else 0
            st.markdown(
                f'<div style="background:{COLORS["card"]};border:1px solid {COLORS["card_border"]};border-radius:14px;'
                f'padding:20px;box-shadow:{COLORS["card_shadow"]};border-top:4px solid #2563EB">'
                f'<div style="display:flex;align-items:center;gap:10px;margin-bottom:12px">'
                f'<div style="width:38px;height:38px;border-radius:10px;background:linear-gradient(135deg,#1E40AF,#3B82F6);'
                f'display:flex;align-items:center;justify-content:center">'
                f'<span style="font-size:1.1rem;filter:brightness(10)">&#x1f3e6;</span></div>'
                f'<div>'
                f'<div style="font-size:0.9rem;font-weight:700;color:{COLORS["text"]}">Savings Accounts</div>'
                f'<div style="font-size:0.68rem;color:{COLORS["text_muted"]}">{len(savings_sources)} account{"s" if len(savings_sources) != 1 else ""} &middot; Liquid</div>'
                f'</div></div>'
                f'<div style="font-size:1.5rem;font-weight:900;color:{COLORS["text"]};margin-bottom:8px">{fmt_inr_full(savings_total)}</div>'
                f'<div style="background:{COLORS["surface2"]};border-radius:4px;height:6px;overflow:hidden;margin-bottom:6px">'
                f'<div style="width:{sav_pct:.1f}%;height:100%;background:#2563EB;border-radius:4px"></div></div>'
                f'<div style="font-size:0.72rem;color:{COLORS["text_muted"]}">{sav_pct:.1f}% of banking total</div>'
                f'</div>',
                unsafe_allow_html=True)
        with sp_cols[1]:
            fd_pct = (fd_total / total_bank * 100) if total_bank > 0 else 0
            st.markdown(
                f'<div style="background:{COLORS["card"]};border:1px solid {COLORS["card_border"]};border-radius:14px;'
                f'padding:20px;box-shadow:{COLORS["card_shadow"]};border-top:4px solid #7C3AED">'
                f'<div style="display:flex;align-items:center;gap:10px;margin-bottom:12px">'
                f'<div style="width:38px;height:38px;border-radius:10px;background:linear-gradient(135deg,#6D28D9,#8B5CF6);'
                f'display:flex;align-items:center;justify-content:center">'
                f'<span style="font-size:1.1rem;filter:brightness(10)">&#x1f512;</span></div>'
                f'<div>'
                f'<div style="font-size:0.9rem;font-weight:700;color:{COLORS["text"]}">Fixed Deposits / RD</div>'
                f'<div style="font-size:0.68rem;color:{COLORS["text_muted"]}">{len(fd_sources)} deposit{"s" if len(fd_sources) != 1 else ""} &middot; Locked</div>'
                f'</div></div>'
                f'<div style="font-size:1.5rem;font-weight:900;color:{COLORS["text"]};margin-bottom:8px">{fmt_inr_full(fd_total)}</div>'
                f'<div style="background:{COLORS["surface2"]};border-radius:4px;height:6px;overflow:hidden;margin-bottom:6px">'
                f'<div style="width:{fd_pct:.1f}%;height:100%;background:#7C3AED;border-radius:4px"></div></div>'
                f'<div style="font-size:0.72rem;color:{COLORS["text_muted"]}">{fd_pct:.1f}% of banking total</div>'
                f'</div>',
                unsafe_allow_html=True)

        # Individual account cards grouped by type
        for group_label, group_sources, group_color, group_grad, group_ico in [
            ("Savings Accounts", savings_sources, "#2563EB", "linear-gradient(135deg,#1E40AF,#3B82F6)", "&#x1f3e6;"),
            ("Fixed Deposits / RD", fd_sources, "#7C3AED", "linear-gradient(135deg,#6D28D9,#8B5CF6)", "&#x1f512;"),
        ]:
            if not group_sources:
                continue
            group_total = sum(bk_balances[s["id"]] for s in group_sources)
            section_header(group_label, group_ico)
            for s in sorted(group_sources, key=lambda x: bk_balances[x["id"]], reverse=True):
                bal = bk_balances[s["id"]]
                b_ico, b_clr, b_grad = _bank_meta(s["name"], s["category"])
                pct_of_group = (bal / group_total * 100) if group_total > 0 else 0
                pct_of_total = (bal / total_bank * 100) if total_bank > 0 else 0
                # Last update info
                history = db.get_balance_history(s["id"])
                last_dt = history[0]["update_date"] if history else "N/A"
                prev_bal = history[1]["balance"] if len(history) > 1 else bal
                change = bal - prev_bal
                if change > 0:
                    chg_color = COLORS["success"]
                    chg_text = f"&#x25B2; +{fmt_inr(abs(change))}"
                elif change < 0:
                    chg_color = COLORS["danger"]
                    chg_text = f"&#x25BC; -{fmt_inr(abs(change))}"
                else:
                    chg_color = COLORS["text_muted"]
                    chg_text = "&#x25CF; No change"
                st.markdown(
                    f'<div style="background:{COLORS["card"]};border:1px solid {COLORS["card_border"]};'
                    f'border-radius:14px;padding:0;margin-bottom:8px;box-shadow:{COLORS["card_shadow"]};overflow:hidden">'
                    f'<div style="height:3px;background:{b_grad}"></div>'
                    f'<div style="padding:14px 20px;display:flex;align-items:center;gap:14px;flex-wrap:wrap">'
                    f'<div style="width:44px;height:44px;border-radius:12px;background:{b_grad};'
                    f'display:flex;align-items:center;justify-content:center;flex-shrink:0;'
                    f'box-shadow:0 3px 10px {b_clr}25">'
                    f'<span style="font-size:1.2rem;filter:brightness(10)">{b_ico}</span></div>'
                    f'<div style="flex:1;min-width:160px">'
                    f'<div style="font-size:0.95rem;font-weight:700;color:{COLORS["text"]}">{s["name"]}</div>'
                    f'<div style="font-size:0.72rem;color:{COLORS["text_muted"]};margin-top:2px">'
                    f'Updated: {last_dt}</div>'
                    f'<div style="display:flex;align-items:center;gap:8px;margin-top:5px">'
                    f'<div style="flex:1;max-width:140px;background:{COLORS["surface2"]};border-radius:3px;height:5px;overflow:hidden">'
                    f'<div style="width:{pct_of_group:.1f}%;height:100%;background:{b_clr};border-radius:3px"></div></div>'
                    f'<span style="font-size:0.62rem;color:{COLORS["text_muted"]}">{pct_of_group:.1f}%</span></div></div>'
                    f'<div style="text-align:right;min-width:140px">'
                    f'<div style="font-size:1.2rem;font-weight:800;color:{COLORS["text"]}">{fmt_inr_full(bal)}</div>'
                    f'<div style="font-size:0.72rem;color:{chg_color};font-weight:600;margin-top:3px">{chg_text}</div>'
                    f'<div style="font-size:0.62rem;color:{COLORS["text_muted"]};margin-top:2px">{pct_of_total:.1f}% of banking</div>'
                    f'</div></div></div>',
                    unsafe_allow_html=True)

        # Charts
        section_header("Visual Breakdown", "&#x1f4ca;")
        ch_cols = st.columns(2)
        with ch_cols[0]:
            # Savings vs FD donut
            if savings_total > 0 or fd_total > 0:
                fig_split = go.Figure(go.Pie(
                    labels=["Savings", "FD / RD"], values=[savings_total, fd_total],
                    hole=0.6, textinfo="label+percent", textposition="outside",
                    marker=dict(colors=["#2563EB", "#7C3AED"]),
                    pull=[0.03, 0.03],
                ))
                apply_chart_theme(fig_split, height=300, margin=dict(t=20, b=20, l=20, r=20))
                fig_split.update_layout(showlegend=False,
                    annotations=[dict(text=f"<b>{fmt_inr(total_bank)}</b>", x=0.5, y=0.5,
                                      font_size=14, font_color=COLORS["text"], showarrow=False)])
                st.plotly_chart(fig_split, use_container_width=True)
        with ch_cols[1]:
            # Bar chart of all accounts
            bk_sorted = sorted(bank_sources, key=lambda s: bk_balances[s["id"]], reverse=True)
            bk_names_chart = [s["name"] for s in bk_sorted]
            bk_vals_chart = [bk_balances[s["id"]] for s in bk_sorted]
            bk_colors_chart = [_bank_meta(s["name"], s["category"])[1] for s in bk_sorted]
            fig_bk_bar = go.Figure(go.Bar(
                x=bk_names_chart, y=bk_vals_chart,
                marker_color=bk_colors_chart, marker_cornerradius=8,
                text=[fmt_inr(v) for v in bk_vals_chart],
                textposition="outside", textfont=dict(size=10, color=COLORS["text"]),
            ))
            apply_chart_theme(fig_bk_bar, height=300, margin=dict(b=110))
            fig_bk_bar.update_layout(
                showlegend=False, xaxis_tickangle=-35,
                xaxis=dict(tickfont=dict(size=11, color=COLORS["text"])),
                yaxis=dict(title=dict(text="Rs.", font=dict(size=11, color=COLORS["text"])),
                           tickfont=dict(size=10, color=COLORS["text"])),
            )
            st.plotly_chart(fig_bk_bar, use_container_width=True)

        # Balance trend chart (last 10 updates per account)
        bk_trend_data = []
        for s in bank_sources:
            hist = db.get_balance_history(s["id"])
            for h in hist[:15]:
                bk_trend_data.append({"date": h["update_date"], "account": s["name"], "balance": h["balance"]})
        if bk_trend_data:
            section_header("Balance Trend", "&#x1f4c8;")
            bk_trend_df = pd.DataFrame(bk_trend_data)
            fig_bk_trend = px.line(bk_trend_df, x="date", y="balance", color="account",
                                    labels={"date": "Date", "balance": "Balance (Rs.)", "account": "Account"},
                                    color_discrete_sequence=CHART_COLORS)
            apply_chart_theme(fig_bk_trend, height=320)
            fig_bk_trend.update_layout(
                legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
                xaxis=dict(tickfont=dict(color=COLORS["text"])),
                yaxis=dict(tickfont=dict(color=COLORS["text"])),
            )
            st.plotly_chart(fig_bk_trend, use_container_width=True)

        # Insights
        sorted_bals = sorted(bk_balances.items(), key=lambda x: x[1], reverse=True)
        name_map = {s["id"]: s["name"] for s in bank_sources}
        largest_id, largest_val = sorted_bals[0]
        largest_name = name_map[largest_id]

        insights = []
        insights.append(f"Total banking: <strong>{fmt_inr_full(total_bank)}</strong> ({fmt_inr_words(total_bank)}) — <strong>{bank_nw_pct:.1f}%</strong> of net worth.")
        if savings_sources and fd_sources:
            insights.append(f"Savings: <strong>{fmt_inr_full(savings_total)}</strong> (liquid) &middot; FD/RD: <strong>{fmt_inr_full(fd_total)}</strong> (locked, earning interest).")
        if total_bank > 0:
            insights.append(f"Largest account: <strong>{largest_name}</strong> with {fmt_inr_full(largest_val)} ({largest_val / total_bank * 100:.1f}% of banking).")
        zero_accts = [name_map[sid] for sid, v in bk_balances.items() if v <= 0]
        if zero_accts:
            warn_c = COLORS["warning"]
            insights.append(f"<span style='color:{warn_c}'>{len(zero_accts)} account(s) at zero: {', '.join(zero_accts)}.</span>")
        if fd_total > 0 and total_bank > 0:
            fd_ratio = fd_total / total_bank * 100
            succ_c = COLORS["success"]
            if fd_ratio > 50:
                insights.append(f"<span style='color:{succ_c}'>Strong: {fd_ratio:.0f}% in FD/RDs — earning higher interest on majority of banking.</span>")
            elif fd_ratio < 20 and fd_sources:
                insights.append(f"Only {fd_ratio:.0f}% in FD/RDs. Consider parking idle savings in fixed deposits for better returns.")
        if savings_total > 100000:
            insights.append(f"Tip: Savings above Rs. 1L earn taxable interest. Consider sweeping excess into short-term FDs.")
        # Concentration check
        if total_bank > 0 and largest_val / total_bank > 0.6 and len(bank_sources) > 2:
            insights.append(f"&#x26a0;&#xfe0f; {largest_val / total_bank * 100:.0f}% concentrated in one account. Diversifying across banks reduces risk.")

        insight_box(insights, "Banking Insights & Recommendations")

    # ========== UPDATE BALANCE TAB ==========
    with bk_tabs[1]:
        bank_names = {s["name"]: s["id"] for s in bank_sources}
        uc1, uc2 = st.columns([3, 2])

        with uc1:
            st.markdown(
                f'<div style="background:{COLORS["card"]};border:1px solid {COLORS["card_border"]};border-radius:14px;'
                f'padding:20px 24px;box-shadow:{COLORS["card_shadow"]};margin-bottom:12px">'
                f'<div style="font-size:0.95rem;font-weight:700;color:{COLORS["text"]};margin-bottom:2px">&#x270f;&#xfe0f; Update Account Balance</div>'
                f'<div style="font-size:0.78rem;color:{COLORS["text_muted"]}">Select an account and enter the latest balance</div>'
                f'</div>',
                unsafe_allow_html=True)

            selected = st.selectbox("Select Account", list(bank_names.keys()), key="bk_sel")
            source_id = bank_names[selected]
            current = db.get_latest_balance(source_id)
            sel_src = next(s for s in bank_sources if s["name"] == selected)
            sel_ico, sel_clr, sel_grad = _bank_meta(selected, sel_src["category"])

            st.markdown(
                f'<div style="background:{sel_grad};border-radius:12px;padding:16px 20px;margin:10px 0">'
                f'<div style="display:flex;align-items:center;gap:10px">'
                f'<span style="font-size:1.3rem;filter:brightness(10)">{sel_ico}</span>'
                f'<div>'
                f'<div style="font-size:0.68rem;font-weight:600;text-transform:uppercase;letter-spacing:0.08em;'
                f'color:rgba(255,255,255,0.7)">Current Balance — {selected}</div>'
                f'<div style="font-size:1.4rem;font-weight:800;color:#FFFFFF;margin-top:2px">{fmt_inr_full(current)}</div>'
                f'</div></div></div>',
                unsafe_allow_html=True)

            new_balance = st.number_input("New Balance (Rs.)", value=current, step=100.0, format="%.2f", key="bk_new_bal")
            update_date = st.date_input("Date of update", value=date.today(), key="bk_update_date")
            note = st.text_input("Note (optional)", placeholder="e.g., Salary credited, EMI debited", key="bk_note")

            if st.button("Update Balance", type="primary", use_container_width=True, key="bk_update_btn"):
                db.update_balance(source_id, new_balance, note, update_date.isoformat())
                change = new_balance - current
                if change >= 0:
                    st.success(f"Updated {selected}! Change: +{fmt_inr_full(change)}")
                else:
                    st.warning(f"Updated {selected}! Change: {fmt_inr_full(change)}")
                st.rerun()

        with uc2:
            section_header("All Balances", "&#x1f4b0;")
            qv_total = 0
            quick_rows = ""
            for s in sorted(bank_sources, key=lambda x: bk_balances[x["id"]], reverse=True):
                bal = bk_balances[s["id"]]
                qv_total += bal
                b_ico, b_clr, _ = _bank_meta(s["name"], s["category"])
                cat_badge = "Savings" if s["category"] == "Bank Account" else "FD/RD"
                quick_rows += (
                    f'<tr>'
                    f'<td style="font-weight:600;color:{COLORS["text"]};font-size:0.85rem">'
                    f'<span style="color:{b_clr};margin-right:4px">{b_ico}</span> {s["name"]}'
                    f'<span style="margin-left:6px;font-size:0.6rem;color:{COLORS["text_muted"]}">{cat_badge}</span></td>'
                    f'<td class="amount" style="text-align:right">{fmt_inr_full(bal)}</td>'
                    f'</tr>'
                )
            quick_rows += (
                f'<tr style="border-top:2px solid {COLORS["card_border"]};font-weight:700">'
                f'<td style="color:{COLORS["primary"]};font-size:0.88rem">Total</td>'
                f'<td class="amount" style="text-align:right;color:{COLORS["primary"]};font-size:0.92rem">{fmt_inr_full(qv_total)}</td>'
                f'</tr>'
            )
            st.markdown(
                f'<table class="styled-table">'
                f'<thead><tr><th>Account</th><th style="text-align:right">Balance</th></tr></thead>'
                f'<tbody>{quick_rows}</tbody></table>',
                unsafe_allow_html=True)

    # ========== BULK UPDATE TAB ==========
    with bk_tabs[2]:
        st.markdown(
            f'<div style="background:{COLORS["card"]};border:1px solid {COLORS["card_border"]};border-radius:14px;'
            f'padding:20px 24px;box-shadow:{COLORS["card_shadow"]};margin-bottom:16px">'
            f'<div style="font-size:0.95rem;font-weight:700;color:{COLORS["text"]};margin-bottom:2px">&#x1f4cb; Bulk Update</div>'
            f'<div style="font-size:0.78rem;color:{COLORS["text_muted"]}">Update all accounts at once — only changed values get saved</div>'
            f'</div>',
            unsafe_allow_html=True)

        bcol1, bcol2 = st.columns(2)
        with bcol1:
            bulk_date = st.date_input("Date for bulk update", value=date.today(), key="bk_bulk_date")
        with bcol2:
            bulk_note = st.text_input("Note for all", placeholder="e.g., Monthly reconciliation", key="bk_bulk_note")

        # Group by type
        for grp_label, grp_srcs in [("Savings Accounts", savings_sources), ("Fixed Deposits / RD", fd_sources)]:
            if not grp_srcs:
                continue
            st.markdown(
                f'<div style="font-size:0.82rem;font-weight:700;color:{COLORS["text"]};margin:14px 0 6px 0;'
                f'padding-bottom:6px;border-bottom:1px solid {COLORS["card_border"]}">{grp_label}</div>',
                unsafe_allow_html=True)
            bulk_cols = st.columns(min(len(grp_srcs), 3))
            for i, s in enumerate(grp_srcs):
                with bulk_cols[i % len(bulk_cols)]:
                    current_bal = bk_balances[s["id"]]
                    st.number_input(
                        f"{s['name']} ({fmt_inr(current_bal)})",
                        value=current_bal, step=100.0, format="%.2f",
                        key=f"bk_bulk_{s['id']}"
                    )

        if st.button("Apply Bulk Update", type="primary", use_container_width=True, key="bk_bulk_btn"):
            count = 0
            for s in bank_sources:
                new_val = st.session_state.get(f"bk_bulk_{s['id']}", bk_balances[s["id"]])
                old_val = bk_balances[s["id"]]
                if abs(new_val - old_val) > 0.01:
                    db.update_balance(s["id"], new_val, bulk_note, bulk_date.isoformat())
                    count += 1
            if count:
                st.success(f"Updated {count} account(s).")
                st.rerun()
            else:
                st.info("No changes detected.")


# ===========================
# OTHER UPDATES PAGE
# ===========================
elif page == "Digital Wallet":
    page_title("Digital Wallet", "Manage your digital wallets, vouchers & prepaid balances")

    # Only Digital Wallet category sources (Amazon Pay, Airtel Bank, Neo Pay, etc.)
    dw_sources = [s for s in db.get_sources() if s["category"] == "Digital Wallet"]

    if not dw_sources:
        st.info("No digital wallet sources found. Add sources from 'Manage Sources' with category 'Digital Wallet'.")
        st.stop()

    # Gather balances
    dw_balances = {}
    dw_total = 0
    for s in dw_sources:
        bal = db.get_latest_balance(s["id"])
        dw_balances[s["id"]] = bal
        dw_total += bal

    # Wallet-specific icons based on name keywords
    def _wallet_icon(name):
        nl = name.lower()
        if "amazon" in nl:
            return ("&#x1f6d2;", "#FF9900", "linear-gradient(135deg,#FF9900,#FFB84D)")
        elif "airtel" in nl:
            return ("&#x1f4f1;", "#ED1C24", "linear-gradient(135deg,#ED1C24,#FF4D4D)")
        elif "neo" in nl:
            return ("&#x1f4b3;", "#6366F1", "linear-gradient(135deg,#4F46E5,#818CF8)")
        elif "paytm" in nl:
            return ("&#x1f4b2;", "#00BAF2", "linear-gradient(135deg,#00BAF2,#4DD0E1)")
        elif "phone" in nl or "phonepe" in nl:
            return ("&#x1f4de;", "#5F259F", "linear-gradient(135deg,#5F259F,#9C27B0)")
        elif "gpay" in nl or "google" in nl:
            return ("&#x1f310;", "#4285F4", "linear-gradient(135deg,#4285F4,#66A6FF)")
        else:
            return ("&#x1f4b3;", "#DB2777", "linear-gradient(135deg,#DB2777,#EC4899)")

    # Sort by balance
    dw_sorted = sorted(dw_sources, key=lambda s: dw_balances[s["id"]], reverse=True)

    # Hero banner — vibrant gradient
    all_src = db.get_sources()
    net_worth = sum(db.get_latest_balance(s["id"]) for s in all_src)
    dw_nw_pct = (dw_total / net_worth * 100) if net_worth > 0 else 0
    wallet_count = len(dw_sources)
    # Highest balance wallet
    top_wallet = dw_sorted[0] if dw_sorted else None
    top_ico = _wallet_icon(top_wallet["name"])[0] if top_wallet else "&#x1f4b3;"

    st.markdown(
        f'<div style="background:linear-gradient(135deg,#0F172A 0%,#1E1B4B 35%,#312E81 70%,#4338CA 100%);'
        f'border-radius:18px;padding:28px 32px;margin-bottom:20px;position:relative;overflow:hidden">'
        f'<div style="position:absolute;top:-30px;right:-10px;font-size:8rem;opacity:0.05">&#x1f4b3;</div>'
        f'<div style="display:flex;align-items:center;flex-wrap:wrap;gap:28px">'
        f'<div style="flex:1;min-width:220px">'
        f'<div style="font-size:0.68rem;font-weight:600;text-transform:uppercase;letter-spacing:0.12em;'
        f'color:#A5B4FC;margin-bottom:6px">Digital Wallet Balance</div>'
        f'<div style="font-size:2.1rem;font-weight:900;color:#F8FAFC;letter-spacing:-0.02em">{fmt_inr_full(dw_total)}</div>'
        f'<div style="font-size:0.82rem;color:#C7D2FE;margin-top:4px">{fmt_inr_words(dw_total)}</div></div>'
        f'<div style="display:flex;gap:16px;flex-wrap:wrap">'
        f'<div style="text-align:center;background:rgba(255,255,255,0.08);border-radius:12px;padding:14px 20px">'
        f'<div style="font-size:1.6rem;font-weight:900;color:#F8FAFC">{wallet_count}</div>'
        f'<div style="font-size:0.62rem;color:#A5B4FC;text-transform:uppercase;letter-spacing:0.5px">Wallets</div></div>'
        f'<div style="text-align:center;background:rgba(255,255,255,0.08);border-radius:12px;padding:14px 20px">'
        f'<div style="font-size:1.6rem;font-weight:900;color:#F8FAFC">{dw_nw_pct:.1f}%</div>'
        f'<div style="font-size:0.62rem;color:#A5B4FC;text-transform:uppercase;letter-spacing:0.5px">of Net Worth</div></div>'
        f'</div></div></div>',
        unsafe_allow_html=True)

    dw_tabs = st.tabs(["Overview", "Update Balance", "Bulk Update", "Sync Trackers"])

    # ---- Tab 1: Overview ----
    with dw_tabs[0]:
        # Individual wallet cards with brand-inspired styling
        section_header("Your Wallets", "&#x1f4b3;")
        for s in dw_sorted:
            bal = dw_balances[s["id"]]
            w_ico, w_clr, w_grad = _wallet_icon(s["name"])
            pct_of_total = (bal / dw_total * 100) if dw_total > 0 else 0
            # Get last update info
            history = db.get_balance_history(s["id"])
            last_dt = history[0]["update_date"] if history else "N/A"
            last_note = history[0]["note"] if history and history[0]["note"] else ""
            # Change from previous
            prev_bal = history[1]["balance"] if len(history) > 1 else bal
            change = bal - prev_bal
            change_pct = (change / prev_bal * 100) if prev_bal > 0 else 0
            if change > 0:
                chg_color = COLORS["success"]
                chg_arrow = "&#x25B2;"
                chg_sign = "+"
                chg_text = f"+{fmt_inr(abs(change))} ({change_pct:+.1f}%)"
            elif change < 0:
                chg_color = COLORS["danger"]
                chg_arrow = "&#x25BC;"
                chg_sign = ""
                chg_text = f"-{fmt_inr(abs(change))} ({change_pct:+.1f}%)"
            else:
                chg_color = COLORS["text_muted"]
                chg_arrow = "&#x25CF;"
                chg_sign = ""
                chg_text = "No change"
            note_html = f' &middot; <em>{last_note}</em>' if last_note else ""
            # Progress bar width
            bar_w = min(pct_of_total, 100)
            st.markdown(
                f'<div style="background:{COLORS["card"]};border:1px solid {COLORS["card_border"]};'
                f'border-radius:14px;padding:0;margin-bottom:10px;box-shadow:{COLORS["card_shadow"]};overflow:hidden">'
                # Top color accent bar
                f'<div style="height:4px;background:{w_grad}"></div>'
                f'<div style="padding:16px 20px;display:flex;align-items:center;gap:16px;flex-wrap:wrap">'
                # Icon
                f'<div style="width:48px;height:48px;border-radius:14px;background:{w_grad};'
                f'display:flex;align-items:center;justify-content:center;flex-shrink:0;'
                f'box-shadow:0 4px 12px {w_clr}30">'
                f'<span style="font-size:1.4rem;filter:brightness(10)">{w_ico}</span></div>'
                # Name & meta
                f'<div style="flex:1;min-width:180px">'
                f'<div style="font-size:1rem;font-weight:700;color:{COLORS["text"]}">{s["name"]}</div>'
                f'<div style="font-size:0.72rem;color:{COLORS["text_muted"]};margin-top:3px">'
                f'Last updated: {last_dt}{note_html}</div>'
                # Mini progress bar
                f'<div style="display:flex;align-items:center;gap:8px;margin-top:6px">'
                f'<div style="flex:1;max-width:160px;background:{COLORS["surface2"]};border-radius:3px;height:5px;overflow:hidden">'
                f'<div style="width:{bar_w:.1f}%;height:100%;background:{w_clr};border-radius:3px"></div></div>'
                f'<span style="font-size:0.65rem;color:{COLORS["text_muted"]}">{pct_of_total:.1f}%</span>'
                f'</div></div>'
                # Balance & change
                f'<div style="text-align:right;min-width:150px">'
                f'<div style="font-size:1.25rem;font-weight:800;color:{COLORS["text"]}">{fmt_inr_full(bal)}</div>'
                f'<div style="font-size:0.72rem;color:{chg_color};font-weight:600;margin-top:3px">'
                f'{chg_arrow} {chg_text}</div>'
                f'</div></div></div>',
                unsafe_allow_html=True)

        # Bar chart if multiple wallets
        if len(dw_sorted) > 1:
            section_header("Balance Comparison", "&#x1f4ca;")
            fig_dw_bar = go.Figure(go.Bar(
                x=[s["name"] for s in dw_sorted],
                y=[dw_balances[s["id"]] for s in dw_sorted],
                marker_color=[_wallet_icon(s["name"])[1] for s in dw_sorted],
                marker_cornerradius=8,
                text=[fmt_inr(dw_balances[s["id"]]) for s in dw_sorted],
                textposition="outside", textfont=dict(size=11, color=COLORS["text"]),
            ))
            apply_chart_theme(fig_dw_bar, height=320, margin=dict(b=100))
            fig_dw_bar.update_layout(
                showlegend=False, xaxis_tickangle=-30,
                xaxis=dict(tickfont=dict(size=12, color=COLORS["text"])),
                yaxis=dict(title=dict(text="Rs.", font=dict(size=11, color=COLORS["text"])),
                           tickfont=dict(size=10, color=COLORS["text"])),
            )
            st.plotly_chart(fig_dw_bar, use_container_width=True)

        # Insights
        insights = []
        insights.append(f"Total digital wallet balance: <strong>{fmt_inr_full(dw_total)}</strong> ({dw_nw_pct:.1f}% of net worth).")
        if top_wallet:
            insights.append(f"Highest balance: <strong>{top_wallet['name']}</strong> at {fmt_inr_full(dw_balances[top_wallet['id']])}.")
        zero_wallets = [s for s in dw_sources if dw_balances[s["id"]] == 0]
        if zero_wallets:
            names = ", ".join(s["name"] for s in zero_wallets[:3])
            insights.append(f"&#x26a0;&#xfe0f; {len(zero_wallets)} wallet(s) at zero balance: {names}.")
        if dw_total > 50000:
            insights.append("Consider moving excess wallet balance to a savings account or investment for better returns.")
        elif dw_total > 0:
            insights.append("Wallet balances are well-managed. Remember to check for expiring vouchers periodically.")
        insight_box(insights, "Wallet Insights")

    # ---- Tab 2: Update Balance ----
    with dw_tabs[1]:
        dw_names = {s["name"]: s["id"] for s in dw_sources}
        uc1, uc2 = st.columns([3, 2])

        with uc1:
            st.markdown(
                f'<div style="background:{COLORS["card"]};border:1px solid {COLORS["card_border"]};border-radius:14px;'
                f'padding:20px 24px;box-shadow:{COLORS["card_shadow"]};margin-bottom:12px">'
                f'<div style="font-size:0.95rem;font-weight:700;color:{COLORS["text"]};margin-bottom:2px">&#x270f;&#xfe0f; Update Wallet Balance</div>'
                f'<div style="font-size:0.78rem;color:{COLORS["text_muted"]}">Select a wallet and enter the latest balance</div>'
                f'</div>',
                unsafe_allow_html=True)

            selected = st.selectbox("Select Wallet", list(dw_names.keys()), key="dw_sel")
            source_id = dw_names[selected]
            current = db.get_latest_balance(source_id)
            sel_ico, sel_clr, sel_grad = _wallet_icon(selected)

            st.markdown(
                f'<div style="background:{sel_grad};border-radius:12px;padding:16px 20px;margin:10px 0">'
                f'<div style="display:flex;align-items:center;gap:10px">'
                f'<span style="font-size:1.3rem;filter:brightness(10)">{sel_ico}</span>'
                f'<div>'
                f'<div style="font-size:0.68rem;font-weight:600;text-transform:uppercase;letter-spacing:0.08em;'
                f'color:rgba(255,255,255,0.7)">Current Balance — {selected}</div>'
                f'<div style="font-size:1.4rem;font-weight:800;color:#FFFFFF;margin-top:2px">{fmt_inr_full(current)}</div>'
                f'</div></div></div>',
                unsafe_allow_html=True)

            new_balance = st.number_input("New Balance (Rs.)", value=current, step=100.0, format="%.2f", key="dw_new_bal")
            update_date = st.date_input("Date of update", value=date.today(), key="dw_update_date")
            note = st.text_input("Note (optional)", placeholder="e.g., Voucher redeemed, cashback credited", key="dw_note")

            if st.button("Update Balance", type="primary", use_container_width=True, key="dw_update_btn"):
                db.update_balance(source_id, new_balance, note, update_date.isoformat())
                change = new_balance - current
                if change >= 0:
                    st.success(f"Updated {selected}! Change: +{fmt_inr_full(change)}")
                else:
                    st.warning(f"Updated {selected}! Change: {fmt_inr_full(change)}")
                st.rerun()

        with uc2:
            section_header("All Wallet Balances", "&#x1f4b0;")
            qv_total = 0
            quick_rows = ""
            for s in dw_sorted:
                bal = dw_balances[s["id"]]
                qv_total += bal
                w_ico, w_clr, _ = _wallet_icon(s["name"])
                quick_rows += (
                    f'<tr>'
                    f'<td style="font-weight:600;color:{COLORS["text"]};font-size:0.85rem">'
                    f'<span style="color:{w_clr};margin-right:4px">{w_ico}</span> {s["name"]}</td>'
                    f'<td class="amount" style="text-align:right">{fmt_inr_full(bal)}</td>'
                    f'</tr>'
                )
            quick_rows += (
                f'<tr style="border-top:2px solid {COLORS["card_border"]};font-weight:700">'
                f'<td style="color:{COLORS["primary"]};font-size:0.88rem">Total</td>'
                f'<td class="amount" style="text-align:right;color:{COLORS["primary"]};font-size:0.92rem">{fmt_inr_full(qv_total)}</td>'
                f'</tr>'
            )
            st.markdown(
                f'<table class="styled-table">'
                f'<thead><tr><th>Wallet</th><th style="text-align:right">Balance</th></tr></thead>'
                f'<tbody>{quick_rows}</tbody></table>',
                unsafe_allow_html=True)

    # ---- Tab 3: Bulk Update ----
    with dw_tabs[2]:
        st.markdown(
            f'<div style="background:{COLORS["card"]};border:1px solid {COLORS["card_border"]};border-radius:14px;'
            f'padding:20px 24px;box-shadow:{COLORS["card_shadow"]};margin-bottom:16px">'
            f'<div style="font-size:0.95rem;font-weight:700;color:{COLORS["text"]};margin-bottom:2px">&#x1f4cb; Bulk Update</div>'
            f'<div style="font-size:0.78rem;color:{COLORS["text_muted"]}">Update all wallets at once — only changed values will be saved</div>'
            f'</div>',
            unsafe_allow_html=True)

        bcol1, bcol2 = st.columns(2)
        with bcol1:
            bulk_date = st.date_input("Date for bulk update", value=date.today(), key="dw_bulk_date")
        with bcol2:
            bulk_note = st.text_input("Note for all", placeholder="e.g., Monthly check", key="dw_bulk_note")

        bulk_data = {}
        cols = st.columns(min(len(dw_sources), 3))
        for i, s in enumerate(dw_sources):
            with cols[i % len(cols)]:
                current_bal = dw_balances[s["id"]]
                w_ico, _, _ = _wallet_icon(s["name"])
                val = st.number_input(
                    f"{s['name']} ({fmt_inr(current_bal)})",
                    value=current_bal, step=100.0, format="%.2f",
                    key=f"dw_bulk_{s['id']}"
                )
                bulk_data[s["id"]] = val

        if st.button("Apply Bulk Update", type="primary", use_container_width=True, key="dw_bulk_btn"):
            count = 0
            for sid, new_val in bulk_data.items():
                old_val = db.get_latest_balance(sid)
                if abs(new_val - old_val) > 0.01:
                    db.update_balance(sid, new_val, bulk_note, bulk_date.isoformat())
                    count += 1
            if count:
                st.success(f"Updated {count} wallet(s).")
                st.rerun()
            else:
                st.info("No changes detected.")

    # ---- Tab 4: Sync Trackers ----
    with dw_tabs[3]:
        st.markdown(
            f'<div style="background:{COLORS["card"]};border:1px solid {COLORS["card_border"]};border-radius:14px;'
            f'padding:20px 24px;box-shadow:{COLORS["card_shadow"]};margin-bottom:16px">'
            f'<div style="font-size:0.95rem;font-weight:700;color:{COLORS["text"]};margin-bottom:2px">&#x1f504; Sync from Tracker Pages</div>'
            f'<div style="font-size:0.78rem;color:{COLORS["text_muted"]}">Pull latest values from Policies, Lent Out, Shares, Gold Portfolio &amp; Gold Schemes into the main balance sheet</div>'
            f'</div>',
            unsafe_allow_html=True)

        tracker_sources = {
            "TATA AIA": ("Policies page — sum of current values", "&#x1f6e1;", "#0D9488"),
            "Lent Out": ("Lent Out page — outstanding amount", "&#x1f4b8;", "#EA580C"),
            "Shares & Stocks": ("Shares & Stock — Indian stocks buy price", "&#x1f4ca;", "#DC2626"),
            "US Stocks": ("Shares & Stock — US stocks (buy price x USD/INR)", "&#x1f30e;", "#2563EB"),
            "Gold Scheme": ("Gold Schemes — sum of deposits", "&#x1f947;", "#D97706"),
            "Gold - Physical": ("Gold Portfolio — physical purchases", "&#x1f4b0;", "#B45309"),
            "Gold - GPay": ("Gold Portfolio — GPay digital gold", "&#x1f4b3;", "#D97706"),
        }
        all_sources_sync = db.get_sources()
        sync_cards = ""
        for name, (desc, ico, clr) in tracker_sources.items():
            src = next((s for s in all_sources_sync if s["name"] == name), None)
            if src:
                bal = db.get_latest_balance(src["id"])
                sync_cards += (
                    f'<div style="display:flex;align-items:center;gap:14px;padding:14px 18px;margin-bottom:6px;'
                    f'background:{COLORS["card"]};border:1px solid {COLORS["card_border"]};border-left:4px solid {clr};'
                    f'border-radius:10px;box-shadow:{COLORS["card_shadow"]}">'
                    f'<div style="width:36px;height:36px;border-radius:10px;background:linear-gradient(135deg,{clr},{clr}CC);'
                    f'display:flex;align-items:center;justify-content:center">'
                    f'<span style="font-size:1rem;filter:brightness(10)">{ico}</span></div>'
                    f'<div style="flex:1">'
                    f'<div style="font-size:0.88rem;font-weight:700;color:{COLORS["text"]}">{name}</div>'
                    f'<div style="font-size:0.72rem;color:{COLORS["text_muted"]}">{desc}</div></div>'
                    f'<div style="font-size:1rem;font-weight:800;color:{COLORS["text"]}">{fmt_inr_full(bal)}</div>'
                    f'</div>'
                )
        if sync_cards:
            st.markdown(sync_cards, unsafe_allow_html=True)

        st.markdown("<div style='height:12px'></div>", unsafe_allow_html=True)
        if st.button("Sync All Balances", type="primary", use_container_width=True, key="dw_sync_btn"):
            usd_rate = None
            rate_row = db.get_latest_exchange_rate()
            if rate_row:
                usd_rate = rate_row["rate"]
            updated = db.sync_balances_from_trackers(usd_inr_rate=usd_rate)
            if updated:
                synced_list = ", ".join([f"{k}: {fmt_inr_full(v)}" for k, v in updated.items()])
                st.success(f"Synced {len(updated)} source(s): {synced_list}")
                st.rerun()
            else:
                st.info("All tracked sources are already up to date.")


# ===========================
# MANAGE SOURCES PAGE
# ===========================
elif page == "Manage Sources":
    page_title("Manage Sources", "Add, edit, or deactivate your financial sources")

    sources = db.get_sources(active_only=False)
    active_sources = [s for s in sources if s["is_active"]]
    inactive_sources = [s for s in sources if not s["is_active"]]

    # Category styling
    ms_cat_colors = {"Bank Account": "#2563EB", "Fixed Deposit/RD": "#059669", "Mutual Funds": "#7C3AED",
                     "Equity": "#DC2626", "Gold": "#D97706", "Insurance": "#0D9488",
                     "Digital Wallet": "#DB2777", "Receivables": "#EA580C", "Crypto": "#4F46E5",
                     "Real Estate": "#65A30D", "Other": "#64748B"}
    ms_cat_icons = {"Bank Account": "&#x1f3e6;", "Fixed Deposit/RD": "&#x1f512;", "Mutual Funds": "&#x1f4c8;",
                    "Equity": "&#x1f4ca;", "Gold": "&#x1f947;", "Insurance": "&#x1f6e1;",
                    "Digital Wallet": "&#x1f4b3;", "Receivables": "&#x1f4b8;", "Crypto": "&#x26d3;",
                    "Real Estate": "&#x1f3e0;", "Other": "&#x1f4c1;"}

    # Summary banner
    act_count = len(active_sources)
    inact_count = len(inactive_sources)
    cat_count = len(set(s["category"] for s in active_sources)) if active_sources else 0
    gold_count = len([s for s in active_sources if s["is_gold"]])
    st.markdown(
        f'<div style="background:linear-gradient(135deg,#1E293B 0%,#334155 50%,#475569 100%);'
        f'border-radius:16px;padding:24px 32px;margin-bottom:20px;display:flex;align-items:center;'
        f'flex-wrap:wrap;gap:32px">'
        f'<div style="flex:1;min-width:200px">'
        f'<div style="font-size:1.3rem;font-weight:800;color:#F8FAFC">Your Sources</div>'
        f'<div style="font-size:0.85rem;color:#94A3B8;margin-top:4px">Manage all accounts, investments &amp; assets</div></div>'
        f'<div style="display:flex;gap:24px;flex-wrap:wrap">'
        f'<div style="text-align:center"><div style="font-size:1.6rem;font-weight:900;color:#60A5FA">{act_count}</div>'
        f'<div style="font-size:0.7rem;color:#94A3B8;text-transform:uppercase;letter-spacing:0.5px">Active</div></div>'
        f'<div style="text-align:center"><div style="font-size:1.6rem;font-weight:900;color:#F59E0B">{cat_count}</div>'
        f'<div style="font-size:0.7rem;color:#94A3B8;text-transform:uppercase;letter-spacing:0.5px">Categories</div></div>'
        f'<div style="text-align:center"><div style="font-size:1.6rem;font-weight:900;color:#F87171">{inact_count}</div>'
        f'<div style="font-size:0.7rem;color:#94A3B8;text-transform:uppercase;letter-spacing:0.5px">Inactive</div></div>'
        + (f'<div style="text-align:center"><div style="font-size:1.6rem;font-weight:900;color:#FBBF24">{gold_count}</div>'
           f'<div style="font-size:0.7rem;color:#94A3B8;text-transform:uppercase;letter-spacing:0.5px">Gold Assets</div></div>'
           if gold_count > 0 else "")
        + f'</div></div>',
        unsafe_allow_html=True)

    ms_tabs = st.tabs(["Active Sources", "Add New Source", "Inactive Sources"])

    # ---- Tab 1: Active Sources ----
    with ms_tabs[0]:
        if not active_sources:
            st.info("No active sources. Add one from the 'Add New Source' tab.")
        else:
            # Group by category
            from collections import OrderedDict
            ms_grouped = OrderedDict()
            for s in active_sources:
                ms_grouped.setdefault(s["category"], []).append(s)

            for cat_name, cat_srcs in ms_grouped.items():
                cat_clr = ms_cat_colors.get(cat_name, "#64748B")
                cat_ico = ms_cat_icons.get(cat_name, "&#x1f4c1;")
                st.markdown(
                    f'<div style="display:flex;align-items:center;gap:8px;margin:20px 0 10px 0">'
                    f'<span style="font-size:1.1rem">{cat_ico}</span>'
                    f'<span style="font-size:0.95rem;font-weight:800;color:{COLORS["text"]}">{cat_name}</span>'
                    f'<span style="background:{cat_clr}18;color:{cat_clr};padding:2px 10px;border-radius:10px;'
                    f'font-size:0.72rem;font-weight:600">{len(cat_srcs)} source{"s" if len(cat_srcs) != 1 else ""}</span>'
                    f'<div style="flex:1;height:1px;background:{COLORS["card_border"]};margin-left:8px"></div>'
                    f'</div>',
                    unsafe_allow_html=True)

                for s in cat_srcs:
                    liq_clr = COLORS["success"] if s["liquidity"] == "Liquid" else "#94A3B8"
                    liq_label = s["liquidity"]
                    gold_badge = ""
                    if s["is_gold"]:
                        gw = s["gold_weight_grams"] or 0
                        gold_badge = (
                            f'<span style="background:#D9770615;color:#D97706;padding:2px 8px;border-radius:8px;'
                            f'font-size:0.68rem;font-weight:600">&#x1f947; {gw:.1f}g</span>'
                        )
                    st.markdown(
                        f'<div style="background:{COLORS["card"]};border:1px solid {COLORS["card_border"]};'
                        f'border-left:4px solid {cat_clr};border-radius:10px;padding:14px 18px;margin-bottom:6px;'
                        f'box-shadow:{COLORS["card_shadow"]};display:flex;align-items:center;gap:14px">'
                        f'<div style="flex:1">'
                        f'<div style="display:flex;align-items:center;gap:8px;flex-wrap:wrap">'
                        f'<span style="font-size:0.95rem;font-weight:700;color:{COLORS["text"]}">{s["name"]}</span>'
                        f'<span style="background:{liq_clr}15;color:{liq_clr};padding:2px 8px;border-radius:8px;'
                        f'font-size:0.68rem;font-weight:600">{liq_label}</span>'
                        f'{gold_badge}</div>'
                        f'<div style="font-size:0.75rem;color:{COLORS["text_muted"]};margin-top:3px">'
                        f'ID: {s["id"]} &middot; Added to portfolio</div>'
                        f'</div>'
                        f'<div style="font-size:0.72rem;color:{COLORS["text_muted"]};white-space:nowrap">'
                        f'&#x270f;&#xfe0f; Edit below</div>'
                        f'</div>',
                        unsafe_allow_html=True)

                    with st.expander(f"Edit {s['name']}", expanded=False):
                        ec1, ec2, ec3 = st.columns(3)
                        with ec1:
                            edit_name = st.text_input("Name", s["name"], key=f"en_{s['id']}")
                        with ec2:
                            cats = ["Bank Account", "Fixed Deposit/RD", "Mutual Funds", "Equity",
                                    "Gold", "Insurance", "Receivables", "Digital Wallet", "Crypto",
                                    "Real Estate", "Other"]
                            idx = cats.index(s["category"]) if s["category"] in cats else len(cats) - 1
                            edit_cat = st.selectbox("Category", cats, index=idx, key=f"ec_{s['id']}")
                        with ec3:
                            edit_liq = st.selectbox("Liquidity", ["Liquid", "Non-Liquid"],
                                                    index=0 if s["liquidity"] == "Liquid" else 1,
                                                    key=f"el_{s['id']}")
                        ec4, ec5 = st.columns(2)
                        with ec4:
                            edit_gold = st.checkbox("Gold asset", value=bool(s["is_gold"]), key=f"eg_{s['id']}")
                        with ec5:
                            edit_wt = st.number_input("Gold weight (g)", value=float(s["gold_weight_grams"] or 0),
                                                      step=1.0, key=f"ew_{s['id']}")
                        bc1, bc2, _ = st.columns([1, 1, 2])
                        with bc1:
                            if st.button("Save Changes", key=f"save_{s['id']}", type="primary", use_container_width=True):
                                db.update_source(s["id"], edit_name, edit_cat, edit_liq, edit_gold, edit_wt)
                                st.success("Updated!")
                                st.rerun()
                        with bc2:
                            if st.button("Deactivate", key=f"deact_{s['id']}", use_container_width=True):
                                db.deactivate_source(s["id"])
                                st.warning(f"Deactivated {s['name']}")
                                st.rerun()

    # ---- Tab 2: Add New Source ----
    with ms_tabs[1]:
        st.markdown(
            f'<div style="background:{COLORS["card"]};border:1px solid {COLORS["card_border"]};border-radius:14px;'
            f'padding:20px 24px;box-shadow:{COLORS["card_shadow"]};margin-bottom:16px">'
            f'<div style="font-size:1rem;font-weight:700;color:{COLORS["text"]};margin-bottom:4px">'
            f'&#x2795; Add a New Financial Source</div>'
            f'<div style="font-size:0.8rem;color:{COLORS["text_muted"]}">Track a new bank account, investment, or asset</div>'
            f'</div>',
            unsafe_allow_html=True)

        col1, col2, col3 = st.columns(3)
        with col1:
            new_name = st.text_input("Source Name", placeholder="e.g. HDFC Savings")
        with col2:
            new_cat = st.selectbox("Category", [
                "Bank Account", "Fixed Deposit/RD", "Mutual Funds",
                "Equity", "Gold", "Insurance", "Receivables",
                "Digital Wallet", "Crypto", "Real Estate", "Other"
            ])
        with col3:
            new_liq = st.selectbox("Liquidity", ["Liquid", "Non-Liquid"])

        col4, col5 = st.columns(2)
        with col4:
            new_is_gold = st.checkbox("This is a Gold asset")
        with col5:
            new_gold_wt = st.number_input("Gold weight (grams)", min_value=0.0, step=1.0, disabled=not new_is_gold)

        if st.button("Add Source", type="primary", use_container_width=False):
            if new_name.strip():
                try:
                    db.add_source(new_name.strip(), new_cat, new_liq, new_is_gold, new_gold_wt)
                    st.success(f"Added source: {new_name}")
                    st.rerun()
                except Exception as e:
                    st.error(f"Error: {e}")
            else:
                st.error("Name cannot be empty.")

    # ---- Tab 3: Inactive Sources ----
    with ms_tabs[2]:
        if not inactive_sources:
            st.info("No inactive sources. Deactivated sources will appear here.")
        else:
            for s in inactive_sources:
                cat_clr = ms_cat_colors.get(s["category"], "#64748B")
                st.markdown(
                    f'<div style="background:{COLORS["surface"]};border:1px solid {COLORS["card_border"]};'
                    f'border-left:4px solid #CBD5E1;border-radius:10px;padding:14px 18px;margin-bottom:6px;'
                    f'opacity:0.75;display:flex;align-items:center;gap:14px">'
                    f'<div style="flex:1">'
                    f'<div style="display:flex;align-items:center;gap:8px">'
                    f'<span style="font-size:0.95rem;font-weight:700;color:{COLORS["text_secondary"]};'
                    f'text-decoration:line-through">{s["name"]}</span>'
                    f'<span style="background:#CBD5E115;color:#94A3B8;padding:2px 8px;border-radius:8px;'
                    f'font-size:0.68rem;font-weight:600">Inactive</span></div>'
                    f'<div style="font-size:0.75rem;color:{COLORS["text_muted"]};margin-top:3px">'
                    f'{s["category"]} &middot; {s["liquidity"]}</div>'
                    f'</div></div>',
                    unsafe_allow_html=True)

    # --- Data Export Section ---
    st.markdown("---")
    st.markdown(
        '<div style="display:flex;align-items:center;gap:10px;margin-bottom:12px">'
        '<span style="font-size:1.1rem">&#x1f4e5;</span>'
        '<span style="font-size:1rem;font-weight:700;color:#0F172A">Data Export / Backup</span></div>',
        unsafe_allow_html=True)
    st.caption("Download a full backup of all your finance data as an Excel file with one sheet per table.")
    if st.button("Download Full Backup (.xlsx)", type="primary", key="export_btn"):
        import io
        all_data = db.export_all_data()
        buf = io.BytesIO()
        with pd.ExcelWriter(buf, engine="openpyxl") as writer:
            for table_name, rows in all_data.items():
                df = pd.DataFrame(rows) if rows else pd.DataFrame()
                df.to_excel(writer, sheet_name=table_name[:31], index=False)
        buf.seek(0)
        st.download_button(
            label="Click to Save",
            data=buf.getvalue(),
            file_name=f"finance_backup_{date.today().isoformat()}.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            key="download_xlsx",
        )


# ===========================
# HISTORY & ANALYTICS PAGE
# ===========================
elif page == "History & Analytics":
    page_title("History & Analytics", "See how your money has grown, moved, and where it's headed")

    sources = db.get_sources()
    source_map = {s["name"]: s["id"] for s in sources}
    monthly = db.get_monthly_summary()

    ha_tab_snapshot, ha_tab_trends, ha_tab_movements, ha_tab_compare = st.tabs(
        ["\u2001\U0001f4ca\u2002Snapshot", "\u2001\U0001f4c8\u2002Growth Trends",
         "\u2001\U0001f4b8\u2002Money Movements", "\u2001\u2696\ufe0f\u2002Compare"])

    # ========== SNAPSHOT TAB ==========
    with ha_tab_snapshot:
        # Current state hero
        snap_today = db.get_snapshot_on_date(date.today().isoformat())
        snap_df = pd.DataFrame([dict(r) for r in snap_today])

        if not snap_df.empty:
            total_now = snap_df["balance"].sum()
            liquid_now = snap_df[snap_df["liquidity"] == "Liquid"]["balance"].sum()
            nonliq_now = snap_df[snap_df["liquidity"] == "Non-Liquid"]["balance"].sum()
            liquid_pct = (liquid_now / total_now * 100) if total_now > 0 else 0

            # MoM change
            mom_change = 0
            mom_pct = 0
            if monthly and len(monthly) >= 2:
                prev_total = monthly[-2]["total"]
                mom_change = total_now - prev_total
                mom_pct = (mom_change / prev_total * 100) if prev_total > 0 else 0

            # 3-month & 6-month change
            chg_3m = 0
            chg_6m = 0
            if monthly and len(monthly) >= 4:
                chg_3m = total_now - monthly[-4]["total"]
            if monthly and len(monthly) >= 7:
                chg_6m = total_now - monthly[-7]["total"]

            # Hero banner
            mom_color = COLORS["success"] if mom_change >= 0 else COLORS["danger"]
            mom_sign = "+" if mom_change >= 0 else ""
            st.markdown(
                f'<div style="background:linear-gradient(135deg,#1E1B4B,#312E81,#3730A3);border-radius:20px;'
                f'padding:28px 32px;margin-bottom:20px;box-shadow:0 8px 32px rgba(30,27,75,0.25);position:relative;overflow:hidden">'
                f'<div style="position:absolute;top:-30px;right:-30px;width:160px;height:160px;border-radius:50%;'
                f'background:rgba(255,255,255,0.04)"></div>'
                f'<div style="font-size:0.72rem;font-weight:700;text-transform:uppercase;letter-spacing:0.12em;'
                f'color:rgba(199,210,254,0.8);margin-bottom:6px">Your Net Worth Today</div>'
                f'<div style="display:flex;align-items:baseline;gap:14px;flex-wrap:wrap">'
                f'<div style="font-size:2.2rem;font-weight:900;color:#E0E7FF;letter-spacing:-0.02em">{fmt_inr(total_now)}</div>'
                f'<div style="font-size:0.95rem;font-weight:600;color:{mom_color};background:rgba(255,255,255,0.1);'
                f'padding:4px 14px;border-radius:20px">{mom_sign}{fmt_inr(mom_change)} this month ({mom_pct:+.1f}%)</div>'
                f'</div>'
                f'<div style="display:flex;gap:32px;margin-top:18px;flex-wrap:wrap">'
                f'<div><div style="font-size:0.68rem;color:rgba(199,210,254,0.6);text-transform:uppercase;letter-spacing:0.08em">Liquid (Accessible)</div>'
                f'<div style="font-size:1.1rem;font-weight:700;color:#C7D2FE">{fmt_inr(liquid_now)} <span style="font-size:0.78rem;color:rgba(199,210,254,0.5)">({liquid_pct:.0f}%)</span></div></div>'
                f'<div><div style="font-size:0.68rem;color:rgba(199,210,254,0.6);text-transform:uppercase;letter-spacing:0.08em">Locked / Invested</div>'
                f'<div style="font-size:1.1rem;font-weight:700;color:#C7D2FE">{fmt_inr(nonliq_now)}</div></div>'
                + (f'<div><div style="font-size:0.68rem;color:rgba(199,210,254,0.6);text-transform:uppercase;letter-spacing:0.08em">Last 3 Months</div>'
                   f'<div style="font-size:1.1rem;font-weight:700;color:{"#86EFAC" if chg_3m>=0 else "#FCA5A5"}">{("+" if chg_3m>=0 else "")}{fmt_inr(chg_3m)}</div></div>' if chg_3m != 0 else '')
                + (f'<div><div style="font-size:0.68rem;color:rgba(199,210,254,0.6);text-transform:uppercase;letter-spacing:0.08em">Last 6 Months</div>'
                   f'<div style="font-size:1.1rem;font-weight:700;color:{"#86EFAC" if chg_6m>=0 else "#FCA5A5"}">{("+" if chg_6m>=0 else "")}{fmt_inr(chg_6m)}</div></div>' if chg_6m != 0 else '')
                + f'</div></div>',
                unsafe_allow_html=True,
            )

            # Category breakdown
            section_header("Where Your Money Sits", "&#x1f4b0;")
            cat_data = snap_df.groupby("category")["balance"].sum().sort_values(ascending=False)
            cat_colors_map = {"Bank Account": "#2563EB", "Fixed Deposit/RD": "#059669", "Mutual Funds": "#7C3AED",
                              "Equity": "#DC2626", "Gold": "#D97706", "Insurance": "#0D9488",
                              "Digital Wallet": "#DB2777", "Receivables": "#EA580C", "Other": "#64748B"}
            cat_icons = {"Bank Account": "&#x1f3e6;", "Fixed Deposit/RD": "&#x1f512;", "Mutual Funds": "&#x1f4c8;",
                         "Equity": "&#x1f4ca;", "Gold": "&#x1f4b0;", "Insurance": "&#x1f6e1;",
                         "Digital Wallet": "&#x1f4b3;", "Receivables": "&#x1f4b8;", "Other": "&#x1f4c1;"}

            active_cats = [(cat, bal) for cat, bal in cat_data.items() if bal > 0]
            if "ha_expanded_cat" not in st.session_state:
                st.session_state["ha_expanded_cat"] = None

            cat_cols = st.columns(min(len(active_cats), 4))
            for i, (cat, bal) in enumerate(active_cats):
                pct = (bal / total_now * 100) if total_now > 0 else 0
                cc = cat_colors_map.get(cat, COLORS["accent"])
                ico = cat_icons.get(cat, "&#x1f4c1;")
                is_expanded = st.session_state["ha_expanded_cat"] == cat
                src_count = len(snap_df[(snap_df["category"] == cat) & (snap_df["balance"] > 0)])
                border_style = f"border:2px solid {cc}" if is_expanded else f"border:1px solid {COLORS['card_border']}"
                with cat_cols[i % len(cat_cols)]:
                    st.markdown(
                        f'<div style="background:{COLORS["card"]};{border_style};border-radius:12px;'
                        f'padding:14px 16px;box-shadow:{COLORS["card_shadow"]};border-top:3px solid {cc};margin-bottom:4px">'
                        f'<div style="display:flex;align-items:center;gap:6px">'
                        f'<span style="font-size:1rem">{ico}</span>'
                        f'<span style="font-size:0.78rem;font-weight:700;color:{COLORS["text"]}">{cat}</span>'
                        f'<span style="margin-left:auto;font-size:0.65rem;color:{COLORS["text_muted"]}">{src_count} source{"s" if src_count!=1 else ""}</span></div>'
                        f'<div style="font-size:1.2rem;font-weight:900;color:{COLORS["text"]};margin:6px 0">{fmt_inr(bal)}</div>'
                        f'<div style="background:{COLORS["surface"]};border-radius:4px;height:6px;overflow:hidden">'
                        f'<div style="width:{pct:.1f}%;height:100%;background:{cc};border-radius:4px"></div></div>'
                        f'<div style="font-size:0.72rem;color:{COLORS["text_muted"]};margin-top:4px">{pct:.1f}% of portfolio</div>'
                        f'</div>',
                        unsafe_allow_html=True)
                    if st.button(f"{'Hide' if is_expanded else 'Details'}", key=f"ha_cat_{cat}",
                                 use_container_width=True):
                        st.session_state["ha_expanded_cat"] = None if is_expanded else cat
                        st.rerun()

            # Expanded category detail
            expanded_cat = st.session_state.get("ha_expanded_cat")
            if expanded_cat:
                ecc = cat_colors_map.get(expanded_cat, COLORS["accent"])
                cat_sources = snap_df[(snap_df["category"] == expanded_cat) & (snap_df["balance"] > 0)].sort_values("balance", ascending=False)
                cat_total = cat_sources["balance"].sum()
                cat_liquid = cat_sources[cat_sources["liquidity"] == "Liquid"]["balance"].sum()
                cat_nonliq = cat_sources[cat_sources["liquidity"] == "Non-Liquid"]["balance"].sum()
                eco = cat_icons.get(expanded_cat, "&#x1f4c1;")

                st.markdown(
                    f'<div style="background:linear-gradient(135deg,{COLORS["card"]},{ecc}08);'
                    f'border:2px solid {ecc}30;border-radius:16px;padding:20px 24px;margin:8px 0 16px 0;'
                    f'box-shadow:0 4px 16px {ecc}10">'
                    f'<div style="display:flex;align-items:center;gap:10px;margin-bottom:14px">'
                    f'<span style="font-size:1.4rem">{eco}</span>'
                    f'<div>'
                    f'<div style="font-size:1.05rem;font-weight:800;color:{COLORS["text"]}">{expanded_cat}</div>'
                    f'<div style="font-size:0.78rem;color:{COLORS["text_muted"]}">'
                    f'{len(cat_sources)} source{"s" if len(cat_sources)!=1 else ""} &middot; '
                    f'{fmt_inr(cat_total)} total</div></div>'
                    f'<div style="margin-left:auto;display:flex;gap:16px">'
                    f'<div style="text-align:center"><div style="font-size:0.62rem;color:{COLORS["text_muted"]};text-transform:uppercase">Liquid</div>'
                    f'<div style="font-size:0.88rem;font-weight:700;color:{COLORS["success"]}">{fmt_inr(cat_liquid)}</div></div>'
                    f'<div style="text-align:center"><div style="font-size:0.62rem;color:{COLORS["text_muted"]};text-transform:uppercase">Locked</div>'
                    f'<div style="font-size:0.88rem;font-weight:700;color:#64748B">{fmt_inr(cat_nonliq)}</div></div>'
                    f'</div></div>',
                    unsafe_allow_html=True,
                )

                # Source list
                for _, src in cat_sources.iterrows():
                    src_pct = (src["balance"] / cat_total * 100) if cat_total > 0 else 0
                    liq_tag = "Liquid" if src["liquidity"] == "Liquid" else "Locked"
                    liq_color = COLORS["success"] if src["liquidity"] == "Liquid" else "#94A3B8"
                    gold_info = ""
                    if src.get("is_gold") and src.get("gold_weight_grams") and src["gold_weight_grams"] > 0:
                        gold_info = f' &middot; {src["gold_weight_grams"]:.1f}g gold'
                    st.markdown(
                        f'<div style="display:flex;align-items:center;gap:12px;padding:10px 16px;margin-bottom:3px;'
                        f'background:{COLORS["white"]};border:1px solid {COLORS["card_border"]};border-radius:10px;'
                        f'border-left:3px solid {ecc}">'
                        f'<div style="flex:1">'
                        f'<div style="display:flex;align-items:center;gap:6px">'
                        f'<span style="font-size:0.85rem;font-weight:700;color:{COLORS["text"]}">{src["name"]}</span>'
                        f'<span style="background:{liq_color}15;color:{liq_color};padding:1px 7px;border-radius:6px;'
                        f'font-size:0.65rem;font-weight:600">{liq_tag}</span></div>'
                        f'<div style="font-size:0.72rem;color:{COLORS["text_muted"]}">Last updated: {src.get("last_update", "N/A")}{gold_info}</div>'
                        f'</div>'
                        f'<div style="text-align:right">'
                        f'<div style="font-size:1rem;font-weight:800;color:{COLORS["text"]}">{fmt_inr(src["balance"])}</div>'
                        f'<div style="font-size:0.72rem;color:{COLORS["text_muted"]}">{src_pct:.1f}% of {expanded_cat}</div>'
                        f'</div></div>',
                        unsafe_allow_html=True)

                # Mini bar chart for this category
                if len(cat_sources) > 1:
                    fig_cat_bar = go.Figure(go.Bar(
                        x=cat_sources["name"], y=cat_sources["balance"],
                        marker_color=ecc, marker_cornerradius=6,
                        text=[fmt_inr(v) for v in cat_sources["balance"]],
                        textposition="outside", textfont=dict(size=10),
                    ))
                    apply_chart_theme(fig_cat_bar, height=340, margin=dict(b=120))
                    fig_cat_bar.update_layout(
                        showlegend=False, xaxis_tickangle=-40,
                        xaxis=dict(tickfont=dict(size=12, color=COLORS["text"])),
                        yaxis=dict(title=dict(text="Rs.", font=dict(size=12, color=COLORS["text"])),
                                   tickfont=dict(size=11, color=COLORS["text"])),
                    )
                    st.plotly_chart(fig_cat_bar, use_container_width=True)

            # Allocation pie
            ch_cols = st.columns(2)
            with ch_cols[0]:
                section_header("Allocation Split", "&#x1f4ca;")
                fig_pie = go.Figure(go.Pie(
                    labels=list(cat_data.index), values=list(cat_data.values), hole=0.55,
                    textinfo="label+percent", textposition="outside",
                    marker=dict(colors=[cat_colors_map.get(c, "#6B7280") for c in cat_data.index]),
                    pull=[0.03] * len(cat_data),
                ))
                apply_chart_theme(fig_pie, height=320, margin=dict(t=10, b=10, l=10, r=10))
                fig_pie.update_layout(showlegend=False)
                fig_pie.update_traces(textfont_size=11)
                st.plotly_chart(fig_pie, use_container_width=True)

            with ch_cols[1]:
                section_header("Liquid vs Locked", "&#x1f512;")
                fig_liq = go.Figure(go.Pie(
                    labels=["Liquid (Accessible)", "Locked / Invested"],
                    values=[liquid_now, nonliq_now], hole=0.6,
                    textinfo="label+percent", textposition="outside",
                    marker=dict(colors=[COLORS["accent"], "#94A3B8"]),
                ))
                apply_chart_theme(fig_liq, height=320, margin=dict(t=10, b=10, l=10, r=10))
                fig_liq.update_layout(showlegend=False)
                fig_liq.update_traces(textfont_size=11)
                st.plotly_chart(fig_liq, use_container_width=True)

            # Top sources
            section_header("Your Top Sources", "&#x1f3c6;")
            top_sources = snap_df.nlargest(8, "balance")
            for _, row in top_sources.iterrows():
                if row["balance"] <= 0:
                    continue
                pct = (row["balance"] / total_now * 100) if total_now > 0 else 0
                cc = cat_colors_map.get(row["category"], COLORS["accent"])
                liq_badge = (f'<span style="background:{COLORS["success"]}15;color:{COLORS["success"]};padding:1px 8px;'
                             f'border-radius:8px;font-size:0.68rem;font-weight:600">Liquid</span>'
                             if row["liquidity"] == "Liquid" else
                             f'<span style="background:#94A3B815;color:#64748B;padding:1px 8px;'
                             f'border-radius:8px;font-size:0.68rem;font-weight:600">Locked</span>')
                st.markdown(
                    f'<div style="display:flex;align-items:center;gap:12px;padding:10px 16px;margin-bottom:4px;'
                    f'background:{COLORS["card"]};border:1px solid {COLORS["card_border"]};border-radius:10px;'
                    f'border-left:3px solid {cc}">'
                    f'<div style="flex:1">'
                    f'<div style="display:flex;align-items:center;gap:8px">'
                    f'<span style="font-size:0.88rem;font-weight:700;color:{COLORS["text"]}">{row["name"]}</span>'
                    f'<span style="font-size:0.72rem;color:{COLORS["text_muted"]}">{row["category"]}</span>'
                    f'{liq_badge}</div></div>'
                    f'<div style="text-align:right">'
                    f'<div style="font-size:1rem;font-weight:800;color:{COLORS["text"]}">{fmt_inr(row["balance"])}</div>'
                    f'<div style="font-size:0.72rem;color:{COLORS["text_muted"]}">{pct:.1f}%</div></div></div>',
                    unsafe_allow_html=True)

            # Insights
            insights = []
            insights.append(f"Your total net worth is <strong>{fmt_inr_full(total_now)}</strong> ({fmt_inr_words(total_now)}).")
            warn_c = COLORS["warning"]
            if liquid_pct < 20:
                insights.append(f"<span style='color:{warn_c}'>Only {liquid_pct:.0f}% of your money is liquid.</span> Consider keeping at least 20% accessible for emergencies.")
            elif liquid_pct > 70:
                insights.append(f"<span style='color:{warn_c}'>{liquid_pct:.0f}% of your money is liquid.</span> You might want to invest more for better returns.")
            else:
                insights.append(f"Healthy liquidity: {liquid_pct:.0f}% accessible, {100-liquid_pct:.0f}% invested/locked.")
            if mom_change != 0:
                direction = "grew" if mom_change > 0 else "decreased"
                insights.append(f"This month your net worth {direction} by <strong>{fmt_inr_full(abs(mom_change))}</strong> ({mom_pct:+.1f}%).")
            if len(top_sources) > 0:
                top = top_sources.iloc[0]
                top_pct = (top["balance"] / total_now * 100) if total_now > 0 else 0
                insights.append(f"Largest holding: <strong>{top['name']}</strong> at {fmt_inr(top['balance'])} ({top_pct:.0f}% of portfolio).")
                if top_pct > 40:
                    insights.append(f"<span style='color:{warn_c}'>Concentration risk: {top_pct:.0f}% in a single source.</span> Consider diversifying.")
            insight_box(insights, "Financial Health Check")
        else:
            st.info("No data available yet. Start by adding sources and updating balances.")

    # ========== GROWTH TRENDS TAB ==========
    with ha_tab_trends:
        if monthly and len(monthly) >= 1:
            # Monthly net worth trend
            section_header("How Your Money Has Grown", "&#x1f4c8;")
            m_df = pd.DataFrame([dict(m) for m in monthly])
            m_df["month_dt"] = pd.to_datetime(m_df["month"] + "-01")
            m_df["month_label"] = m_df["month_dt"].dt.strftime("%b '%y")

            fig_growth = go.Figure()
            fig_growth.add_trace(go.Scatter(
                x=m_df["month_dt"], y=m_df["total"],
                mode="lines+markers+text", name="Net Worth",
                line=dict(color=COLORS["accent"], width=3, shape="spline"),
                marker=dict(size=9, color=COLORS["accent"], line=dict(width=2, color=COLORS["white"])),
                fill="tozeroy", fillcolor="rgba(37,99,235,0.06)",
                text=[fmt_inr(v) for v in m_df["total"]],
                textposition="top center", textfont=dict(size=10, color=COLORS["text_muted"]),
            ))
            apply_chart_theme(fig_growth, height=400, yaxis=dict(title="Net Worth (Rs.)"))
            st.plotly_chart(fig_growth, use_container_width=True)

            # Monthly change bars
            if len(m_df) >= 2:
                section_header("Monthly Change (How Much You Added)", "&#x1f4ca;")
                m_df["change"] = m_df["total"].diff()
                m_df_chg = m_df.dropna(subset=["change"])
                if not m_df_chg.empty:
                    bar_colors = [COLORS["success"] if c >= 0 else COLORS["danger"] for c in m_df_chg["change"]]
                    fig_chg = go.Figure(go.Bar(
                        x=m_df_chg["month_dt"], y=m_df_chg["change"],
                        marker_color=bar_colors, marker_cornerradius=6,
                        text=[f"{'+' if c>=0 else ''}{fmt_inr(c)}" for c in m_df_chg["change"]],
                        textposition="outside", textfont=dict(size=10),
                    ))
                    apply_chart_theme(fig_chg, height=350, yaxis=dict(title="Change (Rs.)"))
                    fig_chg.update_layout(showlegend=False)
                    st.plotly_chart(fig_chg, use_container_width=True)

            # Liquid vs non-liquid trend
            daily_totals = db.get_daily_totals()
            if daily_totals and len(daily_totals) >= 2:
                section_header("Liquid vs Locked Over Time", "&#x1f4ca;")
                dt_df = pd.DataFrame([dict(d) for d in daily_totals])
                dt_df["update_date"] = pd.to_datetime(dt_df["update_date"])
                fig_lnl = go.Figure()
                fig_lnl.add_trace(go.Scatter(
                    x=dt_df["update_date"], y=dt_df["liquid_total"],
                    mode="lines", name="Liquid", stackgroup="one",
                    line=dict(color=COLORS["accent"], width=0),
                    fillcolor="rgba(37,99,235,0.3)",
                ))
                fig_lnl.add_trace(go.Scatter(
                    x=dt_df["update_date"], y=dt_df["non_liquid_total"],
                    mode="lines", name="Locked/Invested", stackgroup="one",
                    line=dict(color="#94A3B8", width=0),
                    fillcolor="rgba(148,163,184,0.3)",
                ))
                apply_chart_theme(fig_lnl, height=350, yaxis=dict(title="Rs."))
                st.plotly_chart(fig_lnl, use_container_width=True)

            # Trend insights
            if len(m_df) >= 3:
                m_df_valid = m_df.dropna(subset=["change"])
                avg_monthly = m_df_valid["change"].mean() if not m_df_valid.empty else 0
                best_month = m_df_valid.loc[m_df_valid["change"].idxmax()] if not m_df_valid.empty else None
                worst_month = m_df_valid.loc[m_df_valid["change"].idxmin()] if not m_df_valid.empty else None
                positive_months = (m_df_valid["change"] > 0).sum()
                total_months_count = len(m_df_valid)
                first_total = m_df.iloc[0]["total"]
                last_total = m_df.iloc[-1]["total"]
                abs_growth = last_total - first_total
                pct_growth = (abs_growth / first_total * 100) if first_total > 0 else 0

                t_insights = []
                t_insights.append(f"Over {len(m_df)} months tracked, your wealth grew by <strong>{fmt_inr_full(abs_growth)}</strong> ({pct_growth:+.1f}%).")
                gc = COLORS["success"] if avg_monthly >= 0 else COLORS["danger"]
                t_insights.append(f"Average monthly change: <strong style='color:{gc}'>{'+' if avg_monthly>=0 else ''}{fmt_inr_full(avg_monthly)}</strong>.")
                t_insights.append(f"You had <strong>{positive_months} growth months</strong> out of {total_months_count} ({positive_months/total_months_count*100:.0f}% hit rate).")
                if best_month is not None:
                    t_insights.append(f"Best month: <strong>{best_month['month_dt'].strftime('%b %Y')}</strong> (+{fmt_inr(best_month['change'])})."
                                      f" Worst: <strong>{worst_month['month_dt'].strftime('%b %Y')}</strong> ({fmt_inr(worst_month['change'])}).")
                if avg_monthly > 0:
                    months_to_next_lakh = ((100000 - (last_total % 100000)) / avg_monthly) if avg_monthly > 0 else 0
                    next_target = ((last_total // 100000) + 1) * 100000
                    if months_to_next_lakh > 0 and months_to_next_lakh < 120:
                        t_insights.append(f"At this pace, you'll cross <strong>{fmt_inr(next_target)}</strong> in ~{months_to_next_lakh:.0f} months.")
                insight_box(t_insights, "Growth Insights")
        else:
            st.info("Not enough monthly data yet. Keep updating your balances to see growth trends.")

    # ========== MONEY MOVEMENTS TAB ==========
    with ha_tab_movements:
        section_header("Recent Activity", "&#x1f4b8;")

        mv_cols = st.columns([2, 1, 1])
        with mv_cols[0]:
            mv_source = st.selectbox("Source", ["All Sources"] + list(source_map.keys()), key="mv_src")
        with mv_cols[1]:
            mv_start = st.date_input("From", value=date.today() - timedelta(days=90), key="mv_from")
        with mv_cols[2]:
            mv_end = st.date_input("To", value=date.today(), key="mv_to")

        mv_source_id = source_map.get(mv_source) if mv_source != "All Sources" else None
        history = db.get_balance_history(mv_source_id, mv_start.isoformat(), mv_end.isoformat())

        if history:
            log_df = pd.DataFrame([dict(r) for r in history])
            positive = log_df[log_df["change_amount"] > 0]["change_amount"].sum()
            negative = log_df[log_df["change_amount"] < 0]["change_amount"].sum()
            net = positive + negative

            # Summary cards
            metric_row(
                ("Updates", str(len(log_df)), f"{mv_start.strftime('%d %b')} - {mv_end.strftime('%d %b')}", "blue", "&#x1f4dd;"),
                ("Money In", fmt_inr_full(positive), "Credits & growth", "green", "&#x2B06;&#xFE0F;"),
                ("Money Out", fmt_inr_full(abs(negative)), "Debits & withdrawals", "amber", "&#x2B07;&#xFE0F;"),
                ("Net Flow", f"{'+' if net >= 0 else ''}{fmt_inr_full(net)}", "In minus Out", "green" if net >= 0 else "amber", "&#x1f4b0;"),
            )

            # Activity feed — card-based instead of table
            st.markdown("<div style='height:10px'></div>", unsafe_allow_html=True)
            section_header("Activity Feed", "&#x1f4dc;")

            for _, r in log_df.head(50).iterrows():
                change = r["change_amount"] or 0
                is_positive = change >= 0
                arrow = "&#x2B06;" if is_positive else "&#x2B07;"
                chg_color = COLORS["success"] if is_positive else COLORS["danger"]
                sign = "+" if is_positive else ""
                note_html = f' <span style="color:{COLORS["text_muted"]};font-style:italic">&middot; {r["note"]}</span>' if r["note"] else ""
                st.markdown(
                    f'<div style="display:flex;align-items:center;gap:12px;padding:10px 16px;margin-bottom:3px;'
                    f'background:{COLORS["card"]};border:1px solid {COLORS["card_border"]};border-radius:10px;'
                    f'border-left:3px solid {chg_color}">'
                    f'<div style="font-size:1.1rem;min-width:20px">{arrow}</div>'
                    f'<div style="flex:1">'
                    f'<div style="font-size:0.85rem;font-weight:600;color:{COLORS["text"]}">{r["source_name"]}'
                    f'<span style="font-size:0.72rem;color:{COLORS["text_muted"]};margin-left:6px">{r["category"]}</span>{note_html}</div>'
                    f'<div style="font-size:0.72rem;color:{COLORS["text_muted"]}">{r["update_date"]} &middot; '
                    f'{fmt_inr(r["previous_balance"] or 0)} &rarr; {fmt_inr(r["balance"])}</div></div>'
                    f'<div style="text-align:right">'
                    f'<div style="font-size:0.95rem;font-weight:800;color:{chg_color}">{sign}{fmt_inr(abs(change))}</div></div></div>',
                    unsafe_allow_html=True)

            if len(log_df) > 50:
                st.markdown(f'<div style="text-align:center;padding:8px;color:{COLORS["text_muted"]};font-size:0.82rem">'
                            f'Showing 50 of {len(log_df)} entries</div>', unsafe_allow_html=True)

            # Movement insights
            if len(log_df) >= 3:
                top_inflows = log_df[log_df["change_amount"] > 0].nlargest(3, "change_amount")
                top_outflows = log_df[log_df["change_amount"] < 0].nsmallest(3, "change_amount")
                by_source = log_df.groupby("source_name")["change_amount"].sum().sort_values()

                mv_insights = []
                mv_insights.append(f"In the selected period: <strong>{fmt_inr_full(positive)}</strong> came in, <strong>{fmt_inr_full(abs(negative))}</strong> went out. Net: <strong>{'+' if net>=0 else ''}{fmt_inr_full(net)}</strong>.")
                if not top_inflows.empty:
                    top_in = top_inflows.iloc[0]
                    mv_insights.append(f"Biggest credit: <strong>{top_in['source_name']}</strong> on {top_in['update_date']} (+{fmt_inr(top_in['change_amount'])}).")
                if not top_outflows.empty:
                    top_out = top_outflows.iloc[0]
                    mv_insights.append(f"Biggest debit: <strong>{top_out['source_name']}</strong> on {top_out['update_date']} ({fmt_inr(top_out['change_amount'])}).")
                most_active = log_df["source_name"].value_counts().head(1)
                if not most_active.empty:
                    mv_insights.append(f"Most active: <strong>{most_active.index[0]}</strong> with {most_active.values[0]} updates.")
                if not by_source.empty:
                    growers = by_source[by_source > 0]
                    shrinkers = by_source[by_source < 0]
                    if not growers.empty:
                        mv_insights.append(f"Sources that grew: {', '.join(f'<strong>{n}</strong> (+{fmt_inr(v)})' for n, v in growers.items())}.")
                insight_box(mv_insights, "Movement Insights")
        else:
            st.info("No activity in selected period. Try a wider date range.")

    # ========== COMPARE TAB ==========
    with ha_tab_compare:
        st.markdown(
            f'<div style="background:linear-gradient(135deg,{COLORS["surface"]},#EEF2FF);border:1px solid {COLORS["card_border"]};'
            f'border-radius:14px;padding:18px 22px;margin-bottom:16px">'
            f'<div style="font-size:1rem;font-weight:800;color:{COLORS["text"]};margin-bottom:4px">Compare Your Finances Across Dates</div>'
            f'<div style="font-size:0.82rem;color:{COLORS["text_secondary"]}">Pick two dates and see exactly what changed — which accounts grew, which shrank, and by how much.</div>'
            f'</div>',
            unsafe_allow_html=True,
        )

        cmp_cols = st.columns([1, 1, 1])
        with cmp_cols[0]:
            date_a = st.date_input("Earlier Date", value=date.today() - timedelta(days=30), key="cmp_a")
        with cmp_cols[1]:
            date_b = st.date_input("Later Date", value=date.today(), key="cmp_b")
        with cmp_cols[2]:
            st.markdown("<div style='height:28px'></div>", unsafe_allow_html=True)
            do_compare = st.button("Compare Now", type="primary", use_container_width=True)

        if do_compare:
            snap_a = db.get_snapshot_on_date(date_a.isoformat())
            snap_b = db.get_snapshot_on_date(date_b.isoformat())
            df_a = pd.DataFrame([dict(r) for r in snap_a])[["name", "category", "balance"]].rename(columns={"balance": "bal_a"})
            df_b = pd.DataFrame([dict(r) for r in snap_b])[["name", "balance"]].rename(columns={"balance": "bal_b"})
            merged = df_a.merge(df_b, on="name", how="outer").fillna(0)
            merged["change"] = merged["bal_b"] - merged["bal_a"]
            merged["pct"] = merged.apply(lambda r: (r["change"] / r["bal_a"] * 100) if r["bal_a"] > 0 else 0, axis=1)

            total_a = merged["bal_a"].sum()
            total_b = merged["bal_b"].sum()
            total_chg = total_b - total_a
            total_pct = (total_chg / total_a * 100) if total_a > 0 else 0
            days_diff = (date_b - date_a).days

            # Summary hero
            chg_color = COLORS["success"] if total_chg >= 0 else COLORS["danger"]
            chg_sign = "+" if total_chg >= 0 else ""
            st.markdown(
                f'<div style="background:{COLORS["card"]};border:2px solid {chg_color}30;border-radius:16px;'
                f'padding:20px 24px;margin:16px 0;text-align:center">'
                f'<div style="font-size:0.72rem;color:{COLORS["text_muted"]};text-transform:uppercase;letter-spacing:0.08em">'
                f'In {days_diff} days ({date_a.strftime("%d %b")} to {date_b.strftime("%d %b")})</div>'
                f'<div style="font-size:2rem;font-weight:900;color:{chg_color};margin:6px 0">{chg_sign}{fmt_inr(total_chg)}</div>'
                f'<div style="font-size:0.88rem;color:{COLORS["text_muted"]}">{fmt_inr(total_a)} &rarr; {fmt_inr(total_b)} ({total_pct:+.1f}%)</div>'
                f'</div>',
                unsafe_allow_html=True)

            # Per-source comparison
            winners = merged[merged["change"] > 0].sort_values("change", ascending=False)
            losers = merged[merged["change"] < 0].sort_values("change")
            unchanged = merged[merged["change"] == 0]

            if not winners.empty:
                section_header(f"Grew ({len(winners)} sources)", "&#x1f4c8;")
                for _, r in winners.iterrows():
                    pct_str = f" ({r['pct']:+.1f}%)" if r["bal_a"] > 0 else ""
                    st.markdown(
                        f'<div style="display:flex;align-items:center;gap:12px;padding:10px 16px;margin-bottom:3px;'
                        f'background:{COLORS["card"]};border:1px solid {COLORS["card_border"]};border-radius:10px;'
                        f'border-left:3px solid {COLORS["success"]}">'
                        f'<div style="flex:1">'
                        f'<div style="font-size:0.88rem;font-weight:700;color:{COLORS["text"]}">{r["name"]}'
                        f'<span style="font-size:0.72rem;color:{COLORS["text_muted"]};margin-left:6px">{r.get("category", "")}</span></div>'
                        f'<div style="font-size:0.72rem;color:{COLORS["text_muted"]}">{fmt_inr(r["bal_a"])} &rarr; {fmt_inr(r["bal_b"])}</div></div>'
                        f'<div style="font-size:1rem;font-weight:800;color:{COLORS["success"]}">+{fmt_inr(r["change"])}{pct_str}</div></div>',
                        unsafe_allow_html=True)

            if not losers.empty:
                section_header(f"Decreased ({len(losers)} sources)", "&#x1f4c9;")
                for _, r in losers.iterrows():
                    pct_str = f" ({r['pct']:+.1f}%)" if r["bal_a"] > 0 else ""
                    st.markdown(
                        f'<div style="display:flex;align-items:center;gap:12px;padding:10px 16px;margin-bottom:3px;'
                        f'background:{COLORS["card"]};border:1px solid {COLORS["card_border"]};border-radius:10px;'
                        f'border-left:3px solid {COLORS["danger"]}">'
                        f'<div style="flex:1">'
                        f'<div style="font-size:0.88rem;font-weight:700;color:{COLORS["text"]}">{r["name"]}'
                        f'<span style="font-size:0.72rem;color:{COLORS["text_muted"]};margin-left:6px">{r.get("category", "")}</span></div>'
                        f'<div style="font-size:0.72rem;color:{COLORS["text_muted"]}">{fmt_inr(r["bal_a"])} &rarr; {fmt_inr(r["bal_b"])}</div></div>'
                        f'<div style="font-size:1rem;font-weight:800;color:{COLORS["danger"]}">{fmt_inr(r["change"])}{pct_str}</div></div>',
                        unsafe_allow_html=True)

            if not unchanged.empty:
                st.markdown(
                    f'<div style="margin-top:10px;padding:10px 16px;background:{COLORS["surface"]};border-radius:10px;'
                    f'font-size:0.82rem;color:{COLORS["text_muted"]}">'
                    f'No change: {", ".join(unchanged["name"].tolist())}</div>',
                    unsafe_allow_html=True)

            # Comparison insights
            c_insights = []
            c_insights.append(f"In <strong>{days_diff} days</strong>, your net worth {'grew' if total_chg>=0 else 'decreased'} by <strong>{chg_sign}{fmt_inr_full(total_chg)}</strong> ({total_pct:+.1f}%).")
            if not winners.empty:
                top_winner = winners.iloc[0]
                c_insights.append(f"Biggest gainer: <strong>{top_winner['name']}</strong> (+{fmt_inr(top_winner['change'])}).")
            if not losers.empty:
                top_loser = losers.iloc[0]
                c_insights.append(f"Biggest drop: <strong>{top_loser['name']}</strong> ({fmt_inr(top_loser['change'])}).")
            if days_diff > 0 and total_chg != 0:
                daily_rate = total_chg / days_diff
                c_insights.append(f"That's roughly <strong>{'+' if daily_rate>=0 else ''}{fmt_inr_full(daily_rate)}/day</strong> or <strong>{'+' if daily_rate>=0 else ''}{fmt_inr_full(daily_rate*30)}/month</strong>.")
            insight_box(c_insights, "Comparison Insights")


# ======================== GOLD PORTFOLIO (Unified) ========================
elif page == "Gold Portfolio":
    page_title("Gold Portfolio", "Physical gold, digital gold & scheme investments — all in one place")

    latest_rate = db.get_latest_gold_rate()
    purchases = db.get_gold_purchases()
    schemes = db.get_gold_schemes()

    # Rate setup
    r22 = latest_rate["rate_per_gram_22k"] or 0 if latest_rate else 0
    r24 = latest_rate["rate_per_gram_24k"] or 0 if latest_rate else 0
    rate_18k = r22 * 18 / 22 if r22 else 0
    rate_map = {"22K": r22, "24K": r24, "18K": rate_18k}
    rate_date_str = latest_rate["rate_date"] if latest_rate else "N/A"

    # Compute totals
    phys_purchases = [p for p in purchases if p["source_type"] == "Physical"]
    digi_purchases = [p for p in purchases if p["source_type"] == "Digital"]
    phys_weight = sum(p["weight_grams"] for p in phys_purchases)
    phys_invested = sum(p["total_purchase_price"] for p in phys_purchases)
    phys_market = sum(p["weight_grams"] * rate_map.get(p["carat"], r22) for p in phys_purchases) if latest_rate else 0
    digi_weight = sum(p["weight_grams"] for p in digi_purchases)
    digi_invested = sum(p["total_purchase_price"] for p in digi_purchases)
    digi_market = sum(p["weight_grams"] * rate_map.get(p["carat"], r24) for p in digi_purchases) if latest_rate else 0
    scheme_deposited = sum(s["total_deposited"] for s in schemes)
    scheme_bonus = sum(s["bonus_amount"] or 0 for s in schemes)
    total_gold_invested = phys_invested + digi_invested + scheme_deposited
    total_gold_market = phys_market + digi_market + scheme_deposited + scheme_bonus
    total_gold_weight = phys_weight + digi_weight
    total_gain = total_gold_market - total_gold_invested if latest_rate else 0
    gain_pct = (total_gain / total_gold_invested * 100) if total_gold_invested > 0 else 0

    # Gold colour palette
    G = {"dark": "#78350F", "mid": "#92400E", "warm": "#B45309", "accent": "#D97706",
         "light": "#F59E0B", "pale": "#FDE68A", "cream": "#FFFBEB", "glow": "#FEF3C7"}

    # --- Tabs ---
    gt_overview, gt_physical, gt_digital, gt_schemes, gt_rates = st.tabs(
        ["\u2001\U0001f4ca\u2002Overview", "\u2001\U0001f48e\u2002Physical Gold",
         "\u2001\U0001f4f1\u2002Digital Gold", "\u2001\U0001f3e6\u2002Gold Schemes",
         "\u2001\U0001f4c8\u2002Rates & History"])

    # ========== OVERVIEW TAB ==========
    with gt_overview:
        # Hero Banner — gold gradient
        gain_color = COLORS["success"] if total_gain >= 0 else COLORS["danger"]
        gain_sign = "+" if total_gain >= 0 else ""
        st.markdown(
            f'<div style="background:linear-gradient(135deg,{G["dark"]},{G["mid"]},{G["warm"]});border-radius:20px;'
            f'padding:28px 32px;margin-bottom:20px;box-shadow:0 8px 32px rgba(120,53,15,0.3);position:relative;overflow:hidden">'
            f'<div style="position:absolute;top:-40px;right:-40px;width:180px;height:180px;border-radius:50%;'
            f'background:rgba(253,230,138,0.08)"></div>'
            f'<div style="position:absolute;bottom:-50px;left:30%;width:220px;height:220px;border-radius:50%;'
            f'background:rgba(253,230,138,0.05)"></div>'
            f'<div style="display:flex;align-items:center;gap:12px;margin-bottom:6px">'
            f'<div style="font-size:0.72rem;font-weight:700;text-transform:uppercase;letter-spacing:0.12em;'
            f'color:{G["pale"]}80">Gold Portfolio</div></div>'
            f'<div style="display:flex;align-items:baseline;gap:14px;flex-wrap:wrap">'
            f'<div style="font-size:2.2rem;font-weight:900;color:{G["pale"]};letter-spacing:-0.02em">'
            f'{fmt_inr(total_gold_market) if latest_rate else fmt_inr(total_gold_invested)}</div>'
            + (f'<div style="font-size:0.95rem;font-weight:600;color:{gain_color};background:rgba(255,255,255,0.12);'
               f'padding:4px 14px;border-radius:20px">{gain_sign}{fmt_inr(total_gain)} ({gain_pct:+.1f}%)</div>'
               if latest_rate and total_gold_invested > 0 else '')
            + f'</div>'
            f'<div style="display:flex;gap:32px;margin-top:18px;flex-wrap:wrap">'
            f'<div><div style="font-size:0.68rem;color:{G["pale"]}60;text-transform:uppercase;letter-spacing:0.08em">Total Invested</div>'
            f'<div style="font-size:1.1rem;font-weight:700;color:{G["pale"]}">{fmt_inr(total_gold_invested)}</div></div>'
            f'<div><div style="font-size:0.68rem;color:{G["pale"]}60;text-transform:uppercase;letter-spacing:0.08em">Total Weight</div>'
            f'<div style="font-size:1.1rem;font-weight:700;color:{G["pale"]}">{total_gold_weight:.2f} g</div></div>'
            f'<div><div style="font-size:0.68rem;color:{G["pale"]}60;text-transform:uppercase;letter-spacing:0.08em">22K Rate</div>'
            f'<div style="font-size:1.1rem;font-weight:700;color:{G["pale"]}">Rs. {r22:,.0f}/g</div></div>'
            f'<div><div style="font-size:0.68rem;color:{G["pale"]}60;text-transform:uppercase;letter-spacing:0.08em">24K Rate</div>'
            f'<div style="font-size:1.1rem;font-weight:700;color:{G["pale"]}">Rs. {r24:,.0f}/g</div></div>'
            f'<div><div style="font-size:0.68rem;color:{G["pale"]}60;text-transform:uppercase;letter-spacing:0.08em">Rate Date</div>'
            f'<div style="font-size:1.1rem;font-weight:700;color:{G["pale"]}">{rate_date_str}</div></div>'
            f'</div></div>',
            unsafe_allow_html=True,
        )

        # --- Fetch / Update Rates ---
        st.markdown(
            f'<div style="background:linear-gradient(135deg,{G["cream"]},{G["glow"]});border:1px solid {G["accent"]}30;'
            f'border-radius:14px;padding:14px 20px;margin-bottom:16px">'
            f'<div style="font-size:0.78rem;font-weight:700;text-transform:uppercase;letter-spacing:0.06em;'
            f'color:{G["warm"]};margin-bottom:8px">Update Gold Rates</div></div>',
            unsafe_allow_html=True,
        )
        rate_cols = st.columns([1, 1, 1, 1, 1])
        with rate_cols[0]:
            if st.button("Fetch Live Rate", type="primary", use_container_width=True, key="gp_fetch_rate"):
                with st.spinner("Fetching Pune gold rate..."):
                    rate_data = gr.fetch_gold_rate_pune()
                if rate_data:
                    db.save_gold_rate(rate_data["rate_22k"], rate_data["rate_24k"], rate_data["date"])
                    st.success(f"Fetched from {rate_data['source']}")
                    st.rerun()
                else:
                    st.error("Could not fetch. Enter manually.")
        with rate_cols[1]:
            m_22k = st.number_input("22K /g", min_value=0.0, step=10.0, key="gp_m22k")
        with rate_cols[2]:
            m_24k = st.number_input("24K /g", min_value=0.0, step=10.0, key="gp_m24k")
        with rate_cols[3]:
            m_date = st.date_input("Date", value=date.today(), key="gp_mdate")
        with rate_cols[4]:
            st.markdown("<div style='height:28px'></div>", unsafe_allow_html=True)
            if st.button("Save Rate", use_container_width=True, key="gp_save_rate"):
                if m_22k > 0:
                    db.save_gold_rate(m_22k, m_24k if m_24k > 0 else None, m_date.isoformat())
                    st.success("Rate saved!")
                    st.rerun()

        # --- Source Breakdown Cards ---
        section_header("Portfolio Breakdown", "&#x1f4ca;")
        src_cols = st.columns(3)
        src_data = [
            ("Physical Gold", phys_weight, phys_invested, phys_market, len(phys_purchases), G["dark"], "&#x1f48e;"),
            ("Digital Gold (GPay)", digi_weight, digi_invested, digi_market, len(digi_purchases), "#1A73E8", "&#x1f4f1;"),
            ("Gold Schemes", 0, scheme_deposited, scheme_deposited + scheme_bonus, len(schemes), "#059669", "&#x1f3e6;"),
        ]
        for i, (label, wt, inv, mkt, cnt, clr, ico) in enumerate(src_data):
            g = mkt - inv if latest_rate or label == "Gold Schemes" else 0
            gp = (g / inv * 100) if inv > 0 else 0
            gc = COLORS["success"] if g >= 0 else COLORS["danger"]
            with src_cols[i]:
                wt_html = f'<div style="font-size:0.78rem;color:{COLORS["text_muted"]}">{wt:.2f}g</div>' if wt > 0 else ""
                st.markdown(
                    f'<div style="background:{COLORS["card"]};border:1px solid {COLORS["card_border"]};border-radius:14px;'
                    f'padding:16px 18px;box-shadow:{COLORS["card_shadow"]};border-top:3px solid {clr}">'
                    f'<div style="display:flex;align-items:center;gap:8px;margin-bottom:8px">'
                    f'<span style="font-size:1.2rem">{ico}</span>'
                    f'<span style="font-size:0.88rem;font-weight:700;color:{COLORS["text"]}">{label}</span>'
                    f'<span style="margin-left:auto;font-size:0.72rem;color:{COLORS["text_muted"]}">{cnt} items</span></div>'
                    f'<div style="font-size:1.3rem;font-weight:900;color:{COLORS["text"]};margin-bottom:4px">'
                    f'{fmt_inr(mkt) if (latest_rate or label == "Gold Schemes") else fmt_inr(inv)}</div>'
                    f'{wt_html}'
                    f'<div style="display:flex;justify-content:space-between;align-items:center;font-size:0.78rem;margin-top:6px;'
                    f'padding-top:8px;border-top:1px solid {COLORS["card_border"]}">'
                    f'<span style="color:{COLORS["text_muted"]}">Invested: {fmt_inr(inv)}</span>'
                    + (f'<span style="color:{gc};font-weight:600">{"+" if g>=0 else ""}{fmt_inr(g)} ({gp:+.1f}%)</span>'
                       if (latest_rate or label == "Gold Schemes") and inv > 0 else '')
                    + f'</div></div>',
                    unsafe_allow_html=True,
                )

        # --- Charts ---
        if total_gold_invested > 0:
            ch_cols = st.columns(2)
            with ch_cols[0]:
                section_header("Allocation by Source", "&#x1f4ca;")
                alloc_labels = ["Physical", "Digital (GPay)", "Schemes"]
                alloc_vals = [phys_invested, digi_invested, scheme_deposited]
                alloc_colors = [G["accent"], "#4285F4", "#34A853"]
                fig_alloc = go.Figure(go.Pie(
                    labels=alloc_labels, values=alloc_vals, hole=0.55,
                    textinfo="label+percent", textposition="outside",
                    marker=dict(colors=alloc_colors), pull=[0.03]*3,
                ))
                apply_chart_theme(fig_alloc, height=300, margin=dict(t=10, b=10, l=10, r=10))
                fig_alloc.update_layout(showlegend=False)
                fig_alloc.update_traces(textfont_size=11)
                st.plotly_chart(fig_alloc, use_container_width=True)

            with ch_cols[1]:
                section_header("Value vs Investment", "&#x1f4b0;")
                bar_labels = ["Physical", "Digital", "Schemes"]
                bar_inv = [phys_invested, digi_invested, scheme_deposited]
                bar_mkt = [phys_market if latest_rate else phys_invested, digi_market if latest_rate else digi_invested, scheme_deposited + scheme_bonus]
                fig_bar = go.Figure()
                fig_bar.add_trace(go.Bar(name="Market Value", x=bar_labels, y=bar_mkt, marker_color=G["accent"], marker_cornerradius=6))
                fig_bar.add_trace(go.Bar(name="Invested", x=bar_labels, y=bar_inv, marker_color="#CBD5E1", marker_cornerradius=6))
                apply_chart_theme(fig_bar, height=300)
                fig_bar.update_layout(barmode="group", yaxis_title="Rs.")
                st.plotly_chart(fig_bar, use_container_width=True)

        # --- Insights ---
        insights = []
        insights.append(f"Total gold portfolio: <strong>{fmt_inr_full(total_gold_invested)}</strong> invested across physical, digital & scheme holdings.")
        if total_gold_weight > 0:
            avg_price = total_gold_invested / total_gold_weight if total_gold_weight > 0 else 0
            insights.append(f"Total weight: <strong>{total_gold_weight:.2f}g</strong> (physical + digital). Average buy price: <strong>Rs. {avg_price:,.0f}/g</strong>.")
        if latest_rate and total_gold_invested > 0:
            gc = COLORS["success"] if total_gain >= 0 else COLORS["danger"]
            insights.append(f"Portfolio gain: <strong style='color:{gc}'>{gain_sign}{fmt_inr_full(total_gain)} ({gain_pct:+.1f}%)</strong> at current rates.")
        if phys_invested > 0 and digi_invested > 0:
            phys_pct = phys_invested / total_gold_invested * 100
            digi_pct = digi_invested / total_gold_invested * 100
            sch_pct = scheme_deposited / total_gold_invested * 100
            insights.append(f"Allocation: Physical {phys_pct:.0f}%, Digital {digi_pct:.0f}%, Schemes {sch_pct:.0f}%.")
        if scheme_bonus > 0:
            insights.append(f"Scheme bonus earned: <strong>{fmt_inr_full(scheme_bonus)}</strong> from jeweller schemes.")
        active_schemes = [s for s in schemes if s["status"] == "Active"]
        if active_schemes:
            monthly_sch = sum(s["monthly_amount"] for s in active_schemes)
            insights.append(f"Active schemes: <strong>{len(active_schemes)}</strong>, monthly commitment: <strong>{fmt_inr_full(monthly_sch)}</strong>.")
        all_src = db.get_sources()
        nw = sum(db.get_latest_balance(src["id"]) for src in all_src)
        if nw > 0:
            gold_nw_pct = (total_gold_market if latest_rate else total_gold_invested) / nw * 100
            insights.append(f"Gold represents <strong>{gold_nw_pct:.1f}%</strong> of your total net worth.")
        insight_box(insights, "Gold Portfolio Insights")

    # ========== PHYSICAL GOLD TAB ==========
    with gt_physical:
        # Add purchase banner
        st.markdown(
            f'<div style="background:linear-gradient(135deg,{G["cream"]},{G["glow"]},{G["pale"]}50);'
            f'border:1px solid {G["accent"]}30;border-radius:16px;padding:20px 24px;margin-bottom:18px;'
            f'border-left:4px solid {G["accent"]}">'
            f'<div style="display:flex;align-items:center;gap:12px">'
            f'<div style="width:42px;height:42px;border-radius:12px;background:linear-gradient(135deg,{G["accent"]},{G["warm"]});'
            f'display:flex;align-items:center;justify-content:center;flex-shrink:0;box-shadow:0 4px 12px rgba(217,119,6,0.25)">'
            f'<span style="font-size:1.2rem">&#x1f48e;</span></div>'
            f'<div>'
            f'<div style="font-size:1rem;font-weight:800;color:{COLORS["text"]}">Add Physical Gold Purchase</div>'
            f'<div style="font-size:0.8rem;color:{COLORS["text_secondary"]};margin-top:2px">'
            f'Jewellery, coins, bars from any jeweller. Price will be compared against live rates.</div>'
            f'</div></div></div>',
            unsafe_allow_html=True,
        )

        if "gp_phys_ver" not in st.session_state:
            st.session_state["gp_phys_ver"] = 0
        gpv = st.session_state["gp_phys_ver"]

        fc = st.columns([2, 2, 1, 1])
        with fc[0]:
            gp_desc = st.text_input("Item Description *", placeholder="e.g. Gold Chain, Coin 10g", key=f"gpp_desc_{gpv}")
        with fc[1]:
            gp_seller = st.text_input("Jeweller *", placeholder="e.g. Tanishq, Malabar, Kalyan", key=f"gpp_sell_{gpv}")
        with fc[2]:
            gp_weight = st.number_input("Weight (g) *", min_value=0.01, step=0.1, format="%.3f", key=f"gpp_wt_{gpv}")
        with fc[3]:
            gp_carat = st.selectbox("Purity", ["22K", "24K", "18K"], key=f"gpp_ct_{gpv}")

        fc2 = st.columns([1, 1, 1, 2])
        with fc2[0]:
            gp_price = st.number_input("Total Price (Rs.) *", min_value=0.0, step=100.0, format="%.2f", key=f"gpp_pr_{gpv}")
        with fc2[1]:
            gp_date = st.date_input("Purchase Date", value=date.today(), key=f"gpp_dt_{gpv}")
        with fc2[2]:
            ppg = gp_price / gp_weight if gp_weight > 0 else 0
            st.markdown(
                f'<div style="margin-top:26px;background:{G["cream"]};border:1px solid {G["accent"]}20;border-radius:10px;padding:8px;text-align:center">'
                f'<div style="font-size:0.6rem;font-weight:600;text-transform:uppercase;color:{COLORS["text_muted"]}">Price/g</div>'
                f'<div style="font-size:1rem;font-weight:800;color:{G["warm"]}">Rs. {ppg:,.0f}</div></div>',
                unsafe_allow_html=True)
        with fc2[3]:
            gp_note = st.text_input("Note", placeholder="Receipt #, hallmark, occasion", key=f"gpp_note_{gpv}")

        if st.button("Add Physical Gold", type="primary", use_container_width=True, key=f"gpp_add_{gpv}"):
            if gp_desc and gp_seller and gp_weight > 0 and gp_price > 0:
                db.add_gold_purchase(gp_desc, gp_seller, gp_weight, gp_carat, gp_price, gp_date.isoformat(), gp_note, "Physical")
                st.success(f"Added: {gp_desc} ({gp_weight}g {gp_carat}) from {gp_seller}")
                st.session_state["gp_phys_ver"] += 1
                st.rerun()
            else:
                st.error("Please fill in all required fields.")

        # --- Physical Gold Holdings ---
        if phys_purchases:
            st.markdown("<div style='height:12px'></div>", unsafe_allow_html=True)
            section_header(f"Physical Holdings ({len(phys_purchases)} items, {phys_weight:.2f}g)", "&#x1f48e;")

            editing_gp_id = st.session_state.get("gp_editing_id")

            for p in phys_purchases:
                pid = p["id"]
                curr_rate = rate_map.get(p["carat"], r22) if latest_rate else 0
                market_val = p["weight_grams"] * curr_rate
                buy_ppg = p["purchase_price_per_gram"]
                gain_item = market_val - p["total_purchase_price"] if latest_rate else 0
                gain_pct_item = (gain_item / p["total_purchase_price"] * 100) if p["total_purchase_price"] > 0 and latest_rate else 0
                gc = COLORS["success"] if gain_item >= 0 else COLORS["danger"]

                if editing_gp_id == pid:
                    st.markdown(
                        f'<div style="background:linear-gradient(135deg,{G["cream"]},#FEF3C7);border:2px solid {G["accent"]};'
                        f'border-radius:14px;padding:14px 18px;margin-bottom:8px">',
                        unsafe_allow_html=True)
                    ec = st.columns([2, 2, 1, 1, 1.5])
                    with ec[0]:
                        e_desc = st.text_input("Description", value=p["description"], key=f"gpe_desc_{pid}")
                    with ec[1]:
                        e_seller = st.text_input("Jeweller", value=p["seller"] or "", key=f"gpe_sell_{pid}")
                    with ec[2]:
                        e_weight = st.number_input("Weight", value=float(p["weight_grams"]), min_value=0.01, step=0.1, format="%.3f", key=f"gpe_wt_{pid}")
                    with ec[3]:
                        ct_opts = ["22K", "24K", "18K"]
                        e_carat = st.selectbox("Purity", ct_opts, index=ct_opts.index(p["carat"]), key=f"gpe_ct_{pid}")
                    with ec[4]:
                        e_price = st.number_input("Total Price", value=float(p["total_purchase_price"]), min_value=0.0, step=100.0, format="%.2f", key=f"gpe_pr_{pid}")
                    ec2 = st.columns([1, 2, 1, 1])
                    with ec2[0]:
                        e_date = st.date_input("Date", value=date.fromisoformat(p["purchase_date"]), key=f"gpe_dt_{pid}")
                    with ec2[1]:
                        e_note = st.text_input("Note", value=p["note"] or "", key=f"gpe_note_{pid}")
                    with ec2[2]:
                        if st.button("Save", type="primary", key=f"gpe_save_{pid}", use_container_width=True):
                            db.update_gold_purchase(pid, e_desc, e_seller, e_weight, e_carat, e_price, e_date.isoformat(), e_note, "Physical")
                            st.session_state.pop("gp_editing_id", None)
                            st.rerun()
                    with ec2[3]:
                        if st.button("Cancel", key=f"gpe_cancel_{pid}", use_container_width=True):
                            st.session_state.pop("gp_editing_id", None)
                            st.rerun()
                    st.markdown("</div>", unsafe_allow_html=True)
                else:
                    card_cols = st.columns([12, 1, 1])
                    with card_cols[0]:
                        mkt_html = f"Mkt: {fmt_inr(market_val)}" if latest_rate else ""
                        var_html = (f'<span style="color:{gc};font-weight:700;margin-left:8px">'
                                    f'{"+" if gain_item>=0 else ""}{fmt_inr(gain_item)} ({gain_pct_item:+.1f}%)</span>') if latest_rate else ""
                        st.markdown(
                            f'<div style="display:flex;align-items:center;gap:14px;padding:12px 16px;margin-bottom:5px;'
                            f'background:{COLORS["card"]};border:1px solid {COLORS["card_border"]};border-radius:12px;'
                            f'box-shadow:{COLORS["card_shadow"]};border-left:3px solid {G["accent"]}">'
                            f'<div style="min-width:44px;text-align:center">'
                            f'<span style="background:{G["cream"]};color:{G["warm"]};padding:3px 10px;'
                            f'border-radius:10px;font-size:0.78rem;font-weight:700">{p["carat"]}</span></div>'
                            f'<div style="flex:1;min-width:0">'
                            f'<div style="font-size:0.92rem;font-weight:700;color:{COLORS["text"]}">{p["description"]}'
                            f'<span style="font-weight:400;color:{COLORS["text_muted"]};font-size:0.78rem;margin-left:8px">{p["seller"] or ""}</span></div>'
                            f'<div style="font-size:0.75rem;color:{COLORS["text_muted"]};margin-top:2px">'
                            f'{p["weight_grams"]:.3f}g &middot; Buy: Rs. {buy_ppg:,.0f}/g &middot; {p["purchase_date"]}'
                            f'{" &middot; " + p["note"] if p["note"] else ""}</div></div>'
                            f'<div style="text-align:right;min-width:160px">'
                            f'<div style="font-size:0.88rem;font-weight:700;color:{COLORS["text"]}">Buy: {fmt_inr(p["total_purchase_price"])}</div>'
                            f'<div style="font-size:0.78rem;color:{COLORS["text_muted"]};margin-top:1px">{mkt_html}{var_html}</div>'
                            f'</div></div>',
                            unsafe_allow_html=True)
                    with card_cols[1]:
                        if st.button("\u270f\ufe0f", key=f"gp_edit_{pid}", help="Edit"):
                            st.session_state["gp_editing_id"] = pid
                            st.session_state.pop("gp_confirm_del", None)
                            st.rerun()
                    with card_cols[2]:
                        if st.session_state.get("gp_confirm_del") == pid:
                            if st.button("\u2705", key=f"gp_cdel_{pid}", help="Confirm delete"):
                                db.deactivate_gold_purchase(pid)
                                st.session_state.pop("gp_confirm_del", None)
                                st.rerun()
                        else:
                            if st.button("\U0001f5d1", key=f"gp_del_{pid}", help="Delete"):
                                st.session_state["gp_confirm_del"] = pid
                                st.rerun()
        else:
            st.markdown(
                f'<div style="text-align:center;padding:40px;background:linear-gradient(135deg,{COLORS["card"]},{G["cream"]});'
                f'border:1px dashed {G["accent"]}40;border-radius:16px;margin-top:16px">'
                f'<div style="font-size:2.5rem;margin-bottom:8px">&#x1f48e;</div>'
                f'<div style="font-size:0.95rem;font-weight:600;color:{COLORS["text"]}">No physical gold yet</div>'
                f'<div style="font-size:0.82rem;color:{COLORS["text_muted"]}">Add your first jewellery, coin or bar above.</div></div>',
                unsafe_allow_html=True)

    # ========== DIGITAL GOLD TAB ==========
    with gt_digital:
        st.markdown(
            f'<div style="background:linear-gradient(135deg,#EBF5FF,#DBEAFE,#BFDBFE);'
            f'border:1px solid #3B82F620;border-radius:16px;padding:20px 24px;margin-bottom:18px;'
            f'border-left:4px solid #2563EB">'
            f'<div style="display:flex;align-items:center;gap:12px">'
            f'<div style="width:42px;height:42px;border-radius:12px;background:linear-gradient(135deg,#2563EB,#3B82F6);'
            f'display:flex;align-items:center;justify-content:center;flex-shrink:0;box-shadow:0 4px 12px rgba(37,99,235,0.25)">'
            f'<span style="font-size:1.2rem;filter:brightness(0) invert(1)">&#x1f4f1;</span></div>'
            f'<div>'
            f'<div style="font-size:1rem;font-weight:800;color:{COLORS["text"]}">Add Digital Gold (Google Pay)</div>'
            f'<div style="font-size:0.8rem;color:{COLORS["text_secondary"]};margin-top:2px">'
            f'Track gold purchased through Google Pay or other digital platforms.</div>'
            f'</div></div></div>',
            unsafe_allow_html=True,
        )

        if "gp_digi_ver" not in st.session_state:
            st.session_state["gp_digi_ver"] = 0
        gdv = st.session_state["gp_digi_ver"]

        dc = st.columns([1, 1, 1, 2])
        with dc[0]:
            dg_weight = st.number_input("Weight (g) *", min_value=0.001, step=0.01, format="%.4f", key=f"dgp_wt_{gdv}")
        with dc[1]:
            dg_price = st.number_input("Purchase Price (Rs.) *", min_value=0.0, step=100.0, format="%.2f", key=f"dgp_pr_{gdv}")
        with dc[2]:
            dg_date = st.date_input("Purchase Date", value=date.today(), key=f"dgp_dt_{gdv}")
        with dc[3]:
            dg_note = st.text_input("Note", placeholder="Transaction ID, platform", key=f"dgp_note_{gdv}")

        if st.button("Add Digital Gold", type="primary", use_container_width=True, key=f"dgp_add_{gdv}"):
            if dg_weight > 0 and dg_price > 0:
                db.add_gold_purchase(f"Digital Gold ({dg_weight:.4f}g)", "Google Pay", dg_weight, "24K", dg_price, dg_date.isoformat(), dg_note, "Digital")
                st.success(f"Added: {dg_weight:.4f}g digital gold for {fmt_inr_full(dg_price)}")
                st.session_state["gp_digi_ver"] += 1
                st.rerun()
            else:
                st.error("Weight and price are required.")

        # Digital holdings
        if digi_purchases:
            st.markdown("<div style='height:12px'></div>", unsafe_allow_html=True)
            section_header(f"Digital Gold Holdings ({digi_weight:.4f}g, {len(digi_purchases)} transactions)", "&#x1f4f1;")

            editing_dg_id = st.session_state.get("dg_editing_id")

            for p in digi_purchases:
                pid = p["id"]
                curr_rate = rate_map.get(p["carat"], r24) if latest_rate else 0
                market_val = p["weight_grams"] * curr_rate
                gain_item = market_val - p["total_purchase_price"] if latest_rate else 0
                gp_item = (gain_item / p["total_purchase_price"] * 100) if p["total_purchase_price"] > 0 and latest_rate else 0
                gc = COLORS["success"] if gain_item >= 0 else COLORS["danger"]

                if editing_dg_id == pid:
                    st.markdown(f'<div style="background:#EBF5FF;border:2px solid #2563EB;border-radius:12px;padding:12px 16px;margin-bottom:6px">', unsafe_allow_html=True)
                    dec = st.columns([1, 1, 1, 2, 0.6, 0.6])
                    with dec[0]:
                        de_wt = st.number_input("Weight", value=float(p["weight_grams"]), min_value=0.001, step=0.01, format="%.4f", key=f"dge_wt_{pid}")
                    with dec[1]:
                        de_pr = st.number_input("Price", value=float(p["total_purchase_price"]), min_value=0.0, step=100.0, format="%.2f", key=f"dge_pr_{pid}")
                    with dec[2]:
                        de_dt = st.date_input("Date", value=date.fromisoformat(p["purchase_date"]), key=f"dge_dt_{pid}")
                    with dec[3]:
                        de_note = st.text_input("Note", value=p["note"] or "", key=f"dge_note_{pid}")
                    with dec[4]:
                        st.markdown("<div style='height:28px'></div>", unsafe_allow_html=True)
                        if st.button("\u2714", key=f"dge_save_{pid}", use_container_width=True):
                            db.update_gold_purchase(pid, f"Digital Gold ({de_wt:.4f}g)", "Google Pay", de_wt, "24K", de_pr, de_dt.isoformat(), de_note, "Digital")
                            st.session_state.pop("dg_editing_id", None)
                            st.rerun()
                    with dec[5]:
                        st.markdown("<div style='height:28px'></div>", unsafe_allow_html=True)
                        if st.button("\u2718", key=f"dge_cancel_{pid}", use_container_width=True):
                            st.session_state.pop("dg_editing_id", None)
                            st.rerun()
                    st.markdown("</div>", unsafe_allow_html=True)
                else:
                    dc2 = st.columns([12, 1, 1])
                    with dc2[0]:
                        mkt_html = f"Mkt: {fmt_inr(market_val)}" if latest_rate else ""
                        var_html = (f'<span style="color:{gc};font-weight:700;margin-left:8px">'
                                    f'{"+" if gain_item>=0 else ""}{fmt_inr(gain_item)} ({gp_item:+.1f}%)</span>') if latest_rate else ""
                        st.markdown(
                            f'<div style="display:flex;align-items:center;gap:14px;padding:10px 16px;margin-bottom:4px;'
                            f'background:{COLORS["card"]};border:1px solid {COLORS["card_border"]};border-radius:10px;'
                            f'border-left:3px solid #2563EB">'
                            f'<div style="flex:1">'
                            f'<div style="font-size:0.88rem;font-weight:700;color:{COLORS["text"]}">{p["weight_grams"]:.4f}g'
                            f'<span style="font-size:0.75rem;font-weight:400;color:{COLORS["text_muted"]};margin-left:8px">'
                            f'24K &middot; Buy: Rs. {p["purchase_price_per_gram"]:,.0f}/g &middot; {p["purchase_date"]}'
                            f'{" &middot; " + p["note"] if p["note"] else ""}</span></div></div>'
                            f'<div style="text-align:right;min-width:150px">'
                            f'<div style="font-size:0.85rem;font-weight:700;color:{COLORS["text"]}">Buy: {fmt_inr(p["total_purchase_price"])}</div>'
                            f'<div style="font-size:0.75rem">{mkt_html}{var_html}</div></div></div>',
                            unsafe_allow_html=True)
                    with dc2[1]:
                        if st.button("\u270f\ufe0f", key=f"dg_edit_{pid}", help="Edit"):
                            st.session_state["dg_editing_id"] = pid
                            st.session_state.pop("dg_confirm_del", None)
                            st.rerun()
                    with dc2[2]:
                        if st.session_state.get("dg_confirm_del") == pid:
                            if st.button("\u2705", key=f"dg_cdel_{pid}", help="Confirm"):
                                db.deactivate_gold_purchase(pid)
                                st.session_state.pop("dg_confirm_del", None)
                                st.rerun()
                        else:
                            if st.button("\U0001f5d1", key=f"dg_del_{pid}", help="Delete"):
                                st.session_state["dg_confirm_del"] = pid
                                st.rerun()
        else:
            st.markdown(
                f'<div style="text-align:center;padding:40px;background:linear-gradient(135deg,{COLORS["card"]},#EBF5FF);'
                f'border:1px dashed #3B82F640;border-radius:16px;margin-top:16px">'
                f'<div style="font-size:2.5rem;margin-bottom:8px">&#x1f4f1;</div>'
                f'<div style="font-size:0.95rem;font-weight:600;color:{COLORS["text"]}">No digital gold yet</div>'
                f'<div style="font-size:0.82rem;color:{COLORS["text_muted"]}">Add your first Google Pay gold purchase above.</div></div>',
                unsafe_allow_html=True)

    # ========== GOLD SCHEMES TAB ==========
    with gt_schemes:
        if schemes:
            section_header(f"Gold Schemes ({len(schemes)} schemes, {fmt_inr(scheme_deposited)} deposited)", "&#x1f3e6;")

            active_schemes = [s for s in schemes if s["status"] == "Active"]
            matured_schemes = [s for s in schemes if s["status"] != "Active"]

            if active_schemes:
                st.markdown(
                    f'<div style="font-size:0.78rem;font-weight:700;text-transform:uppercase;letter-spacing:0.08em;'
                    f'color:{COLORS["success"]};margin-bottom:8px">Active Schemes</div>',
                    unsafe_allow_html=True)
                for s in active_schemes:
                    pct = (s["months_paid"] / s["total_months"] * 100) if s["total_months"] > 0 else 0
                    remaining = s["total_months"] - s["months_paid"]
                    remaining_amt = remaining * s["monthly_amount"]
                    st.markdown(
                        f'<div style="background:{COLORS["card"]};border:1px solid {COLORS["card_border"]};border-radius:14px;'
                        f'padding:16px 20px;margin-bottom:8px;box-shadow:{COLORS["card_shadow"]};border-left:4px solid {G["accent"]}">'
                        f'<div style="display:flex;justify-content:space-between;align-items:flex-start;margin-bottom:10px">'
                        f'<div>'
                        f'<div style="font-size:0.95rem;font-weight:800;color:{COLORS["text"]}">{s["scheme_name"]}</div>'
                        f'<div style="font-size:0.78rem;color:{COLORS["text_muted"]}">{s["jeweller"]} &middot; Rs. {s["monthly_amount"]:,.0f}/mo &middot; Started {s["start_date"] or "N/A"}</div>'
                        f'</div>'
                        f'<div style="text-align:right">'
                        f'<div style="font-size:1.05rem;font-weight:800;color:{COLORS["text"]}">{fmt_inr(s["total_deposited"])}</div>'
                        f'<div style="font-size:0.75rem;color:{COLORS["text_muted"]}">{s["months_paid"]}/{s["total_months"]} months</div>'
                        f'</div></div>'
                        f'<div style="background:{COLORS["surface"]};border-radius:6px;height:10px;overflow:hidden;margin-bottom:6px">'
                        f'<div style="width:{pct:.1f}%;height:100%;background:linear-gradient(90deg,{G["accent"]},{G["light"]});'
                        f'border-radius:6px"></div></div>'
                        f'<div style="display:flex;justify-content:space-between;font-size:0.72rem;color:{COLORS["text_muted"]}">'
                        f'<span>{pct:.0f}% complete</span>'
                        f'<span>{remaining} months left (Rs. {remaining_amt:,.0f})</span>'
                        + (f'<span>Bonus: {fmt_inr(s["bonus_amount"])}</span>' if s["bonus_amount"] else '')
                        + f'</div></div>',
                        unsafe_allow_html=True)

            if matured_schemes:
                st.markdown(
                    f'<div style="font-size:0.78rem;font-weight:700;text-transform:uppercase;letter-spacing:0.08em;'
                    f'color:{COLORS["text_muted"]};margin:16px 0 8px 0">Completed / Matured</div>',
                    unsafe_allow_html=True)
                for s in matured_schemes:
                    st.markdown(
                        f'<div style="background:{COLORS["card"]};border:1px solid {COLORS["card_border"]};border-radius:10px;'
                        f'padding:12px 16px;margin-bottom:6px;opacity:0.8">'
                        f'<div style="display:flex;justify-content:space-between;align-items:center">'
                        f'<div><span style="font-weight:700;color:{COLORS["text"]}">{s["scheme_name"]}</span>'
                        f'<span style="font-size:0.78rem;color:{COLORS["text_muted"]};margin-left:8px">{s["jeweller"]}</span></div>'
                        f'<div style="text-align:right">'
                        f'<span style="font-weight:700;color:{COLORS["text"]}">{fmt_inr(s["total_deposited"])}</span>'
                        f'<span style="background:{COLORS["success"]}15;color:{COLORS["success"]};padding:2px 8px;border-radius:8px;'
                        f'font-size:0.72rem;font-weight:600;margin-left:8px">Matured</span></div></div></div>',
                        unsafe_allow_html=True)

            st.markdown(
                f'<div style="margin-top:14px;padding:10px 16px;background:{G["cream"]};border:1px solid {G["accent"]}20;'
                f'border-radius:10px;font-size:0.82rem;color:{COLORS["text_secondary"]}">'
                f'Manage schemes, add payments & view payment history on the <strong>Gold Schemes</strong> page from the sidebar.</div>',
                unsafe_allow_html=True)
        else:
            st.markdown(
                f'<div style="text-align:center;padding:40px;background:linear-gradient(135deg,{COLORS["card"]},{G["cream"]});'
                f'border:1px dashed {G["accent"]}40;border-radius:16px">'
                f'<div style="font-size:2.5rem;margin-bottom:8px">&#x1f3e6;</div>'
                f'<div style="font-size:0.95rem;font-weight:600;color:{COLORS["text"]}">No gold schemes yet</div>'
                f'<div style="font-size:0.82rem;color:{COLORS["text_muted"]}">Add gold savings schemes from the Gold Schemes page.</div></div>',
                unsafe_allow_html=True)

    # ========== RATES & HISTORY TAB ==========
    with gt_rates:
        rate_hist = db.get_gold_rate_history()
        if rate_hist:
            section_header("Gold Rate Trend", "&#x1f4c8;")
            rh_df = pd.DataFrame([dict(r) for r in rate_hist])
            rh_df["rate_date"] = pd.to_datetime(rh_df["rate_date"])

            fig = go.Figure()
            fig.add_trace(go.Scatter(
                x=rh_df["rate_date"], y=rh_df["rate_per_gram_22k"],
                mode="lines+markers", name="22K",
                line=dict(color=G["accent"], width=3, shape="spline"),
                marker=dict(size=7, color=G["accent"], line=dict(width=2, color=COLORS["white"])),
                fill="tozeroy", fillcolor="rgba(217,119,6,0.08)",
            ))
            if rh_df["rate_per_gram_24k"].notna().any():
                fig.add_trace(go.Scatter(
                    x=rh_df["rate_date"], y=rh_df["rate_per_gram_24k"],
                    mode="lines+markers", name="24K",
                    line=dict(color="#EA580C", width=3, shape="spline"),
                    marker=dict(size=7, color="#EA580C", line=dict(width=2, color=COLORS["white"])),
                ))
            apply_chart_theme(fig, height=380, yaxis=dict(title="Rate / gram (Rs.)"))
            st.plotly_chart(fig, use_container_width=True)

            # Rate table
            section_header("Rate History", "&#x1f4c5;")
            for _, r in rh_df.sort_values("rate_date", ascending=False).iterrows():
                r24_str = f"Rs. {r['rate_per_gram_24k']:,.0f}" if pd.notna(r['rate_per_gram_24k']) else "N/A"
                st.markdown(
                    f'<div style="display:flex;align-items:center;gap:16px;padding:8px 14px;margin-bottom:3px;'
                    f'background:{COLORS["card"]};border:1px solid {COLORS["card_border"]};border-radius:8px;font-size:0.82rem">'
                    f'<span style="color:{COLORS["text_muted"]};min-width:90px">{r["rate_date"].strftime("%d %b %Y")}</span>'
                    f'<span style="color:{G["warm"]};font-weight:700;min-width:110px">22K: Rs. {r["rate_per_gram_22k"]:,.0f}</span>'
                    f'<span style="color:#EA580C;font-weight:700">24K: {r24_str}</span></div>',
                    unsafe_allow_html=True)

            if len(rh_df) >= 2:
                st.markdown("<div style='height:12px'></div>", unsafe_allow_html=True)
                section_header("Rate Change Summary", "&#x1f4b9;")
                first_rate = rh_df.iloc[-1]["rate_per_gram_22k"]
                last_rate = rh_df.iloc[0]["rate_per_gram_22k"]
                change = last_rate - first_rate
                pct = (change / first_rate) * 100 if first_rate > 0 else 0
                chg_style = "green" if change >= 0 else "amber"
                metric_row(
                    ("First Recorded", f"Rs. {first_rate:,.0f}", rh_df.iloc[-1]["rate_date"].strftime("%d %b %Y"), "blue", ""),
                    ("Latest Rate", f"Rs. {last_rate:,.0f}", rh_df.iloc[0]["rate_date"].strftime("%d %b %Y"), "gold", ""),
                    ("Change (22K)", f"Rs. {change:,.0f}", f"{pct:+.1f}%", chg_style, ""),
                )
        else:
            st.markdown(
                f'<div style="text-align:center;padding:40px;background:{COLORS["card"]};border:1px dashed {COLORS["card_border"]};'
                f'border-radius:16px">'
                f'<div style="font-size:2.5rem;margin-bottom:8px">&#x1f4c8;</div>'
                f'<div style="font-size:0.95rem;font-weight:600;color:{COLORS["text"]}">No rate history yet</div>'
                f'<div style="font-size:0.82rem;color:{COLORS["text_muted"]}">Fetch or enter a rate on the Overview tab to start tracking.</div></div>',
                unsafe_allow_html=True)

# ======================== STOCK PORTFOLIO ========================
elif page == "Shares & Stock":
    page_title("Shares & Stock", "Track your stock portfolio, current values, and sell transactions")

    # --- USD/INR rate ---
    fx_rate = db.get_latest_exchange_rate()
    usd_inr = fx_rate["rate"] if fx_rate else 0

    col_fx1, col_fx2 = st.columns([1, 3])
    with col_fx1:
        if st.button("Fetch USD/INR Rate", use_container_width=True):
            with st.spinner("Fetching..."):
                fx = sp.fetch_usd_inr_rate()
            if fx:
                db.save_exchange_rate(fx["rate"], fx["date"])
                st.success(f"USD/INR: Rs. {fx['rate']}")
                st.rerun()
            else:
                st.error("Could not fetch exchange rate.")
    with col_fx2:
        if fx_rate:
            st.markdown(f"""<div style="padding:8px 16px;background:{COLORS['surface2']};border-radius:8px;
                display:inline-flex;align-items:center;gap:8px;margin-top:4px">
                <span style="color:{COLORS['text_muted']};font-size:0.85rem">USD/INR</span>
                <span style="font-weight:700;color:{COLORS['primary']};font-size:1.1rem">Rs. {fx_rate['rate']:,.2f}</span>
                <span style="color:{COLORS['text_muted']};font-size:0.75rem">({fx_rate['rate_date']})</span>
            </div>""", unsafe_allow_html=True)

    # --- Tabs ---
    tab_portfolio, tab_update_val, tab_sell, tab_add, tab_manage = st.tabs(
        ["\u2001📊\u2002Portfolio", "\u2001📈\u2002Update Value", "\u2001💸\u2002Sell Stock", "\u2001➕\u2002Add Holding", "\u2001⚙️\u2002Manage"])

    all_holdings = db.get_stock_holdings()

    # ---- PORTFOLIO TAB ----
    with tab_portfolio:
        if all_holdings:
            # --- Compute combined totals ---
            total_invested_all_inr = 0
            total_current_all_inr = 0

            for h in all_holdings:
                latest_val = db.get_latest_stock_value(h["id"])
                curr_val = latest_val["current_value"] if latest_val else 0
                invested = h["total_buy_price"]
                if h["market"] == "US" and usd_inr:
                    total_invested_all_inr += invested * usd_inr
                    total_current_all_inr += curr_val * usd_inr if curr_val else invested * usd_inr
                else:
                    total_invested_all_inr += invested
                    total_current_all_inr += curr_val if curr_val else invested

            total_gain_all = total_current_all_inr - total_invested_all_inr
            gain_pct_all = (total_gain_all / total_invested_all_inr * 100) if total_invested_all_inr > 0 else 0

            sell_summary = db.get_stock_sell_summary()
            total_sold_inr = 0
            for ss in sell_summary:
                if ss["currency"] == "USD" and usd_inr:
                    total_sold_inr += ss["total_sold"] * usd_inr
                else:
                    total_sold_inr += ss["total_sold"]

            india_holdings = [h for h in all_holdings if h["market"] == "India"]
            us_holdings = [h for h in all_holdings if h["market"] == "US"]

            # --- Combined overview bar ---
            india_inv = sum(h["total_buy_price"] for h in india_holdings)
            us_inv_usd = sum(h["total_buy_price"] for h in us_holdings)
            us_inv_inr = us_inv_usd * usd_inr if usd_inr else 0
            india_pct = (india_inv / total_invested_all_inr * 100) if total_invested_all_inr > 0 else 0
            us_pct = 100 - india_pct if total_invested_all_inr > 0 else 0

            st.markdown(
                f'<div style="background:{COLORS["card"]};border:1px solid {COLORS["card_border"]};border-radius:14px;'
                f'padding:18px 22px;margin-bottom:20px;box-shadow:{COLORS["card_shadow"]}">'
                f'<div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:14px">'
                f'<div style="font-size:0.72rem;font-weight:700;text-transform:uppercase;letter-spacing:0.06em;color:{COLORS["text_muted"]}">Combined Portfolio</div>'
                f'<div style="font-size:1.15rem;font-weight:800;color:{COLORS["text"]}">{fmt_inr_full(total_current_all_inr)}'
                f'<span style="font-size:0.82rem;font-weight:600;margin-left:8px;color:{COLORS["success"] if total_gain_all>=0 else COLORS["danger"]}">'
                f'{"+" if total_gain_all>=0 else ""}{fmt_inr(total_gain_all)} ({gain_pct_all:+.1f}%)</span></div></div>'
                f'<div style="display:flex;height:10px;border-radius:6px;overflow:hidden;margin-bottom:10px">'
                f'<div style="width:{india_pct}%;background:linear-gradient(90deg,#F97316,#FB923C)" title="India {india_pct:.0f}%"></div>'
                f'<div style="width:{us_pct}%;background:linear-gradient(90deg,#3B82F6,#60A5FA)" title="US {us_pct:.0f}%"></div></div>'
                f'<div style="display:flex;justify-content:space-between;font-size:0.78rem">'
                f'<div><span style="display:inline-block;width:10px;height:10px;border-radius:3px;background:#F97316;margin-right:6px"></span>'
                f'<span style="color:{COLORS["text_secondary"]}">India: {fmt_inr(india_inv)} ({india_pct:.0f}%)</span></div>'
                f'<div><span style="display:inline-block;width:10px;height:10px;border-radius:3px;background:#3B82F6;margin-right:6px"></span>'
                f'<span style="color:{COLORS["text_secondary"]}">US: {fmt_inr(us_inv_inr)} ({us_pct:.0f}%)</span></div>'
                f'<div style="color:{COLORS["text_muted"]}">Invested: {fmt_inr(total_invested_all_inr)} &middot; {len(all_holdings)} holdings</div>'
                f'</div></div>',
                unsafe_allow_html=True,
            )

            # --- Market sub-tabs ---
            mkt_tab_india, mkt_tab_us = st.tabs(["\u2001\U0001f1ee\U0001f1f3\u2002Indian Stocks", "\u2001\U0001f1fa\U0001f1f8\u2002US Stocks"])

            # ===== INDIA TAB =====
            with mkt_tab_india:
                if india_holdings:
                    # India metrics
                    in_invested = sum(h["total_buy_price"] for h in india_holdings)
                    in_current = 0
                    for h in india_holdings:
                        lv = db.get_latest_stock_value(h["id"])
                        in_current += lv["current_value"] if lv else h["total_buy_price"]
                    in_gain = in_current - in_invested
                    in_gain_pct = (in_gain / in_invested * 100) if in_invested > 0 else 0
                    in_g_style = "green" if in_gain >= 0 else "amber"

                    metric_row(
                        ("Holdings", str(len(india_holdings)), "Indian market", "blue", "&#x1f4bc;"),
                        ("Invested", fmt_inr_full(in_invested), fmt_inr_words(in_invested), "blue", "&#x1f4b5;"),
                        ("Current Value", fmt_inr_full(in_current), fmt_inr_words(in_current), "green" if in_current >= in_invested else "amber", "&#x1f4b0;"),
                        ("Gain/Loss", f"{'+'if in_gain>=0 else ''}{fmt_inr_full(in_gain)}", f"{in_gain_pct:+.1f}%", in_g_style, "&#x1f4c8;"),
                    )

                    # Holdings cards
                    st.markdown("<div style='height:8px'></div>", unsafe_allow_html=True)
                    for h in india_holdings:
                        lv = db.get_latest_stock_value(h["id"])
                        cp = lv["current_price"] if lv else None
                        cv = lv["current_value"] if lv else None
                        vd = lv["update_date"] if lv else None
                        g = cv - h["total_buy_price"] if cv else None
                        gp = (g / h["total_buy_price"] * 100) if g is not None and h["total_buy_price"] > 0 else None
                        gc = COLORS["success"] if (g is not None and g >= 0) else COLORS["danger"]
                        gx = "+" if (g is not None and g >= 0) else ""

                        st.markdown(
                            f'<div style="display:flex;align-items:center;gap:14px;padding:12px 16px;margin-bottom:6px;'
                            f'background:{COLORS["card"]};border:1px solid {COLORS["card_border"]};border-radius:12px;'
                            f'box-shadow:{COLORS["card_shadow"]};border-left:3px solid #F97316">'
                            f'<div style="min-width:56px;text-align:center">'
                            f'<span style="background:{COLORS["surface2"]};padding:3px 10px;border-radius:10px;'
                            f'font-size:0.78rem;font-weight:700;color:{COLORS["primary"]}">{h["ticker"]}</span>'
                            f'<div style="font-size:0.65rem;color:{COLORS["text_muted"]};margin-top:3px">{h["exchange"]}</div></div>'
                            f'<div style="flex:1;min-width:0">'
                            f'<div style="font-size:0.92rem;font-weight:700;color:{COLORS["text"]}">{h["name"]}</div>'
                            f'<div style="font-size:0.75rem;color:{COLORS["text_muted"]};margin-top:2px">'
                            f'{h["quantity"]:,.3f} qty &middot; Buy: {fmt_inr_full(h["buy_price_per_unit"])}/unit'
                            f'{" &middot; CMP: " + fmt_inr_full(cp) if cp else ""}'
                            f'{" (" + vd + ")" if vd else ""}</div></div>'
                            f'<div style="text-align:right;min-width:150px">'
                            f'<div style="font-size:0.75rem;color:{COLORS["text_muted"]}">Invested: {fmt_inr(h["total_buy_price"])}</div>'
                            f'<div style="font-size:1rem;font-weight:800;color:{COLORS["text"]}">{fmt_inr(cv) if cv else "--"}</div>'
                            f'<div style="font-size:0.78rem;font-weight:600;color:{gc}">'
                            f'{gx}{fmt_inr(abs(g)) if g is not None else "--"}'
                            f'{f" ({gp:+.1f}%)" if gp is not None else ""}</div></div></div>',
                            unsafe_allow_html=True,
                        )

                    # India trend chart
                    india_trend = []
                    for h in india_holdings:
                        hist = db.get_stock_value_history(h["id"])
                        for v in hist:
                            india_trend.append({"date": v["update_date"], "stock": f"{h['name']} ({h['ticker']})", "value": v["current_value"]})
                    if india_trend:
                        section_header("Indian Stocks Trend", "&#x1f4c8;")
                        trend_df = pd.DataFrame(india_trend)
                        fig = px.line(trend_df, x="date", y="value", color="stock",
                                      labels={"date": "Date", "value": "Value (Rs.)", "stock": "Stock"},
                                      color_discrete_sequence=["#F97316", "#FB923C", "#FDBA74", "#EA580C", "#C2410C", "#9A3412"])
                        apply_chart_theme(fig, height=320)
                        fig.update_layout(height=320, legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1))
                        st.plotly_chart(fig, use_container_width=True)

                    # India sells
                    all_sells = db.get_stock_sells()
                    india_sells = [s for s in all_sells if s["market"] == "India"]
                    if india_sells:
                        section_header("Indian Sell History", "&#x1f4b8;")
                        sell_rows = ""
                        for s in india_sells:
                            sell_rows += (
                                f'<tr><td style="font-weight:500;color:{COLORS["text"]}">{s["name"]} ({s["ticker"]})</td>'
                                f'<td style="text-align:right">{s["quantity_sold"]:,.3f}</td>'
                                f'<td class="amount">{fmt_inr_full(s["sell_price_per_unit"])}</td>'
                                f'<td class="amount">{fmt_inr_full(s["total_sell_price"])}</td>'
                                f'<td style="color:{COLORS["text_muted"]};font-size:0.85rem">{s["sell_date"]}</td>'
                                f'<td style="color:{COLORS["text_muted"]};font-size:0.85rem">{s["note"] or ""}</td></tr>'
                            )
                        st.markdown(
                            f'<table class="styled-table"><thead><tr>'
                            f'<th>Stock</th><th>Qty Sold</th><th>Sell Price</th><th>Total</th><th>Date</th><th>Note</th>'
                            f'</tr></thead><tbody>{sell_rows}</tbody></table>',
                            unsafe_allow_html=True,
                        )

                    # India insights
                    in_insights = []
                    in_insights.append(f"Indian portfolio: <strong>{len(india_holdings)} stocks</strong>, invested {fmt_inr_full(in_invested)}, current value <strong>{fmt_inr_full(in_current)}</strong>.")
                    in_gc = COLORS["success"] if in_gain >= 0 else COLORS["danger"]
                    in_insights.append(f"Return: <strong style='color:{in_gc}'>{'+'if in_gain>=0 else ''}{fmt_inr_full(in_gain)} ({in_gain_pct:+.1f}%)</strong>.")
                    in_returns = []
                    for h in india_holdings:
                        lv = db.get_latest_stock_value(h["id"])
                        if lv:
                            ret = (lv["current_value"] - h["total_buy_price"]) / h["total_buy_price"] * 100 if h["total_buy_price"] > 0 else 0
                            in_returns.append((h["name"], ret))
                    if len(in_returns) > 1:
                        best = max(in_returns, key=lambda x: x[1])
                        worst = min(in_returns, key=lambda x: x[1])
                        in_insights.append(f"Best: <strong>{best[0]}</strong> ({best[1]:+.1f}%). Worst: <strong>{worst[0]}</strong> ({worst[1]:+.1f}%).")
                    # Exchange breakdown
                    exchanges = {}
                    for h in india_holdings:
                        ex = h["exchange"] or "Unknown"
                        exchanges[ex] = exchanges.get(ex, 0) + 1
                    if len(exchanges) > 1:
                        ex_str = ", ".join(f"{k}: {v}" for k, v in exchanges.items())
                        in_insights.append(f"Exchange split: {ex_str}.")
                    insight_box(in_insights, "Indian Market Insights")
                else:
                    st.markdown(
                        f'<div style="text-align:center;padding:50px 20px;background:{COLORS["card"]};border-radius:14px;'
                        f'border:1px dashed {COLORS["card_border"]};margin:12px 0">'
                        f'<div style="font-size:2.5rem;margin-bottom:10px">&#x1f1ee;&#x1f1f3;</div>'
                        f'<div style="font-size:1rem;font-weight:600;color:{COLORS["text"]}">No Indian stocks yet</div>'
                        f'<div style="font-size:0.85rem;color:{COLORS["text_muted"]}">Add holdings via the Add Holding tab.</div></div>',
                        unsafe_allow_html=True,
                    )

            # ===== US TAB =====
            with mkt_tab_us:
                if us_holdings:
                    # US metrics in USD
                    us_invested_usd = sum(h["total_buy_price"] for h in us_holdings)
                    us_current_usd = 0
                    for h in us_holdings:
                        lv = db.get_latest_stock_value(h["id"])
                        us_current_usd += lv["current_value"] if lv else h["total_buy_price"]
                    us_gain_usd = us_current_usd - us_invested_usd
                    us_gain_pct = (us_gain_usd / us_invested_usd * 100) if us_invested_usd > 0 else 0
                    us_g_style = "green" if us_gain_usd >= 0 else "amber"

                    # INR equivalents
                    us_invested_inr_val = us_invested_usd * usd_inr if usd_inr else 0
                    us_current_inr_val = us_current_usd * usd_inr if usd_inr else 0

                    us_gain_inr = us_current_inr_val - us_invested_inr_val if usd_inr else 0
                    metric_row(
                        ("Holdings", str(len(us_holdings)), "US market", "blue", "&#x1f4bc;"),
                        ("Invested", f"$ {us_invested_usd:,.2f}", fmt_inr_full(us_invested_inr_val) if usd_inr else "Set USD/INR rate", "blue", "&#x1f4b5;"),
                        ("Current Value", f"$ {us_current_usd:,.2f}", fmt_inr_full(us_current_inr_val) if usd_inr else "", "green" if us_current_usd >= us_invested_usd else "amber", "&#x1f4b0;"),
                        ("Gain/Loss", f"{'+'if us_gain_usd>=0 else ''}$ {us_gain_usd:,.2f}", f"{us_gain_pct:+.1f}% | {'+'if us_gain_inr>=0 else ''}{fmt_inr_full(us_gain_inr)}" if usd_inr else f"{us_gain_pct:+.1f}%", us_g_style, "&#x1f4c8;"),
                    )

                    if usd_inr:
                        st.markdown(
                            f'<div style="background:{COLORS["surface2"]};border-radius:10px;padding:8px 16px;margin-bottom:12px;'
                            f'display:inline-flex;align-items:center;gap:8px">'
                            f'<span style="font-size:0.78rem;color:{COLORS["text_muted"]}">USD/INR:</span>'
                            f'<span style="font-size:0.88rem;font-weight:700;color:{COLORS["primary"]}">Rs. {usd_inr:,.2f}</span>'
                            f'<span style="font-size:0.78rem;color:{COLORS["text_muted"]}">&middot; INR Value: <strong>{fmt_inr(us_current_inr_val)}</strong></span></div>',
                            unsafe_allow_html=True,
                        )

                    # Holdings cards
                    st.markdown("<div style='height:8px'></div>", unsafe_allow_html=True)
                    for h in us_holdings:
                        lv = db.get_latest_stock_value(h["id"])
                        cp = lv["current_price"] if lv else None
                        cv = lv["current_value"] if lv else None
                        vd = lv["update_date"] if lv else None
                        g = cv - h["total_buy_price"] if cv else None
                        gp = (g / h["total_buy_price"] * 100) if g is not None and h["total_buy_price"] > 0 else None
                        gc = COLORS["success"] if (g is not None and g >= 0) else COLORS["danger"]
                        gx = "+" if (g is not None and g >= 0) else ""
                        inr_val = cv * usd_inr if cv and usd_inr else None

                        cmp_str = f" &middot; CMP: $ {cp:,.2f}" if cp else ""
                        vd_str = f" ({vd})" if vd else ""
                        val_str = f"$ {cv:,.2f}" if cv else "--"
                        inr_str = f'<span style="font-size:0.75rem;color:{COLORS["text_muted"]};margin-left:6px">({fmt_inr(inr_val)})</span>' if inr_val else ""
                        gain_str = f'<div style="font-size:0.78rem;font-weight:600;color:{gc}">{gx}$ {abs(g):,.2f}{f" ({gp:+.1f}%)" if gp is not None else ""}</div>' if g is not None else ""

                        st.markdown(
                            f'<div style="display:flex;align-items:center;gap:14px;padding:12px 16px;margin-bottom:6px;'
                            f'background:{COLORS["card"]};border:1px solid {COLORS["card_border"]};border-radius:12px;'
                            f'box-shadow:{COLORS["card_shadow"]};border-left:3px solid #3B82F6">'
                            f'<div style="min-width:56px;text-align:center">'
                            f'<span style="background:#EFF6FF;padding:3px 10px;border-radius:10px;'
                            f'font-size:0.78rem;font-weight:700;color:#1D4ED8">{h["ticker"]}</span>'
                            f'<div style="font-size:0.65rem;color:{COLORS["text_muted"]};margin-top:3px">{h["exchange"]}</div></div>'
                            f'<div style="flex:1;min-width:0">'
                            f'<div style="font-size:0.92rem;font-weight:700;color:{COLORS["text"]}">{h["name"]}</div>'
                            f'<div style="font-size:0.75rem;color:{COLORS["text_muted"]};margin-top:2px">'
                            f'{h["quantity"]:,.3f} qty &middot; Buy: $ {h["buy_price_per_unit"]:,.2f}/unit'
                            f'{cmp_str}{vd_str}</div></div>'
                            f'<div style="text-align:right;min-width:160px">'
                            f'<div style="font-size:0.75rem;color:{COLORS["text_muted"]}">Invested: $ {h["total_buy_price"]:,.2f}</div>'
                            f'<div style="font-size:1rem;font-weight:800;color:{COLORS["text"]}">{val_str}{inr_str}</div>'
                            f'{gain_str}</div></div>',
                            unsafe_allow_html=True,
                        )

                    # US trend chart
                    us_trend = []
                    for h in us_holdings:
                        hist = db.get_stock_value_history(h["id"])
                        for v in hist:
                            us_trend.append({"date": v["update_date"], "stock": f"{h['name']} ({h['ticker']})", "value": v["current_value"]})
                    if us_trend:
                        section_header("US Stocks Trend", "&#x1f4c8;")
                        trend_df = pd.DataFrame(us_trend)
                        fig = px.line(trend_df, x="date", y="value", color="stock",
                                      labels={"date": "Date", "value": "Value (USD)", "stock": "Stock"},
                                      color_discrete_sequence=["#3B82F6", "#60A5FA", "#93C5FD", "#1D4ED8", "#2563EB", "#1E40AF"])
                        apply_chart_theme(fig, height=320)
                        fig.update_layout(height=320, legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1))
                        st.plotly_chart(fig, use_container_width=True)

                    # US sells
                    all_sells = db.get_stock_sells()
                    us_sells = [s for s in all_sells if s["market"] == "US"]
                    if us_sells:
                        section_header("US Sell History", "&#x1f4b8;")
                        sell_rows = ""
                        for s in us_sells:
                            inr_total = s["total_sell_price"] * usd_inr if usd_inr else None
                            sell_rows += (
                                f'<tr><td style="font-weight:500;color:{COLORS["text"]}">{s["name"]} ({s["ticker"]})</td>'
                                f'<td style="text-align:right">{s["quantity_sold"]:,.3f}</td>'
                                f'<td class="amount">$ {s["sell_price_per_unit"]:,.2f}</td>'
                                f'<td class="amount">$ {s["total_sell_price"]:,.2f}</td>'
                                f'<td class="amount">{fmt_inr(inr_total) if inr_total else "--"}</td>'
                                f'<td style="color:{COLORS["text_muted"]};font-size:0.85rem">{s["sell_date"]}</td></tr>'
                            )
                        st.markdown(
                            f'<table class="styled-table"><thead><tr>'
                            f'<th>Stock</th><th>Qty Sold</th><th>Sell Price</th><th>Total (USD)</th><th>Total (INR)</th><th>Date</th>'
                            f'</tr></thead><tbody>{sell_rows}</tbody></table>',
                            unsafe_allow_html=True,
                        )

                    # US insights
                    us_insights = []
                    us_insights.append(f"US portfolio: <strong>{len(us_holdings)} stocks</strong>, invested $ {us_invested_usd:,.2f}, current value <strong>$ {us_current_usd:,.2f}</strong>.")
                    us_gc = COLORS["success"] if us_gain_usd >= 0 else COLORS["danger"]
                    us_insights.append(f"Return: <strong style='color:{us_gc}'>{'+'if us_gain_usd>=0 else ''}$ {us_gain_usd:,.2f} ({us_gain_pct:+.1f}%)</strong>.")
                    if usd_inr:
                        us_insights.append(f"INR equivalent: invested {fmt_inr(us_invested_inr_val)}, current <strong>{fmt_inr(us_current_inr_val)}</strong> at Rs. {usd_inr:,.2f}/USD.")
                    us_returns = []
                    for h in us_holdings:
                        lv = db.get_latest_stock_value(h["id"])
                        if lv:
                            ret = (lv["current_value"] - h["total_buy_price"]) / h["total_buy_price"] * 100 if h["total_buy_price"] > 0 else 0
                            us_returns.append((h["name"], ret))
                    if len(us_returns) > 1:
                        best = max(us_returns, key=lambda x: x[1])
                        worst = min(us_returns, key=lambda x: x[1])
                        us_insights.append(f"Best: <strong>{best[0]}</strong> ({best[1]:+.1f}%). Worst: <strong>{worst[0]}</strong> ({worst[1]:+.1f}%).")
                    insight_box(us_insights, "US Market Insights")
                else:
                    st.markdown(
                        f'<div style="text-align:center;padding:50px 20px;background:{COLORS["card"]};border-radius:14px;'
                        f'border:1px dashed {COLORS["card_border"]};margin:12px 0">'
                        f'<div style="font-size:2.5rem;margin-bottom:10px">&#x1f1fa;&#x1f1f8;</div>'
                        f'<div style="font-size:1rem;font-weight:600;color:{COLORS["text"]}">No US stocks yet</div>'
                        f'<div style="font-size:0.85rem;color:{COLORS["text_muted"]}">Add holdings via the Add Holding tab.</div></div>',
                        unsafe_allow_html=True,
                    )

        else:
            st.info("No stock holdings yet. Go to 'Add Holding' tab to get started.")

    # ---- UPDATE VALUE TAB ----
    with tab_update_val:
        section_header("Update Current Value", "&#x1f4ca;")
        if all_holdings:
            st.markdown(f"""
            <div style="background:{COLORS['surface2']};border-radius:10px;padding:12px 16px;margin-bottom:16px;border:1px solid {COLORS['card_border']};">
                <span style="color:{COLORS['text_secondary']};font-size:0.85rem">
                    Update the current market price for each stock. The current value will be auto-calculated based on quantity held.
                </span>
            </div>
            """, unsafe_allow_html=True)

            holding_labels = {}
            for h in all_holdings:
                currency_sym = "$" if h["market"] == "US" else "Rs."
                latest = db.get_latest_stock_value(h["id"])
                last_price_info = f" | Last: {currency_sym} {latest['current_price']:,.2f} on {latest['update_date']}" if latest else ""
                label = f"{h['name']} ({h['ticker']}) - {h['quantity']:,.3f} qty{last_price_info}"
                holding_labels[label] = h

            selected_holding = st.selectbox("Select Stock", list(holding_labels.keys()), key="val_update_select")
            h = holding_labels[selected_holding]
            currency_sym = "$" if h["market"] == "US" else "Rs."

            latest = db.get_latest_stock_value(h["id"])
            default_price = latest["current_price"] if latest else h["buy_price_per_unit"]

            vu_cols = st.columns([1, 1, 1])
            with vu_cols[0]:
                new_price = st.number_input(f"Current Price ({currency_sym})", value=float(default_price), min_value=0.0, step=1.0, format="%.2f", key="new_stock_price")
            with vu_cols[1]:
                val_date = st.date_input("As of Date", value=date.today(), key="stock_val_date")
            with vu_cols[2]:
                val_note = st.text_input("Note (optional)", placeholder="Market close, intraday, etc.", key="stock_val_note")

            new_val = h["quantity"] * new_price
            gain = new_val - h["total_buy_price"]
            gain_pct = (gain / h["total_buy_price"] * 100) if h["total_buy_price"] > 0 else 0

            st.markdown(f"""
            <div style="display:flex;gap:16px;margin:12px 0;">
                <div style="flex:1;background:{COLORS['surface2']};border-radius:10px;padding:12px 16px;border:1px solid {COLORS['card_border']};">
                    <span style="color:{COLORS['text_muted']};font-size:0.75rem;font-weight:600;text-transform:uppercase">Invested</span>
                    <div style="font-size:1.1rem;font-weight:700;color:{COLORS['text']}">{currency_sym} {h['total_buy_price']:,.2f}</div>
                </div>
                <div style="flex:1;background:{COLORS['surface2']};border-radius:10px;padding:12px 16px;border:1px solid {COLORS['card_border']};">
                    <span style="color:{COLORS['text_muted']};font-size:0.75rem;font-weight:600;text-transform:uppercase">New Value</span>
                    <div style="font-size:1.1rem;font-weight:700;color:{COLORS['text']}">{currency_sym} {new_val:,.2f}</div>
                </div>
                <div style="flex:1;background:{COLORS['success_light'] if gain >= 0 else COLORS['danger_light']};border-radius:10px;padding:12px 16px;border:1px solid {COLORS['card_border']};">
                    <span style="color:{COLORS['text_muted']};font-size:0.75rem;font-weight:600;text-transform:uppercase">Gain/Loss</span>
                    <div style="font-size:1.1rem;font-weight:700;color:{COLORS['success'] if gain >= 0 else COLORS['danger']}">{'+' if gain >= 0 else ''}{currency_sym} {gain:,.2f} ({gain_pct:+.1f}%)</div>
                </div>
            </div>
            """, unsafe_allow_html=True)

            if st.button("Update Value", type="primary", use_container_width=True, key="update_stock_val_btn"):
                db.add_stock_value_update(h["id"], new_price, val_date.isoformat(), val_note)
                st.success(f"Updated {h['name']}: {currency_sym} {new_price:,.2f} per unit = {currency_sym} {new_val:,.2f} total")
                st.rerun()

            # Show value history for selected stock
            val_hist = db.get_stock_value_history(h["id"])
            if val_hist:
                section_header(f"Value History: {h['name']}", "&#x1f4c8;")
                hist_rows = ""
                for v in val_hist:
                    v_gain = v["current_value"] - h["total_buy_price"]
                    v_gain_pct = (v_gain / h["total_buy_price"] * 100) if h["total_buy_price"] > 0 else 0
                    v_class = "amount-positive" if v_gain >= 0 else "amount-negative"
                    hist_rows += f"""
                    <tr>
                        <td style="color:{COLORS['text_muted']}">{v['update_date']}</td>
                        <td class="amount">{currency_sym} {v['current_price']:,.2f}</td>
                        <td class="amount">{currency_sym} {v['current_value']:,.2f}</td>
                        <td class="amount {v_class}">{'+' if v_gain >= 0 else ''}{currency_sym} {v_gain:,.2f} ({v_gain_pct:+.1f}%)</td>
                        <td style="color:{COLORS['text_muted']};font-size:0.85rem">{v['note'] or ''}</td>
                    </tr>"""
                st.markdown(f"""
                <table class="styled-table">
                    <thead><tr><th>Date</th><th>Price</th><th>Value</th><th>vs Invested</th><th>Note</th></tr></thead>
                    <tbody>{hist_rows}</tbody>
                </table>
                """, unsafe_allow_html=True)

                # Mini chart
                hist_df = pd.DataFrame([dict(v) for v in val_hist])
                fig = go.Figure()
                fig.add_trace(go.Scatter(x=hist_df["update_date"], y=hist_df["current_value"],
                    mode="lines+markers", name="Value", line=dict(color=COLORS["primary"], width=2)))
                fig.add_hline(y=h["total_buy_price"], line_dash="dash", line_color=COLORS["text_muted"],
                    annotation_text="Invested", annotation_position="top left")
                fig.update_layout(
                    plot_bgcolor=COLORS["white"], paper_bgcolor=COLORS["surface"],
                    font=dict(family="Inter", color=COLORS["text"]),
                    margin=dict(l=20, r=20, t=30, b=20), height=280, showlegend=False,
                    yaxis_title=f"Value ({currency_sym})",
                )
                fig.update_xaxes(gridcolor=COLORS["card_border"])
                fig.update_yaxes(gridcolor=COLORS["card_border"])
                st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("No stock holdings yet. Add holdings first.")

    # ---- SELL TAB ----
    with tab_sell:
        section_header("Sell Stock", "&#x1f4b8;")
        if all_holdings:
            sell_labels = {}
            for h in all_holdings:
                currency_sym = "$" if h["market"] == "US" else "Rs."
                label = f"{h['name']} ({h['ticker']}) - {h['quantity']:,.3f} qty @ {currency_sym} {h['buy_price_per_unit']:,.2f}"
                sell_labels[label] = h

            sell_selected = st.selectbox("Select Stock to Sell", list(sell_labels.keys()), key="sell_select")
            h = sell_labels[sell_selected]
            currency_sym = "$" if h["market"] == "US" else "Rs."

            st.markdown(f"""
            <div style="background:{COLORS['surface2']};border-radius:10px;padding:14px 18px;margin:12px 0;border:1px solid {COLORS['card_border']};">
                <span style="color:{COLORS['text_muted']};font-size:0.78rem;font-weight:600;text-transform:uppercase;letter-spacing:0.06em;">Holdings</span>
                <div style="font-size:1.1rem;font-weight:700;color:{COLORS['text']};margin-top:4px;">
                    {h['quantity']:,.3f} units @ {currency_sym} {h['buy_price_per_unit']:,.2f} = {currency_sym} {h['total_buy_price']:,.2f}
                </div>
            </div>
            """, unsafe_allow_html=True)

            sell_cols = st.columns([1, 1, 1, 2])
            with sell_cols[0]:
                sell_qty = st.number_input("Quantity to Sell", min_value=0.001, max_value=float(h["quantity"]),
                                            value=float(h["quantity"]), step=1.0, format="%.3f", key="sell_qty")
            with sell_cols[1]:
                sell_price = st.number_input(f"Sell Price per Unit ({currency_sym})", min_value=0.0,
                                              step=1.0, format="%.2f", key="sell_price")
            with sell_cols[2]:
                sell_date = st.date_input("Sell Date", value=date.today(), key="sell_date")
            with sell_cols[3]:
                sell_note = st.text_input("Note (optional)", placeholder="Broker, reason, etc.", key="sell_note")

            if sell_price > 0:
                total_sell = sell_qty * sell_price
                cost_basis = sell_qty * h["buy_price_per_unit"]
                profit = total_sell - cost_basis
                profit_pct = (profit / cost_basis * 100) if cost_basis > 0 else 0

                st.markdown(f"""
                <div style="display:flex;gap:16px;margin:12px 0;">
                    <div style="flex:1;background:{COLORS['surface2']};border-radius:10px;padding:12px 16px;border:1px solid {COLORS['card_border']};">
                        <span style="color:{COLORS['text_muted']};font-size:0.75rem;font-weight:600;text-transform:uppercase">Sell Amount</span>
                        <div style="font-size:1.1rem;font-weight:700;color:{COLORS['text']}">{currency_sym} {total_sell:,.2f}</div>
                    </div>
                    <div style="flex:1;background:{COLORS['surface2']};border-radius:10px;padding:12px 16px;border:1px solid {COLORS['card_border']};">
                        <span style="color:{COLORS['text_muted']};font-size:0.75rem;font-weight:600;text-transform:uppercase">Cost Basis</span>
                        <div style="font-size:1.1rem;font-weight:700;color:{COLORS['text']}">{currency_sym} {cost_basis:,.2f}</div>
                    </div>
                    <div style="flex:1;background:{COLORS['success_light'] if profit >= 0 else COLORS['danger_light']};border-radius:10px;padding:12px 16px;border:1px solid {COLORS['card_border']};">
                        <span style="color:{COLORS['text_muted']};font-size:0.75rem;font-weight:600;text-transform:uppercase">Profit/Loss</span>
                        <div style="font-size:1.1rem;font-weight:700;color:{COLORS['success'] if profit >= 0 else COLORS['danger']}">{'+' if profit >= 0 else ''}{currency_sym} {profit:,.2f} ({profit_pct:+.1f}%)</div>
                    </div>
                </div>
                """, unsafe_allow_html=True)

                remaining = h["quantity"] - sell_qty
                if remaining <= 0:
                    st.warning("This will close the entire position (sell all units).")

            if st.button("Record Sale", type="primary", use_container_width=True, key="sell_btn"):
                if sell_price > 0 and sell_qty > 0:
                    db.sell_stock(h["id"], sell_qty, sell_price, sell_date.isoformat(), sell_note)
                    st.success(f"Sold {sell_qty:,.3f} units of {h['name']} @ {currency_sym} {sell_price:,.2f}")
                    st.rerun()
                else:
                    st.error("Enter a valid sell price.")
        else:
            st.info("No stock holdings to sell.")

    # ---- ADD HOLDING TAB ----
    with tab_add:
        section_header("Add Stock Holding", "&#x2795;")
        with st.form("add_stock_holding", clear_on_submit=True):
            s_cols = st.columns([2, 1, 1, 1])
            with s_cols[0]:
                sh_name = st.text_input("Stock Name *", placeholder="e.g. Reliance Industries")
            with s_cols[1]:
                sh_ticker = st.text_input("Ticker Symbol *", placeholder="e.g. RELIANCE, AAPL")
            with s_cols[2]:
                sh_market = st.selectbox("Market", ["India", "US"])
            with s_cols[3]:
                sh_exchange = st.selectbox("Exchange", ["NSE", "BSE", "NASDAQ", "NYSE"])

            s_cols2 = st.columns([1, 1, 1, 2])
            with s_cols2[0]:
                sh_qty = st.number_input("Quantity *", min_value=0.001, step=1.0, format="%.3f")
            with s_cols2[1]:
                sh_buy_price = st.number_input("Buy Price per Unit *", min_value=0.0, step=1.0, format="%.2f")
            with s_cols2[2]:
                sh_date = st.date_input("Buy Date", value=date.today(), key="sh_buy_date")
            with s_cols2[3]:
                sh_note = st.text_input("Note (optional)", placeholder="Broker, lot info, etc.")

            if st.form_submit_button("Add Holding", type="primary", use_container_width=True):
                if sh_name and sh_ticker and sh_qty > 0 and sh_buy_price > 0:
                    db.add_stock_holding(sh_name, sh_ticker, sh_market, sh_exchange, sh_qty, sh_buy_price, sh_date.isoformat(), sh_note)
                    currency_label = "USD" if sh_market == "US" else "INR"
                    st.success(f"Added: {sh_name} ({sh_ticker}) - {sh_qty} units @ {currency_label} {sh_buy_price}")
                    st.rerun()
                else:
                    st.error("Please fill in Name, Ticker, Quantity, and Buy Price.")

    # ---- MANAGE TAB ----
    with tab_manage:
        if all_holdings:
            section_header("Edit / Remove Holdings", "&#x270f;")
            manage_labels = {}
            for h in all_holdings:
                currency_sym = "$" if h["market"] == "US" else "Rs."
                label = f"{h['name']} ({h['ticker']}) - {h['market']} - {h['quantity']:,.3f} @ {currency_sym} {h['buy_price_per_unit']:,.2f}"
                manage_labels[label] = h

            sel_manage = st.selectbox("Select holding to edit", [""] + list(manage_labels.keys()), key="manage_stock")
            if sel_manage and sel_manage in manage_labels:
                h = manage_labels[sel_manage]
                with st.form("edit_stock_holding"):
                    e_cols = st.columns([2, 1, 1, 1])
                    with e_cols[0]:
                        e_name = st.text_input("Name", value=h["name"])
                    with e_cols[1]:
                        e_ticker = st.text_input("Ticker", value=h["ticker"])
                    with e_cols[2]:
                        mkt_opts = ["India", "US"]
                        e_market = st.selectbox("Market", mkt_opts, index=mkt_opts.index(h["market"]))
                    with e_cols[3]:
                        exc_opts = ["NSE", "BSE", "NASDAQ", "NYSE"]
                        e_exc = st.selectbox("Exchange", exc_opts, index=exc_opts.index(h["exchange"]) if h["exchange"] in exc_opts else 0)
                    e_cols2 = st.columns([1, 1, 1, 2])
                    with e_cols2[0]:
                        e_qty = st.number_input("Quantity", value=float(h["quantity"]), min_value=0.001, step=1.0, format="%.3f")
                    with e_cols2[1]:
                        e_bp = st.number_input("Buy Price", value=float(h["buy_price_per_unit"]), min_value=0.0, step=1.0, format="%.2f")
                    with e_cols2[2]:
                        e_dt = st.date_input("Buy Date", value=date.fromisoformat(h["buy_date"]), key="edit_stock_date")
                    with e_cols2[3]:
                        e_note = st.text_input("Note", value=h["note"] or "")
                    btn_cols = st.columns(2)
                    with btn_cols[0]:
                        if st.form_submit_button("Update", type="primary", use_container_width=True):
                            db.update_stock_holding(h["id"], e_name, e_ticker, e_market, e_exc, e_qty, e_bp, e_dt.isoformat(), e_note)
                            st.success("Updated!")
                            st.rerun()
                    with btn_cols[1]:
                        if st.form_submit_button("Remove", use_container_width=True):
                            db.deactivate_stock_holding(h["id"])
                            st.warning("Removed.")
                            st.rerun()
        else:
            st.info("No holdings to manage.")

# ======================== SIP TRACKER ========================
elif page == "SIP & MF Portfolio":
    page_title("SIP & MF Portfolio", "Track your SIPs and mutual fund investments across all platforms")

    from dateutil.relativedelta import relativedelta

    sips = db.get_sips()

    plat_colors = {"Groww": "#00D09C", "ET Money": "#2563EB", "K-Invest": "#7C3AED",
                   "Zerodha (Coin)": "#387ED1", "Kuvera": "#F97316", "MF Central": "#059669",
                   "Direct AMC": "#6366F1", "Other": "#6B7280", "Unknown": "#9CA3AF"}

    # --- Tabs ---
    sip_tab_overview, sip_tab_update, sip_tab_add, sip_tab_manage = st.tabs(
        ["\u2001\U0001f4ca\u2002Overview", "\u2001\U0001f4c8\u2002Update Values", "\u2001\u2795\u2002Add Fund", "\u2001\u2699\ufe0f\u2002Manage"])

    # ========== ADD FUND TAB ==========
    with sip_tab_add:
        st.markdown(
            f'<div style="background:linear-gradient(135deg,#EEF2FF,#E0E7FF,#C7D2FE);border:1px solid {COLORS["accent"]}25;'
            f'border-radius:16px;padding:22px 26px;margin-bottom:22px;display:flex;align-items:center;gap:16px;'
            f'box-shadow:0 4px 16px rgba(99,102,241,0.08)">'
            f'<div style="width:48px;height:48px;border-radius:14px;background:linear-gradient(135deg,{COLORS["accent"]},#818CF8);'
            f'display:flex;align-items:center;justify-content:center;flex-shrink:0;box-shadow:0 4px 12px rgba(99,102,241,0.25)">'
            f'<span style="font-size:1.4rem;filter:brightness(0) invert(1)">&#x1f4c8;</span></div>'
            f'<div>'
            f'<div style="font-size:1.05rem;font-weight:800;color:{COLORS["text"]}">Add Mutual Fund / SIP</div>'
            f'<div style="font-size:0.82rem;color:{COLORS["text_secondary"]};margin-top:2px;line-height:1.4">'
            f'Add SIPs (recurring) or lump-sum MF investments from Groww, ET Money, K-Invest or any platform.</div>'
            f'</div></div>',
            unsafe_allow_html=True,
        )

        if "sip_form_ver" not in st.session_state:
            st.session_state["sip_form_ver"] = 0
        sfv = st.session_state["sip_form_ver"]

        # Investment type toggle
        sip_type_cols = st.columns([1, 3])
        with sip_type_cols[0]:
            sip_inv_type = st.selectbox("Investment Type *", ["SIP", "Lump Sum"], key=f"sip_type_{sfv}",
                                         help="SIP = recurring investment, Lump Sum = one-time MF purchase")
        is_sip = sip_inv_type == "SIP"

        # Type indicator
        type_color = COLORS["accent"] if is_sip else "#D97706"
        type_icon = "&#x1f504;" if is_sip else "&#x1f4b0;"
        type_label = "Systematic Investment Plan — recurring monthly/quarterly investment" if is_sip else "One-time mutual fund investment — lump sum purchase"
        with sip_type_cols[1]:
            st.markdown(
                f'<div style="background:{type_color}08;border:1px solid {type_color}20;border-radius:10px;'
                f'padding:10px 16px;margin-top:26px;display:flex;align-items:center;gap:8px">'
                f'<span style="font-size:1rem">{type_icon}</span>'
                f'<span style="font-size:0.82rem;color:{type_color};font-weight:600">{type_label}</span></div>',
                unsafe_allow_html=True)

        sip_cols = st.columns([3, 2, 1])
        with sip_cols[0]:
            sip_fund = st.text_input("Fund Name *", placeholder="e.g. Mirae Asset Large Cap Fund", key=f"sip_fund_{sfv}")
        with sip_cols[1]:
            sip_platform = st.selectbox("Platform *", ["Groww", "ET Money", "K-Invest", "Zerodha (Coin)", "Kuvera", "MF Central", "Direct AMC", "Other"], key=f"sip_plat_{sfv}")
        with sip_cols[2]:
            sip_category = st.selectbox("Category", ["Equity", "Debt", "Hybrid", "ELSS", "Index", "Liquid", "Other"], key=f"sip_cat_{sfv}")

        if is_sip:
            sip_cols2 = st.columns([1, 1, 1, 1])
            with sip_cols2[0]:
                sip_amount = st.number_input("SIP Amount (Rs.) *", min_value=100.0, step=500.0, value=1000.0, format="%.2f", key=f"sip_amt_{sfv}")
            with sip_cols2[1]:
                sip_invested = st.number_input("Total Invested So Far (Rs.) *", min_value=0.0, step=1000.0, format="%.2f", key=f"sip_inv_{sfv}",
                                                help="Total amount you've put in till today")
            with sip_cols2[2]:
                sip_current = st.number_input("Current Value (Rs.) *", min_value=0.0, step=1000.0, format="%.2f", key=f"sip_cur_{sfv}",
                                               help="Current market value from your app")
            with sip_cols2[3]:
                sip_units = st.number_input("Units Held", min_value=0.0, step=0.01, format="%.4f", key=f"sip_units_{sfv}",
                                             help="Total units from your app (optional)")
        else:
            sip_cols2 = st.columns([1, 1, 1])
            with sip_cols2[0]:
                sip_amount = st.number_input("Amount Invested (Rs.) *", min_value=100.0, step=1000.0, value=10000.0, format="%.2f", key=f"sip_amt_{sfv}",
                                              help="Total lump sum amount invested")
                sip_invested = sip_amount  # For lump sum, invested = amount
            with sip_cols2[1]:
                sip_current = st.number_input("Current Value (Rs.) *", min_value=0.0, step=1000.0, format="%.2f", key=f"sip_cur_{sfv}",
                                               help="Current market value from your app")
            with sip_cols2[2]:
                sip_units = st.number_input("Units Held", min_value=0.0, step=0.01, format="%.4f", key=f"sip_units_{sfv}",
                                             help="Total units from your app (optional)")

        sip_cols3 = st.columns([1, 1, 1, 1])
        with sip_cols3[0]:
            date_label = "SIP Start Date" if is_sip else "Purchase Date"
            sip_start = st.date_input(date_label, value=date.today() - relativedelta(months=12) if is_sip else date.today(),
                                       key=f"sip_start_{sfv}")
        with sip_cols3[1]:
            if is_sip:
                sip_freq = st.selectbox("Frequency", ["Monthly", "Weekly", "Quarterly", "Annually"], key=f"sip_freq_{sfv}")
            else:
                sip_freq = "One-time"
                st.markdown(
                    f'<div style="background:{COLORS["surface2"]};border-radius:10px;padding:10px 14px;margin-top:26px">'
                    f'<span style="font-size:0.82rem;font-weight:600;color:{COLORS["text_secondary"]}">Frequency: One-time</span></div>',
                    unsafe_allow_html=True)
        with sip_cols3[2]:
            sip_folio = st.text_input("Folio Number", placeholder="Optional", key=f"sip_folio_{sfv}")
        with sip_cols3[3]:
            sip_note = st.text_input("Note / Goal", placeholder="e.g. Retirement, Child edu", key=f"sip_note_{sfv}")

        # Live preview
        if sip_invested > 0 and sip_current > 0:
            prev_gain = sip_current - sip_invested
            prev_pct = (prev_gain / sip_invested * 100)
            prev_gc = COLORS["success"] if prev_gain >= 0 else COLORS["danger"]
            if is_sip and sip_amount > 0:
                months_est = max(1, int(sip_invested / sip_amount))
                est_html = (
                    f'<div style="margin-left:auto"><div style="font-size:0.65rem;font-weight:600;text-transform:uppercase;'
                    f'color:{COLORS["text_muted"]}">Est. Installments</div>'
                    f'<div style="font-size:1.15rem;font-weight:800;color:{COLORS["text_secondary"]}">{months_est} months</div></div>'
                )
            else:
                est_html = ""
            st.markdown(
                f'<div style="background:linear-gradient(135deg,{COLORS["card"]},#F5F3FF);border:1px solid {COLORS["accent"]}20;'
                f'border-radius:14px;padding:18px 22px;margin:12px 0;border-left:4px solid {type_color}">'
                f'<div style="font-size:0.65rem;font-weight:700;text-transform:uppercase;letter-spacing:0.08em;'
                f'color:{type_color};margin-bottom:10px">{sip_inv_type} Preview</div>'
                f'<div style="display:flex;gap:28px;flex-wrap:wrap;align-items:center">'
                f'<div><div style="font-size:0.65rem;font-weight:600;text-transform:uppercase;color:{COLORS["text_muted"]}">Invested</div>'
                f'<div style="font-size:1.15rem;font-weight:800;color:{COLORS["text"]}">{fmt_inr_full(sip_invested)}</div></div>'
                f'<div style="font-size:1.2rem;color:{COLORS["text_muted"]}">\u2192</div>'
                f'<div><div style="font-size:0.65rem;font-weight:600;text-transform:uppercase;color:{COLORS["text_muted"]}">Current Value</div>'
                f'<div style="font-size:1.15rem;font-weight:800;color:{COLORS["text"]}">{fmt_inr_full(sip_current)}</div></div>'
                f'<div><div style="font-size:0.65rem;font-weight:600;text-transform:uppercase;color:{COLORS["text_muted"]}">Returns</div>'
                f'<div style="font-size:1.15rem;font-weight:800;color:{prev_gc}">{"+" if prev_gain>=0 else ""}{fmt_inr_full(prev_gain)} ({prev_pct:+.1f}%)</div></div>'
                f'{est_html}'
                f'</div></div>',
                unsafe_allow_html=True,
            )

        if st.session_state.get("sip_added_msg"):
            st.success(st.session_state.pop("sip_added_msg"))

        btn_label = "Add SIP" if is_sip else "Add Mutual Fund"
        if st.button(btn_label, type="primary", use_container_width=True, key="sip_add_btn"):
            if sip_fund and sip_amount > 0:
                installments_est = max(0, int(sip_invested / sip_amount)) if sip_amount > 0 and is_sip else (1 if not is_sip else 0)
                end_est = sip_start + relativedelta(months=60) if is_sip else sip_start
                db.add_sip(sip_fund, sip_platform, sip_folio, sip_amount, sip_freq, sip_start.day,
                           sip_start.isoformat(), end_est.isoformat(), sip_category, sip_note,
                           installments_paid=installments_est, total_invested=sip_invested,
                           current_value=sip_current if sip_current > 0 else sip_invested, units_held=sip_units,
                           investment_type=sip_inv_type)
                # Record initial value snapshot
                new_sips = db.get_sips()
                if new_sips:
                    latest_sip = max(new_sips, key=lambda x: x["id"])
                    db.add_sip_value_update(latest_sip["id"], sip_current if sip_current > 0 else sip_invested,
                                            sip_invested, note="Initial entry")
                st.session_state["sip_added_msg"] = f"Added {sip_inv_type}: {sip_fund} on {sip_platform} \u2014 {fmt_inr_full(sip_invested)} invested, {fmt_inr_full(sip_current)} current"
                st.session_state["sip_form_ver"] = sfv + 1
                st.rerun()
            else:
                st.error("Please fill in Fund Name and Amount.")

    # ========== OVERVIEW TAB ==========
    with sip_tab_overview:
        if sips:
            # Helper for sqlite3.Row (no .get() support)
            def _row_get(row, key, default=None):
                try:
                    return row[key]
                except (IndexError, KeyError):
                    return default

            # Separate SIPs and Lump Sum MFs
            sip_list = [s for s in sips if _row_get(s, "investment_type", "SIP") == "SIP"]
            mf_list = [s for s in sips if _row_get(s, "investment_type", "SIP") == "Lump Sum"]

            total_invested = sum(s["total_invested"] for s in sips)
            total_current = sum(s["current_value"] for s in sips)
            total_gain = total_current - total_invested
            gain_pct = (total_gain / total_invested * 100) if total_invested > 0 else 0
            active_count = sum(1 for s in sips if s["status"] == "Active")
            total_monthly = sum(s["sip_amount"] for s in sip_list if s["status"] == "Active")

            sip_invested = sum(s["total_invested"] for s in sip_list)
            sip_current = sum(s["current_value"] for s in sip_list)
            sip_gain = sip_current - sip_invested
            mf_invested = sum(s["total_invested"] for s in mf_list)
            mf_current = sum(s["current_value"] for s in mf_list)
            mf_gain = mf_current - mf_invested

            # Hero banner
            st.markdown(
                f'<div style="background:linear-gradient(135deg,#312E81,#4338CA,#6366F1);border-radius:18px;'
                f'padding:28px 30px;margin-bottom:22px;color:white;position:relative;overflow:hidden;'
                f'box-shadow:0 8px 32px rgba(99,102,241,0.2)">'
                f'<div style="position:absolute;top:-30px;right:-30px;width:120px;height:120px;border-radius:50%;'
                f'background:rgba(255,255,255,0.06)"></div>'
                f'<div style="position:absolute;bottom:-20px;right:60px;width:80px;height:80px;border-radius:50%;'
                f'background:rgba(255,255,255,0.04)"></div>'
                f'<div style="font-size:0.68rem;font-weight:600;text-transform:uppercase;letter-spacing:0.1em;'
                f'color:rgba(255,255,255,0.6);margin-bottom:6px">SIP &amp; Mutual Fund Portfolio</div>'
                f'<div style="display:flex;align-items:flex-end;gap:16px;flex-wrap:wrap">'
                f'<div style="font-size:2rem;font-weight:800;letter-spacing:-0.02em">{fmt_inr_full(total_current)}</div>'
                f'<div style="padding-bottom:4px">'
                f'<span style="background:{"rgba(52,211,153,0.2)" if total_gain>=0 else "rgba(251,113,133,0.2)"};'
                f'padding:4px 12px;border-radius:20px;font-size:0.82rem;font-weight:700;'
                f'color:{"#6EE7B7" if total_gain>=0 else "#FCA5A5"}">'
                f'{"+" if total_gain>=0 else ""}{fmt_inr(total_gain)} ({gain_pct:+.1f}%)</span></div></div>'
                f'<div style="display:flex;gap:28px;margin-top:18px;flex-wrap:wrap">'
                f'<div><div style="font-size:0.6rem;font-weight:600;text-transform:uppercase;letter-spacing:0.08em;'
                f'color:rgba(255,255,255,0.5)">Active Funds</div>'
                f'<div style="font-size:1.15rem;font-weight:700;margin-top:2px">{active_count}<span style="font-size:0.75rem;'
                f'font-weight:400;color:rgba(255,255,255,0.5);margin-left:4px">of {len(sips)}</span></div></div>'
                f'<div><div style="font-size:0.6rem;font-weight:600;text-transform:uppercase;letter-spacing:0.08em;'
                f'color:rgba(255,255,255,0.5)">Monthly SIP</div>'
                f'<div style="font-size:1.15rem;font-weight:700;margin-top:2px">{fmt_inr_full(total_monthly)}</div></div>'
                f'<div><div style="font-size:0.6rem;font-weight:600;text-transform:uppercase;letter-spacing:0.08em;'
                f'color:rgba(255,255,255,0.5)">Total Invested</div>'
                f'<div style="font-size:1.15rem;font-weight:700;margin-top:2px">{fmt_inr_full(total_invested)}</div></div>'
                f'<div><div style="font-size:0.6rem;font-weight:600;text-transform:uppercase;letter-spacing:0.08em;'
                f'color:rgba(255,255,255,0.5)">Annual SIP Outflow</div>'
                f'<div style="font-size:1.15rem;font-weight:700;margin-top:2px">{fmt_inr(total_monthly * 12)}</div></div>'
                f'</div></div>',
                unsafe_allow_html=True,
            )

            # --- SIP vs Lump Sum Split Cards ---
            if sip_list or mf_list:
                section_header("SIP vs Lump Sum Breakdown", "&#x1f4ca;")
                split_cols = st.columns(2)
                with split_cols[0]:
                    sip_g_pct = (sip_gain / sip_invested * 100) if sip_invested > 0 else 0
                    sip_g_clr = COLORS["success"] if sip_gain >= 0 else COLORS["danger"]
                    st.markdown(
                        f'<div style="background:{COLORS["card"]};border:1px solid {COLORS["card_border"]};border-radius:14px;'
                        f'padding:20px;box-shadow:{COLORS["card_shadow"]};border-top:4px solid {COLORS["accent"]}">'
                        f'<div style="display:flex;align-items:center;gap:8px;margin-bottom:12px">'
                        f'<div style="width:34px;height:34px;border-radius:10px;background:linear-gradient(135deg,{COLORS["accent"]},#818CF8);'
                        f'display:flex;align-items:center;justify-content:center">'
                        f'<span style="font-size:1rem;filter:brightness(10)">&#x1f504;</span></div>'
                        f'<div>'
                        f'<div style="font-size:0.88rem;font-weight:700;color:{COLORS["text"]}">SIP Investments</div>'
                        f'<div style="font-size:0.68rem;color:{COLORS["text_muted"]}">{len(sip_list)} fund{"s" if len(sip_list) != 1 else ""} &middot; Recurring</div>'
                        f'</div></div>'
                        f'<div style="display:flex;gap:20px;flex-wrap:wrap;margin-bottom:8px">'
                        f'<div><div style="font-size:0.62rem;font-weight:600;text-transform:uppercase;color:{COLORS["text_muted"]}">Invested</div>'
                        f'<div style="font-size:1.1rem;font-weight:800;color:{COLORS["text"]}">{fmt_inr(sip_invested)}</div></div>'
                        f'<div><div style="font-size:0.62rem;font-weight:600;text-transform:uppercase;color:{COLORS["text_muted"]}">Current</div>'
                        f'<div style="font-size:1.1rem;font-weight:800;color:{COLORS["text"]}">{fmt_inr(sip_current)}</div></div>'
                        f'<div><div style="font-size:0.62rem;font-weight:600;text-transform:uppercase;color:{COLORS["text_muted"]}">Returns</div>'
                        f'<div style="font-size:1.1rem;font-weight:800;color:{sip_g_clr}">{"+" if sip_gain >= 0 else ""}{fmt_inr(sip_gain)}'
                        f' ({sip_g_pct:+.1f}%)</div></div></div>'
                        f'<div style="font-size:0.72rem;color:{COLORS["text_muted"]}">Monthly outflow: {fmt_inr_full(total_monthly)}</div>'
                        f'</div>',
                        unsafe_allow_html=True)
                with split_cols[1]:
                    mf_g_pct = (mf_gain / mf_invested * 100) if mf_invested > 0 else 0
                    mf_g_clr = COLORS["success"] if mf_gain >= 0 else COLORS["danger"]
                    st.markdown(
                        f'<div style="background:{COLORS["card"]};border:1px solid {COLORS["card_border"]};border-radius:14px;'
                        f'padding:20px;box-shadow:{COLORS["card_shadow"]};border-top:4px solid #D97706">'
                        f'<div style="display:flex;align-items:center;gap:8px;margin-bottom:12px">'
                        f'<div style="width:34px;height:34px;border-radius:10px;background:linear-gradient(135deg,#D97706,#F59E0B);'
                        f'display:flex;align-items:center;justify-content:center">'
                        f'<span style="font-size:1rem;filter:brightness(10)">&#x1f4b0;</span></div>'
                        f'<div>'
                        f'<div style="font-size:0.88rem;font-weight:700;color:{COLORS["text"]}">Lump Sum MF</div>'
                        f'<div style="font-size:0.68rem;color:{COLORS["text_muted"]}">{len(mf_list)} fund{"s" if len(mf_list) != 1 else ""} &middot; One-time</div>'
                        f'</div></div>'
                        f'<div style="display:flex;gap:20px;flex-wrap:wrap;margin-bottom:8px">'
                        f'<div><div style="font-size:0.62rem;font-weight:600;text-transform:uppercase;color:{COLORS["text_muted"]}">Invested</div>'
                        f'<div style="font-size:1.1rem;font-weight:800;color:{COLORS["text"]}">{fmt_inr(mf_invested)}</div></div>'
                        f'<div><div style="font-size:0.62rem;font-weight:600;text-transform:uppercase;color:{COLORS["text_muted"]}">Current</div>'
                        f'<div style="font-size:1.1rem;font-weight:800;color:{COLORS["text"]}">{fmt_inr(mf_current)}</div></div>'
                        f'<div><div style="font-size:0.62rem;font-weight:600;text-transform:uppercase;color:{COLORS["text_muted"]}">Returns</div>'
                        f'<div style="font-size:1.1rem;font-weight:800;color:{mf_g_clr}">{"+" if mf_gain >= 0 else ""}{fmt_inr(mf_gain)}'
                        f' ({mf_g_pct:+.1f}%)</div></div></div>'
                        + (f'<div style="font-size:0.72rem;color:{COLORS["text_muted"]}">No recurring outflow — one-time investments</div>'
                           if mf_list else f'<div style="font-size:0.72rem;color:{COLORS["text_muted"]}">No lump sum investments yet</div>')
                        + f'</div>',
                        unsafe_allow_html=True)

            # --- Platform Breakdown ---
            plat_data = {}
            for s in sips:
                p = s["amc"] or "Unknown"
                if p not in plat_data:
                    plat_data[p] = {"invested": 0, "current": 0, "count": 0, "monthly": 0}
                plat_data[p]["invested"] += s["total_invested"]
                plat_data[p]["current"] += s["current_value"]
                plat_data[p]["count"] += 1
                if s["status"] == "Active":
                    plat_data[p]["monthly"] += s["sip_amount"]

            if len(plat_data) > 0:
                section_header("By Platform", "&#x1f4f1;")
                p_cols = st.columns(min(len(plat_data), 4))
                for i, (plat, data) in enumerate(plat_data.items()):
                    g = data["current"] - data["invested"]
                    gp = (g / data["invested"] * 100) if data["invested"] > 0 else 0
                    pc = plat_colors.get(plat, "#6B7280")
                    with p_cols[i % len(p_cols)]:
                        st.markdown(
                            f'<div style="background:{COLORS["card"]};border:1px solid {COLORS["card_border"]};border-radius:12px;'
                            f'padding:14px 16px;box-shadow:{COLORS["card_shadow"]};border-left:4px solid {pc};margin-bottom:8px">'
                            f'<div style="font-size:0.82rem;font-weight:700;color:{COLORS["text"]}">{plat}</div>'
                            f'<div style="font-size:1.1rem;font-weight:800;color:{COLORS["text"]};margin:4px 0">{fmt_inr(data["current"])}</div>'
                            f'<div style="font-size:0.72rem;color:{COLORS["text_muted"]}">{data["count"]} fund{"s" if data["count"]!=1 else ""}'
                            f' &middot; Invested: {fmt_inr(data["invested"])}</div>'
                            f'<div style="font-size:0.78rem;font-weight:600;color:{COLORS["success"] if g>=0 else COLORS["danger"]};margin-top:4px">'
                            f'{"+" if g>=0 else ""}{fmt_inr(g)} ({gp:+.1f}%)</div></div>',
                            unsafe_allow_html=True,
                        )

            # --- Category Breakdown ---
            cat_data = {}
            for s in sips:
                cat = s["category"] or "Other"
                if cat not in cat_data:
                    cat_data[cat] = {"invested": 0, "current": 0, "count": 0, "monthly": 0}
                cat_data[cat]["invested"] += s["total_invested"]
                cat_data[cat]["current"] += s["current_value"]
                cat_data[cat]["count"] += 1
                if s["status"] == "Active":
                    cat_data[cat]["monthly"] += s["sip_amount"]

            cat_colors = {"Equity": "#6366F1", "Debt": "#10B981", "Hybrid": "#F59E0B",
                          "ELSS": "#8B5CF6", "Index": "#3B82F6", "Liquid": "#06B6D4", "Other": "#6B7280"}

            if len(cat_data) > 1:
                section_header("By Category", "&#x1f4ca;")
                import plotly.graph_objects as go
                cat_chart_cols = st.columns([1, 1])
                with cat_chart_cols[0]:
                    fig_cat = go.Figure(data=[go.Pie(
                        labels=list(cat_data.keys()),
                        values=[v["current"] for v in cat_data.values()],
                        hole=0.55,
                        marker=dict(colors=[cat_colors.get(c, "#6B7280") for c in cat_data.keys()]),
                        textinfo="label+percent", textfont_size=11,
                    )])
                    apply_chart_theme(fig_cat, height=280)
                    fig_cat.update_layout(showlegend=False, title_text="Current Value", title_x=0.5,
                                          title_font=dict(size=12, color=COLORS["text_muted"]))
                    st.plotly_chart(fig_cat, use_container_width=True)
                with cat_chart_cols[1]:
                    fig_inv = go.Figure(data=[go.Pie(
                        labels=list(cat_data.keys()),
                        values=[v["invested"] for v in cat_data.values()],
                        hole=0.55,
                        marker=dict(colors=[cat_colors.get(c, "#6B7280") for c in cat_data.keys()]),
                        textinfo="label+percent", textfont_size=11,
                    )])
                    apply_chart_theme(fig_inv, height=280)
                    fig_inv.update_layout(showlegend=False, title_text="Invested", title_x=0.5,
                                          title_font=dict(size=12, color=COLORS["text_muted"]))
                    st.plotly_chart(fig_inv, use_container_width=True)

                c_cols = st.columns(min(len(cat_data), 4))
                for i, (cat, data) in enumerate(cat_data.items()):
                    g = data["current"] - data["invested"]
                    gp = (g / data["invested"] * 100) if data["invested"] > 0 else 0
                    color = cat_colors.get(cat, "#6B7280")
                    with c_cols[i % len(c_cols)]:
                        st.markdown(
                            f'<div style="background:{COLORS["card"]};border:1px solid {COLORS["card_border"]};border-radius:12px;'
                            f'padding:14px 16px;box-shadow:{COLORS["card_shadow"]};border-top:3px solid {color};margin-bottom:8px">'
                            f'<div style="font-size:0.72rem;font-weight:700;text-transform:uppercase;letter-spacing:0.06em;color:{color}">{cat}</div>'
                            f'<div style="font-size:1.05rem;font-weight:800;color:{COLORS["text"]};margin:4px 0">{fmt_inr(data["current"])}</div>'
                            f'<div style="font-size:0.72rem;color:{COLORS["text_muted"]}">{data["count"]} fund{"s" if data["count"]!=1 else ""}'
                            f' &middot; {fmt_inr(data["monthly"])}/mo</div>'
                            f'<div style="font-size:0.78rem;font-weight:600;color:{COLORS["success"] if g>=0 else COLORS["danger"]};margin-top:4px">'
                            f'{"+" if g>=0 else ""}{fmt_inr(g)} ({gp:+.1f}%)</div></div>',
                            unsafe_allow_html=True,
                        )

            # --- Value Trend Chart ---
            all_val_hist = db.get_all_sip_value_history()
            if all_val_hist:
                section_header("Portfolio Value Trend", "&#x1f4c8;")
                trend_data = [{"date": v["update_date"], "fund": v["fund_name"], "value": v["current_value"]} for v in all_val_hist]
                trend_df = pd.DataFrame(trend_data)
                fig_trend = px.line(trend_df, x="date", y="value", color="fund",
                                    labels={"date": "Date", "value": "Value (Rs.)", "fund": "Fund"},
                                    color_discrete_sequence=CHART_COLORS)
                apply_chart_theme(fig_trend, height=350)
                fig_trend.update_layout(legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1))
                st.plotly_chart(fig_trend, use_container_width=True)

            # --- Individual Fund Cards ---
            st.markdown("<div style='height:12px'></div>", unsafe_allow_html=True)
            section_header("Your Funds", "&#x1f4cb;")

            for s in sips:
                s_invested = s["total_invested"]
                s_current = s["current_value"]
                s_gain = s_current - s_invested
                s_gain_pct = (s_gain / s_invested * 100) if s_invested > 0 else 0
                gain_color = COLORS["success"] if s_gain >= 0 else COLORS["danger"]
                status_colors = {"Active": COLORS["success"], "Paused": COLORS["warning"], "Completed": COLORS["accent"], "Stopped": COLORS["text_muted"]}
                s_color = status_colors.get(s["status"], COLORS["text_muted"])
                cat_color = cat_colors.get(s["category"], "#6B7280")
                p_color = plat_colors.get(s["amc"] or "", "#6B7280")
                units_str = f" &middot; {s['units_held']:.2f} units" if s["units_held"] > 0 else ""
                folio_str = f" &middot; {s['folio_number']}" if s["folio_number"] else ""
                inv_type = _row_get(s, "investment_type", "SIP")
                type_clr = COLORS["accent"] if inv_type == "SIP" else "#D97706"
                # Detail line
                if inv_type == "Lump Sum":
                    detail_line = f'Lump sum &middot; Purchased {s["start_date"][:10] if s["start_date"] else "N/A"}{units_str}{folio_str}'
                else:
                    freq_txt = s["frequency"].lower() if s["frequency"] else "month"
                    detail_line = f'{fmt_inr_full(s["sip_amount"])}/{freq_txt} &middot; Since {s["start_date"][:7] if s["start_date"] else "N/A"}{units_str}{folio_str}'

                st.markdown(
                    f'<div style="background:{COLORS["card"]};border:1px solid {COLORS["card_border"]};border-radius:14px;'
                    f'padding:16px 20px;margin-bottom:10px;box-shadow:{COLORS["card_shadow"]};border-left:4px solid {cat_color}">'
                    f'<div style="display:flex;align-items:flex-start;gap:14px;flex-wrap:wrap">'
                    f'<div style="flex:1;min-width:200px">'
                    f'<div style="display:flex;align-items:center;gap:6px;margin-bottom:6px;flex-wrap:wrap">'
                    f'<span style="background:{type_clr}15;color:{type_clr};padding:2px 10px;border-radius:8px;'
                    f'font-size:0.68rem;font-weight:700">{inv_type}</span>'
                    f'<span style="background:{p_color}15;color:{p_color};padding:2px 10px;border-radius:8px;'
                    f'font-size:0.68rem;font-weight:700">{s["amc"] or "Unknown"}</span>'
                    f'<span style="background:{cat_color}15;color:{cat_color};padding:2px 8px;border-radius:8px;'
                    f'font-size:0.65rem;font-weight:600">{s["category"]}</span>'
                    f'<span style="background:{s_color}15;color:{s_color};padding:2px 8px;border-radius:8px;'
                    f'font-size:0.62rem;font-weight:600">{s["status"]}</span></div>'
                    f'<div style="font-size:0.95rem;font-weight:700;color:{COLORS["text"]};line-height:1.3">{s["fund_name"]}</div>'
                    f'<div style="font-size:0.75rem;color:{COLORS["text_muted"]};margin-top:4px">{detail_line}</div></div>'
                    f'<div style="text-align:right;min-width:160px">'
                    f'<div style="display:flex;gap:20px;justify-content:flex-end;margin-bottom:6px">'
                    f'<div><div style="font-size:0.62rem;font-weight:600;text-transform:uppercase;color:{COLORS["text_muted"]}">Invested</div>'
                    f'<div style="font-size:0.92rem;font-weight:600;color:{COLORS["text_secondary"]}">{fmt_inr(s_invested)}</div></div>'
                    f'<div><div style="font-size:0.62rem;font-weight:600;text-transform:uppercase;color:{COLORS["text_muted"]}">Current</div>'
                    f'<div style="font-size:1.05rem;font-weight:800;color:{COLORS["text"]}">{fmt_inr(s_current)}</div></div></div>'
                    f'<div style="font-size:0.82rem;font-weight:700;color:{gain_color};'
                    f'background:{gain_color}10;padding:3px 10px;border-radius:8px;display:inline-block">'
                    f'{"+" if s_gain>=0 else ""}{fmt_inr(s_gain)} ({s_gain_pct:+.1f}%)</div>'
                    f'</div></div></div>',
                    unsafe_allow_html=True,
                )

            # --- Financial Insights ---
            insights = []
            sip_count_str = f"{len(sip_list)} SIP{'s' if len(sip_list) != 1 else ''}"
            mf_count_str = f"{len(mf_list)} lump sum MF{'s' if len(mf_list) != 1 else ''}" if mf_list else ""
            portfolio_str = f"{sip_count_str} + {mf_count_str}" if mf_list else sip_count_str
            insights.append(f"Portfolio: <strong>{portfolio_str}</strong> across {len(plat_data)} platform{'s' if len(plat_data)!=1 else ''}. Monthly SIP outflow: <strong>{fmt_inr_full(total_monthly)}</strong>.")
            insights.append(f"Total invested: <strong>{fmt_inr_full(total_invested)}</strong>, current value: <strong>{fmt_inr_full(total_current)}</strong>.")
            if total_current > 0:
                color = COLORS['success'] if total_gain >= 0 else COLORS['danger']
                insights.append(f"Overall return: <strong style='color:{color}'>{'+'if total_gain>=0 else ''}{fmt_inr_full(total_gain)} ({gain_pct:+.1f}%)</strong>.")
            if total_monthly > 0:
                annual = total_monthly * 12
                insights.append(f"Annual SIP commitment: <strong>{fmt_inr_full(annual)}</strong> ({fmt_inr_words(annual)}).")
            # Best/worst by return %
            fund_returns = [(s["fund_name"], (s["current_value"] - s["total_invested"]) / s["total_invested"] * 100 if s["total_invested"] > 0 else 0) for s in sips]
            if len(fund_returns) > 1:
                best = max(fund_returns, key=lambda x: x[1])
                worst = min(fund_returns, key=lambda x: x[1])
                insights.append(f"Best performer: <strong>{best[0]}</strong> ({best[1]:+.1f}%). Weakest: <strong>{worst[0]}</strong> ({worst[1]:+.1f}%).")
            # Platform split
            for plat, data in plat_data.items():
                pct = (data["current"] / total_current * 100) if total_current > 0 else 0
                g = data["current"] - data["invested"]
                insights.append(f"<strong>{plat}</strong>: {data['count']} fund{'s' if data['count']!=1 else ''}, {fmt_inr(data['current'])} ({pct:.0f}%), return {'+'if g>=0 else ''}{fmt_inr(g)}.")
            # Category allocation
            for cat, data in cat_data.items():
                pct = (data["current"] / total_current * 100) if total_current > 0 else 0
                insights.append(f"{cat}: {pct:.0f}% allocation ({fmt_inr(data['current'])}).")
            # Net worth context
            all_src = db.get_sources()
            nw = sum(db.get_latest_balance(src["id"]) for src in all_src)
            if nw > 0:
                sip_nw_pct = total_current / nw * 100
                insights.append(f"Mutual funds represent <strong>{sip_nw_pct:.1f}%</strong> of your total net worth.")

            insight_box(insights, "Mutual Fund Insights & Analysis")

        else:
            st.markdown(
                f'<div style="text-align:center;padding:60px 24px;background:linear-gradient(135deg,{COLORS["card"]},#EEF2FF);'
                f'border:1px dashed {COLORS["accent"]}60;border-radius:18px;margin:20px 0">'
                f'<div style="font-size:3.5rem;margin-bottom:14px">&#x1f4c8;</div>'
                f'<div style="font-size:1.2rem;font-weight:700;color:{COLORS["text"]};margin-bottom:6px">No Funds Yet</div>'
                f'<div style="font-size:0.9rem;color:{COLORS["text_muted"]};max-width:420px;margin:0 auto;line-height:1.6">'
                f'Add your mutual fund SIPs from Groww, ET Money, K-Invest or any platform via the <strong>Add Fund</strong> tab.</div></div>',
                unsafe_allow_html=True,
            )

    # ========== UPDATE VALUES TAB ==========
    with sip_tab_update:
        if sips:
            st.markdown(
                f'<div style="background:linear-gradient(135deg,#F0FDF4,#DCFCE7);border:1px solid {COLORS["success"]}25;'
                f'border-radius:14px;padding:18px 22px;margin-bottom:20px;display:flex;align-items:center;gap:14px">'
                f'<div style="font-size:1.5rem">&#x1f4f1;</div>'
                f'<div>'
                f'<div style="font-size:0.95rem;font-weight:700;color:{COLORS["text"]}">Update Current Values</div>'
                f'<div style="font-size:0.82rem;color:{COLORS["text_secondary"]}">Open your Groww/ET Money/K-Invest app and enter the latest values. This records a snapshot for trend tracking.</div>'
                f'</div></div>',
                unsafe_allow_html=True,
            )

            upd_date = st.date_input("As of Date", value=date.today(), key="sip_upd_date")

            for s in sips:
                s_gain = s["current_value"] - s["total_invested"]
                s_gain_pct = (s_gain / s["total_invested"] * 100) if s["total_invested"] > 0 else 0
                gc = COLORS["success"] if s_gain >= 0 else COLORS["danger"]
                p_color = plat_colors.get(s["amc"] or "", "#6B7280")

                st.markdown(
                    f'<div style="background:{COLORS["card"]};border:1px solid {COLORS["card_border"]};border-radius:12px;'
                    f'padding:12px 16px;margin-bottom:4px;box-shadow:{COLORS["card_shadow"]}">'
                    f'<div style="display:flex;align-items:center;gap:8px">'
                    f'<span style="background:{p_color}15;color:{p_color};padding:2px 8px;border-radius:6px;'
                    f'font-size:0.65rem;font-weight:700">{s["amc"] or "?"}</span>'
                    f'<span style="font-size:0.88rem;font-weight:700;color:{COLORS["text"]}">{s["fund_name"]}</span>'
                    f'<span style="margin-left:auto;font-size:0.78rem;color:{COLORS["text_muted"]}">Invested: {fmt_inr(s["total_invested"])}</span>'
                    f'<span style="font-size:0.78rem;font-weight:600;color:{gc}">{"+" if s_gain>=0 else ""}{s_gain_pct:.1f}%</span>'
                    f'</div></div>',
                    unsafe_allow_html=True,
                )
                upd_cols = st.columns([1, 1, 1, 3, 1])
                with upd_cols[0]:
                    new_invested = st.number_input("Invested", value=float(s["total_invested"]),
                                                    min_value=0.0, step=500.0, format="%.2f", key=f"sip_ui_{s['id']}")
                with upd_cols[1]:
                    new_val = st.number_input("Current Value", value=float(s["current_value"]),
                                               min_value=0.0, step=500.0, format="%.2f", key=f"sip_uv_{s['id']}")
                with upd_cols[2]:
                    new_units = st.number_input("Units", value=float(s["units_held"]),
                                                 min_value=0.0, step=0.01, format="%.4f", key=f"sip_uu_{s['id']}")
                with upd_cols[3]:
                    upd_note = st.text_input("Note", placeholder="Optional", key=f"sip_un_{s['id']}")
                with upd_cols[4]:
                    st.markdown("<div style='height:28px'></div>", unsafe_allow_html=True)
                    if st.button("Save", key=f"sip_ubtn_{s['id']}", use_container_width=True):
                        db.add_sip_value_update(s["id"], new_val, new_invested,
                                                update_date=upd_date.isoformat(), note=upd_note,
                                                units_held=new_units if new_units != s["units_held"] else None)
                        st.success(f"Updated {s['fund_name']}")
                        st.rerun()

                st.markdown("<div style='height:6px'></div>", unsafe_allow_html=True)

            # Value history for selected fund
            st.markdown("<div style='height:12px'></div>", unsafe_allow_html=True)
            section_header("Value History", "&#x1f4c8;")
            hist_labels = {f"{s['fund_name']} ({s['amc'] or 'N/A'})": s for s in sips}
            sel_hist = st.selectbox("Select fund", list(hist_labels.keys()), key="sip_hist_select")
            if sel_hist:
                sel_s = hist_labels[sel_hist]
                val_hist = db.get_sip_value_history(sel_s["id"])
                if val_hist:
                    hist_df = pd.DataFrame([dict(v) for v in val_hist])
                    fig_h = go.Figure()
                    fig_h.add_trace(go.Scatter(x=hist_df["update_date"], y=hist_df["current_value"],
                        mode="lines+markers", name="Current Value", line=dict(color=COLORS["accent"], width=2.5),
                        fill="tozeroy", fillcolor=f"rgba(99,102,241,0.08)"))
                    if "total_invested" in hist_df.columns:
                        fig_h.add_trace(go.Scatter(x=hist_df["update_date"], y=hist_df["total_invested"],
                            mode="lines", name="Invested", line=dict(color=COLORS["text_muted"], width=1.5, dash="dash")))
                    apply_chart_theme(fig_h, height=300)
                    fig_h.update_layout(yaxis_title="Value (Rs.)")
                    st.plotly_chart(fig_h, use_container_width=True)

                    # History table with edit/delete
                    editing_vh_id = st.session_state.get("vh_editing_id")
                    confirm_del_vh = st.session_state.get("vh_confirm_del")

                    for v in reversed(list(val_hist)):
                        vid = v["id"]
                        g = v["current_value"] - (v["total_invested"] or 0)
                        gp = (g / v["total_invested"] * 100) if v["total_invested"] and v["total_invested"] > 0 else 0
                        vgc = COLORS["success"] if g >= 0 else COLORS["danger"]

                        if editing_vh_id == vid:
                            # Inline edit form
                            st.markdown(
                                f'<div style="background:{COLORS["card"]};border:2px solid {COLORS["accent"]};border-radius:10px;'
                                f'padding:12px 16px;margin-bottom:6px">',
                                unsafe_allow_html=True,
                            )
                            ec = st.columns([1.2, 1.2, 1.2, 2, 0.6, 0.6])
                            with ec[0]:
                                ev_date = st.date_input("Date", value=date.fromisoformat(v["update_date"]), key=f"vh_ed_{vid}")
                            with ec[1]:
                                ev_val = st.number_input("Current Value", value=float(v["current_value"]),
                                                         min_value=0.0, step=500.0, format="%.2f", key=f"vh_ev_{vid}")
                            with ec[2]:
                                ev_inv = st.number_input("Invested", value=float(v["total_invested"] or 0),
                                                         min_value=0.0, step=500.0, format="%.2f", key=f"vh_ei_{vid}")
                            with ec[3]:
                                ev_note = st.text_input("Note", value=v["note"] or "", key=f"vh_en_{vid}")
                            with ec[4]:
                                st.markdown("<div style='height:28px'></div>", unsafe_allow_html=True)
                                if st.button("\u2714", key=f"vh_save_{vid}", use_container_width=True):
                                    db.update_sip_value_update(vid, ev_val, ev_inv, ev_date.isoformat(), ev_note)
                                    st.session_state["vh_editing_id"] = None
                                    st.rerun()
                            with ec[5]:
                                st.markdown("<div style='height:28px'></div>", unsafe_allow_html=True)
                                if st.button("\u2718", key=f"vh_cancel_{vid}", use_container_width=True):
                                    st.session_state["vh_editing_id"] = None
                                    st.rerun()
                            st.markdown("</div>", unsafe_allow_html=True)
                        else:
                            # Display row with action buttons
                            rc = st.columns([1.2, 1.5, 1.5, 2, 2, 0.5, 0.5])
                            with rc[0]:
                                st.markdown(
                                    f'<div style="padding:8px 0;font-size:0.82rem;color:{COLORS["text_muted"]}">{v["update_date"]}</div>',
                                    unsafe_allow_html=True)
                            with rc[1]:
                                st.markdown(
                                    f'<div style="padding:8px 0;font-size:0.82rem;font-weight:600;color:{COLORS["text"]}">Val: {fmt_inr(v["current_value"])}</div>',
                                    unsafe_allow_html=True)
                            with rc[2]:
                                st.markdown(
                                    f'<div style="padding:8px 0;font-size:0.82rem;color:{COLORS["text_muted"]}">Inv: {fmt_inr(v["total_invested"] or 0)}</div>',
                                    unsafe_allow_html=True)
                            with rc[3]:
                                st.markdown(
                                    f'<div style="padding:8px 0;font-size:0.82rem;font-weight:600;color:{vgc}">{"+" if g>=0 else ""}{fmt_inr(g)} ({gp:+.1f}%)</div>',
                                    unsafe_allow_html=True)
                            with rc[4]:
                                st.markdown(
                                    f'<div style="padding:8px 0;font-size:0.75rem;color:{COLORS["text_muted"]}">{v["note"] or ""}</div>',
                                    unsafe_allow_html=True)
                            with rc[5]:
                                if st.button("\u270f\ufe0f", key=f"vh_edit_{vid}", help="Edit"):
                                    st.session_state["vh_editing_id"] = vid
                                    st.session_state["vh_confirm_del"] = None
                                    st.rerun()
                            with rc[6]:
                                if confirm_del_vh == vid:
                                    if st.button("\u2705", key=f"vh_cdel_{vid}", help="Confirm delete"):
                                        db.delete_sip_value_update(vid)
                                        st.session_state["vh_confirm_del"] = None
                                        st.rerun()
                                else:
                                    if st.button("\U0001f5d1", key=f"vh_del_{vid}", help="Delete"):
                                        st.session_state["vh_confirm_del"] = vid
                                        st.rerun()

                            # Divider
                            st.markdown(
                                f'<div style="height:1px;background:{COLORS["card_border"]};margin:0 0 2px 0"></div>',
                                unsafe_allow_html=True)
                else:
                    st.info("No value history yet. Update values above to start tracking trends.")

        else:
            st.info("No funds yet. Add funds first in the 'Add Fund' tab.")

    # ========== MANAGE TAB ==========
    with sip_tab_manage:
        if sips:
            section_header("Edit / Remove Funds", "&#x270f;")
            sip_names = {f"{s['fund_name']} ({s['amc'] or 'N/A'} - {s['category']})": s for s in sips}
            selected_sip = st.selectbox("Select fund to edit", [""] + list(sip_names.keys()), key="sip_manage_select")

            if selected_sip and selected_sip in sip_names:
                s = sip_names[selected_sip]
                with st.form(f"edit_sip_{s['id']}"):
                    e_cols = st.columns([3, 2, 1])
                    with e_cols[0]:
                        e_fund = st.text_input("Fund Name", value=s["fund_name"])
                    with e_cols[1]:
                        plat_opts = ["Groww", "ET Money", "K-Invest", "Zerodha (Coin)", "Kuvera", "MF Central", "Direct AMC", "Other"]
                        e_plat = st.selectbox("Platform", plat_opts, index=plat_opts.index(s["amc"]) if s["amc"] in plat_opts else len(plat_opts)-1)
                    with e_cols[2]:
                        cat_opts = ["Equity", "Debt", "Hybrid", "ELSS", "Index", "Liquid", "Other"]
                        e_cat = st.selectbox("Category", cat_opts, index=cat_opts.index(s["category"]) if s["category"] in cat_opts else 0)
                    e_cols2 = st.columns([1, 1, 1, 1])
                    with e_cols2[0]:
                        e_amt = st.number_input("SIP Amount", value=float(s["sip_amount"]), min_value=100.0, step=500.0, format="%.2f")
                    with e_cols2[1]:
                        freq_opts = ["Monthly", "Weekly", "Quarterly"]
                        e_freq = st.selectbox("Frequency", freq_opts, index=freq_opts.index(s["frequency"]) if s["frequency"] in freq_opts else 0)
                    with e_cols2[2]:
                        e_start = st.date_input("Start Date", value=date.fromisoformat(s["start_date"]) if s["start_date"] else date.today())
                    with e_cols2[3]:
                        stat_opts = ["Active", "Paused", "Completed", "Stopped"]
                        e_status = st.selectbox("Status", stat_opts, index=stat_opts.index(s["status"]) if s["status"] in stat_opts else 0)
                    e_cols3 = st.columns([1, 1, 2])
                    with e_cols3[0]:
                        e_folio = st.text_input("Folio", value=s["folio_number"] or "")
                    with e_cols3[1]:
                        e_end = st.date_input("End Date", value=date.fromisoformat(s["end_date"]) if s["end_date"] else date.today() + relativedelta(years=5))
                    with e_cols3[2]:
                        e_note = st.text_input("Note / Goal", value=s["note"] or "")

                    btn_cols = st.columns(2)
                    with btn_cols[0]:
                        if st.form_submit_button("Update Fund", type="primary", use_container_width=True):
                            db.update_sip(s["id"], e_fund, e_plat, e_folio, e_amt, e_freq, e_start.day,
                                          e_start.isoformat(), e_end.isoformat(), e_cat, e_status, e_note)
                            st.success("Updated!")
                            st.rerun()
                    with btn_cols[1]:
                        if st.form_submit_button("Remove Fund", use_container_width=True):
                            db.deactivate_sip(s["id"])
                            st.warning("Removed.")
                            st.rerun()
        else:
            st.info("No funds yet. Add your first fund in the 'Add Fund' tab.")

# ======================== POLICIES ========================
elif page == "Policies":
    page_title("Insurance Policies", "Track policies, premiums, coverage & fund value across providers")

    policies = db.get_policies()

    type_colors = {"ULIP": "#7C3AED", "Term": "#DC2626", "Endowment": "#059669", "Whole Life": "#1E40AF",
                   "Money Back": "#D97706", "Pension": "#0D9488", "Other": "#64748B"}
    prov_colors = {"TATA AIA": "#1A237E", "LIC": "#D32F2F", "HDFC Life": "#004D40", "ICICI Prudential": "#E65100",
                   "SBI Life": "#1565C0", "Max Life": "#6A1B9A", "Bajaj Allianz": "#0277BD", "Star Health": "#2E7D32",
                   "Kotak Life": "#C62828"}
    freq_mult = {"Yearly": 1, "Half-Yearly": 2, "Quarterly": 4, "Monthly": 12, "One-Time": 0}

    pol_tab_overview, pol_tab_policies, pol_tab_add, pol_tab_manage = st.tabs(
        ["\u2001\U0001f4ca\u2002Overview", "\u2001\U0001f4cb\u2002Policies", "\u2001\u2795\u2002Add Policy", "\u2001\u2699\ufe0f\u2002Manage"])

    # ========== ADD POLICY TAB ==========
    with pol_tab_add:
        st.markdown(
            f'<div style="background:linear-gradient(135deg,#EEF2FF,#E0E7FF,#C7D2FE);border:1px solid {COLORS["accent"]}25;'
            f'border-radius:16px;padding:22px 26px;margin-bottom:22px;display:flex;align-items:center;gap:16px;'
            f'box-shadow:0 4px 16px rgba(99,102,241,0.08)">'
            f'<div style="width:48px;height:48px;border-radius:14px;background:linear-gradient(135deg,{COLORS["accent"]},#818CF8);'
            f'display:flex;align-items:center;justify-content:center;flex-shrink:0;box-shadow:0 4px 12px rgba(99,102,241,0.25)">'
            f'<span style="font-size:1.4rem;filter:brightness(0) invert(1)">&#x1f6e1;</span></div>'
            f'<div>'
            f'<div style="font-size:1.05rem;font-weight:800;color:{COLORS["text"]}">Add Insurance Policy</div>'
            f'<div style="font-size:0.82rem;color:{COLORS["text_secondary"]};margin-top:2px;line-height:1.4">'
            f'Add life insurance, ULIP, term, endowment or any policy. Track premiums, fund value & maturity.</div>'
            f'</div></div>',
            unsafe_allow_html=True,
        )

        if "pol_form_ver" not in st.session_state:
            st.session_state["pol_form_ver"] = 0
        pfv = st.session_state["pol_form_ver"]

        p_cols = st.columns([2, 2, 1, 1])
        with p_cols[0]:
            pol_name = st.text_input("Policy Name *", placeholder="e.g. TATA AIA Smart Wealth", key=f"pol_name_{pfv}")
        with p_cols[1]:
            pol_provider = st.text_input("Provider *", placeholder="e.g. TATA AIA, LIC, HDFC Life", key=f"pol_prov_{pfv}")
        with p_cols[2]:
            pol_number = st.text_input("Policy Number", placeholder="e.g. U1234567", key=f"pol_num_{pfv}")
        with p_cols[3]:
            pol_type = st.selectbox("Type", ["Endowment", "ULIP", "Term", "Whole Life", "Money Back", "Pension", "Other"], key=f"pol_type_{pfv}")

        p_cols2 = st.columns([1, 1, 1, 1, 1])
        with p_cols2[0]:
            pol_premium = st.number_input("Premium Amount (Rs.)", min_value=0.0, step=500.0, format="%.2f", key=f"pol_prem_{pfv}")
        with p_cols2[1]:
            pol_freq = st.selectbox("Premium Frequency", ["Yearly", "Half-Yearly", "Quarterly", "Monthly", "One-Time"], key=f"pol_freq_{pfv}")
        with p_cols2[2]:
            pol_sum_assured = st.number_input("Sum Assured (Rs.)", min_value=0.0, step=10000.0, format="%.2f", key=f"pol_sa_{pfv}")
        with p_cols2[3]:
            pol_current = st.number_input("Current Fund Value (Rs.) *", min_value=0.0, step=1000.0, format="%.2f", key=f"pol_cv_{pfv}")
        with p_cols2[4]:
            pol_total_paid = st.number_input("Total Premiums Paid (Rs.)", min_value=0.0, step=1000.0, format="%.2f", key=f"pol_tp_{pfv}")

        p_cols3 = st.columns([1, 1, 2])
        with p_cols3[0]:
            pol_start = st.date_input("Start Date", value=None, key=f"pol_start_{pfv}")
        with p_cols3[1]:
            pol_maturity = st.date_input("Maturity Date", value=None, key=f"pol_mat_{pfv}")
        with p_cols3[2]:
            pol_note = st.text_input("Note (optional)", key=f"pol_note_{pfv}")

        if st.button("Add Policy", type="primary", use_container_width=True, key=f"pol_add_btn_{pfv}"):
            if pol_name and pol_provider:
                start_str = pol_start.isoformat() if pol_start else None
                mat_str = pol_maturity.isoformat() if pol_maturity else None
                db.add_policy(pol_name, pol_provider, pol_number, pol_type, pol_premium, pol_freq,
                              pol_sum_assured, pol_current, pol_total_paid, start_str, mat_str, pol_note)
                st.success(f"Added: {pol_name} ({pol_provider})")
                st.session_state["pol_form_ver"] += 1
                st.rerun()
            else:
                st.error("Please fill in Policy Name and Provider.")

    # ========== OVERVIEW TAB ==========
    with pol_tab_overview:
        if policies:
            total_value = sum(p["current_value"] for p in policies)
            total_premiums = sum(p["total_premiums_paid"] for p in policies)
            total_sum_assured = sum(p["sum_assured"] for p in policies)
            total_gain = total_value - total_premiums if total_premiums > 0 else 0
            gain_pct = (total_gain / total_premiums * 100) if total_premiums > 0 else 0
            annual_commitment = sum(p["premium_amount"] * freq_mult.get(p["premium_frequency"], 0) for p in policies)

            # --- Hero Banner ---
            gain_color = COLORS["success"] if total_gain >= 0 else COLORS["danger"]
            gain_sign = "+" if total_gain >= 0 else ""
            st.markdown(
                f'<div style="background:linear-gradient(135deg,#1E1B4B,#312E81,#3730A3);border-radius:20px;'
                f'padding:28px 32px;margin-bottom:20px;box-shadow:0 8px 32px rgba(30,27,75,0.25);position:relative;overflow:hidden">'
                f'<div style="position:absolute;top:-30px;right:-30px;width:160px;height:160px;border-radius:50%;'
                f'background:rgba(255,255,255,0.04)"></div>'
                f'<div style="position:absolute;bottom:-40px;left:40%;width:200px;height:200px;border-radius:50%;'
                f'background:rgba(255,255,255,0.03)"></div>'
                f'<div style="font-size:0.72rem;font-weight:700;text-transform:uppercase;letter-spacing:0.12em;'
                f'color:rgba(199,210,254,0.8);margin-bottom:6px">Insurance Portfolio</div>'
                f'<div style="display:flex;align-items:baseline;gap:14px;flex-wrap:wrap">'
                f'<div style="font-size:2rem;font-weight:900;color:#E0E7FF;letter-spacing:-0.02em">{fmt_inr(total_value)}</div>'
                f'<div style="font-size:0.95rem;font-weight:600;color:{gain_color};background:rgba(255,255,255,0.1);'
                f'padding:4px 14px;border-radius:20px">{gain_sign}{fmt_inr(total_gain)} ({gain_pct:+.1f}%)</div>'
                f'</div>'
                f'<div style="display:flex;gap:32px;margin-top:16px;flex-wrap:wrap">'
                f'<div><div style="font-size:0.68rem;color:rgba(199,210,254,0.6);text-transform:uppercase;letter-spacing:0.08em">Premiums Paid</div>'
                f'<div style="font-size:1.1rem;font-weight:700;color:#C7D2FE">{fmt_inr(total_premiums)}</div></div>'
                f'<div><div style="font-size:0.68rem;color:rgba(199,210,254,0.6);text-transform:uppercase;letter-spacing:0.08em">Sum Assured</div>'
                f'<div style="font-size:1.1rem;font-weight:700;color:#C7D2FE">{fmt_inr(total_sum_assured)}</div></div>'
                f'<div><div style="font-size:0.68rem;color:rgba(199,210,254,0.6);text-transform:uppercase;letter-spacing:0.08em">Annual Premium</div>'
                f'<div style="font-size:1.1rem;font-weight:700;color:#C7D2FE">{fmt_inr(annual_commitment)}</div></div>'
                f'<div><div style="font-size:0.68rem;color:rgba(199,210,254,0.6);text-transform:uppercase;letter-spacing:0.08em">Policies</div>'
                f'<div style="font-size:1.1rem;font-weight:700;color:#C7D2FE">{len(policies)}</div></div>'
                f'</div></div>',
                unsafe_allow_html=True,
            )

            # --- Provider Breakdown ---
            summary = db.get_policies_summary()
            if summary:
                section_header("By Provider", "&#x1f3e2;")
                prov_cols = st.columns(min(len(summary), 4))
                for i, s in enumerate(summary):
                    g = s["total_value"] - s["total_premiums"]
                    gp = (g / s["total_premiums"] * 100) if s["total_premiums"] > 0 else 0
                    gc = COLORS["success"] if g >= 0 else COLORS["danger"]
                    pc = prov_colors.get(s["provider"], COLORS["accent"])
                    with prov_cols[i % len(prov_cols)]:
                        st.markdown(
                            f'<div style="background:{COLORS["card"]};border:1px solid {COLORS["card_border"]};border-radius:12px;'
                            f'padding:14px 16px;box-shadow:{COLORS["card_shadow"]};border-left:4px solid {pc};margin-bottom:8px">'
                            f'<div style="display:flex;justify-content:space-between;align-items:center">'
                            f'<div style="font-size:0.82rem;font-weight:700;color:{COLORS["text"]}">{s["provider"]}</div>'
                            f'<div style="font-size:0.72rem;color:{COLORS["text_muted"]}">{s["count"]} {"policy" if s["count"]==1 else "policies"}</div></div>'
                            f'<div style="font-size:1.15rem;font-weight:800;color:{COLORS["text"]};margin:6px 0">{fmt_inr(s["total_value"])}</div>'
                            f'<div style="display:flex;justify-content:space-between;align-items:center;font-size:0.78rem">'
                            f'<span style="color:{COLORS["text_muted"]}">Paid: {fmt_inr(s["total_premiums"])}</span>'
                            f'<span style="color:{gc};font-weight:600">{"+" if g>=0 else ""}{fmt_inr(g)} ({gp:+.1f}%)</span></div>'
                            f'</div>',
                            unsafe_allow_html=True,
                        )

            # --- Charts Row ---
            ch_cols = st.columns(2)

            # Type breakdown pie
            with ch_cols[0]:
                section_header("By Policy Type", "&#x1f4ca;")
                type_data = {}
                for p in policies:
                    t = p["policy_type"]
                    type_data[t] = type_data.get(t, 0) + p["current_value"]
                if type_data:
                    fig_type = go.Figure(go.Pie(
                        labels=list(type_data.keys()), values=list(type_data.values()),
                        hole=0.55, textinfo="label+percent", textposition="outside",
                        marker=dict(colors=[type_colors.get(t, "#6B7280") for t in type_data.keys()]),
                        pull=[0.03] * len(type_data),
                    ))
                    apply_chart_theme(fig_type, height=300, margin=dict(t=10, b=10, l=10, r=10))
                    fig_type.update_layout(showlegend=False)
                    fig_type.update_traces(textfont_size=11)
                    st.plotly_chart(fig_type, use_container_width=True)

            # Fund value vs premiums bar
            with ch_cols[1]:
                section_header("Fund Value vs Premiums Paid", "&#x1f4b0;")
                pol_names_short = [p["name"][:20] + (".." if len(p["name"]) > 20 else "") for p in policies]
                fig_bar = go.Figure()
                fig_bar.add_trace(go.Bar(
                    name="Fund Value", x=pol_names_short, y=[p["current_value"] for p in policies],
                    marker_color=COLORS["accent"], marker_cornerradius=6,
                ))
                fig_bar.add_trace(go.Bar(
                    name="Premiums Paid", x=pol_names_short, y=[p["total_premiums_paid"] for p in policies],
                    marker_color="#CBD5E1", marker_cornerradius=6,
                ))
                apply_chart_theme(fig_bar, height=300)
                fig_bar.update_layout(barmode="group", xaxis_tickangle=-25, yaxis_title="Rs.")
                st.plotly_chart(fig_bar, use_container_width=True)

            # --- Maturity Timeline ---
            mat_policies = [(p, date.fromisoformat(p["maturity_date"])) for p in policies
                            if p["maturity_date"] and date.fromisoformat(p["maturity_date"]) > date.today()]
            if mat_policies:
                section_header("Maturity Timeline", "&#x1f4c5;")
                mat_policies.sort(key=lambda x: x[1])
                for p, mat_d in mat_policies:
                    days_left = (mat_d - date.today()).days
                    years_left = days_left / 365.25
                    start_d = date.fromisoformat(p["start_date"]) if p["start_date"] else mat_d - timedelta(days=days_left * 2)
                    total_days = (mat_d - start_d).days if start_d < mat_d else 1
                    elapsed = (date.today() - start_d).days
                    pct = min(max(elapsed / total_days * 100, 0), 100) if total_days > 0 else 0
                    bar_color = COLORS["warning"] if days_left <= 365 else COLORS["accent"] if days_left <= 1825 else COLORS["success"]
                    tc = type_colors.get(p["policy_type"], COLORS["text_muted"])
                    st.markdown(
                        f'<div style="background:{COLORS["card"]};border:1px solid {COLORS["card_border"]};border-radius:10px;'
                        f'padding:12px 16px;margin-bottom:6px;box-shadow:{COLORS["card_shadow"]}">'
                        f'<div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:8px">'
                        f'<div style="display:flex;align-items:center;gap:8px">'
                        f'<span style="font-size:0.82rem;font-weight:700;color:{COLORS["text"]}">{p["name"]}</span>'
                        f'<span style="background:{tc}15;color:{tc};padding:1px 8px;border-radius:8px;font-size:0.72rem;font-weight:600">{p["policy_type"]}</span>'
                        f'</div>'
                        f'<div style="font-size:0.78rem;color:{COLORS["text_muted"]}">{p["provider"]}</div></div>'
                        f'<div style="background:{COLORS["surface"]};border-radius:6px;height:10px;overflow:hidden;margin-bottom:6px">'
                        f'<div style="width:{pct:.1f}%;height:100%;background:linear-gradient(90deg,{bar_color},{bar_color}cc);'
                        f'border-radius:6px;transition:width 0.5s ease"></div></div>'
                        f'<div style="display:flex;justify-content:space-between;font-size:0.75rem;color:{COLORS["text_muted"]}">'
                        f'<span>{p["start_date"] or "?"}</span>'
                        f'<span style="font-weight:600;color:{bar_color}">{years_left:.1f} yrs left ({days_left} days)</span>'
                        f'<span>{p["maturity_date"]}</span></div>'
                        f'</div>',
                        unsafe_allow_html=True,
                    )

            # --- Coverage Analysis ---
            section_header("Coverage Analysis", "&#x1f6e1;")
            cov_cols = st.columns(4)
            with cov_cols[0]:
                coverage_ratio = (total_sum_assured / total_premiums) if total_premiums > 0 else 0
                cr_color = COLORS["success"] if coverage_ratio >= 10 else COLORS["warning"] if coverage_ratio >= 5 else COLORS["danger"]
                st.markdown(
                    f'<div style="background:{COLORS["card"]};border:1px solid {COLORS["card_border"]};border-radius:12px;'
                    f'padding:16px;text-align:center;box-shadow:{COLORS["card_shadow"]}">'
                    f'<div style="font-size:0.72rem;color:{COLORS["text_muted"]};text-transform:uppercase;letter-spacing:0.06em">Coverage Ratio</div>'
                    f'<div style="font-size:1.8rem;font-weight:900;color:{cr_color};margin:4px 0">{coverage_ratio:.1f}x</div>'
                    f'<div style="font-size:0.72rem;color:{COLORS["text_muted"]}">Sum assured / premiums</div></div>',
                    unsafe_allow_html=True)
            with cov_cols[1]:
                monthly_cost = annual_commitment / 12 if annual_commitment > 0 else 0
                st.markdown(
                    f'<div style="background:{COLORS["card"]};border:1px solid {COLORS["card_border"]};border-radius:12px;'
                    f'padding:16px;text-align:center;box-shadow:{COLORS["card_shadow"]}">'
                    f'<div style="font-size:0.72rem;color:{COLORS["text_muted"]};text-transform:uppercase;letter-spacing:0.06em">Monthly Cost</div>'
                    f'<div style="font-size:1.8rem;font-weight:900;color:{COLORS["text"]};margin:4px 0">{fmt_inr(monthly_cost)}</div>'
                    f'<div style="font-size:0.72rem;color:{COLORS["text_muted"]}">Annual: {fmt_inr(annual_commitment)}</div></div>',
                    unsafe_allow_html=True)
            with cov_cols[2]:
                term_count = sum(1 for p in policies if p["policy_type"] == "Term")
                invest_count = sum(1 for p in policies if p["policy_type"] in ("ULIP", "Endowment", "Money Back"))
                st.markdown(
                    f'<div style="background:{COLORS["card"]};border:1px solid {COLORS["card_border"]};border-radius:12px;'
                    f'padding:16px;text-align:center;box-shadow:{COLORS["card_shadow"]}">'
                    f'<div style="font-size:0.72rem;color:{COLORS["text_muted"]};text-transform:uppercase;letter-spacing:0.06em">Policy Mix</div>'
                    f'<div style="font-size:1.8rem;font-weight:900;color:{COLORS["text"]};margin:4px 0">{term_count}T / {invest_count}I</div>'
                    f'<div style="font-size:0.72rem;color:{COLORS["text_muted"]}">Term / Investment</div></div>',
                    unsafe_allow_html=True)
            with cov_cols[3]:
                roi = gain_pct if total_premiums > 0 else 0
                roi_color = COLORS["success"] if roi >= 0 else COLORS["danger"]
                st.markdown(
                    f'<div style="background:{COLORS["card"]};border:1px solid {COLORS["card_border"]};border-radius:12px;'
                    f'padding:16px;text-align:center;box-shadow:{COLORS["card_shadow"]}">'
                    f'<div style="font-size:0.72rem;color:{COLORS["text_muted"]};text-transform:uppercase;letter-spacing:0.06em">Return on Premiums</div>'
                    f'<div style="font-size:1.8rem;font-weight:900;color:{roi_color};margin:4px 0">{roi:+.1f}%</div>'
                    f'<div style="font-size:0.72rem;color:{COLORS["text_muted"]}">{"+" if total_gain>=0 else ""}{fmt_inr(total_gain)}</div></div>',
                    unsafe_allow_html=True)

            # --- Insights ---
            insights = []
            insights.append(f"Portfolio: <strong>{len(policies)} policies</strong>, premiums paid {fmt_inr_full(total_premiums)}, current fund value <strong>{fmt_inr_full(total_value)}</strong>.")
            if total_premiums > 0:
                color = COLORS["success"] if total_gain >= 0 else COLORS["danger"]
                insights.append(f"Overall return: <strong style='color:{color}'>{'+' if total_gain >= 0 else ''}{fmt_inr_full(total_gain)} ({gain_pct:+.1f}%)</strong> on premiums paid.")
            if total_sum_assured > 0:
                insights.append(f"Total sum assured: <strong>{fmt_inr_full(total_sum_assured)}</strong> ({fmt_inr_words(total_sum_assured)}) - coverage ratio: {coverage_ratio:.1f}x premiums paid.")
            if annual_commitment > 0:
                insights.append(f"Annual premium commitment: <strong>{fmt_inr_full(annual_commitment)}</strong> ({fmt_inr_words(annual_commitment)}), monthly: {fmt_inr_full(monthly_cost)}.")
            # Maturity alerts
            maturing_soon = []
            for p in policies:
                if p["maturity_date"]:
                    try:
                        mat_d = date.fromisoformat(p["maturity_date"])
                        days = (mat_d - date.today()).days
                        if 0 < days <= 365:
                            maturing_soon.append((p["name"], days))
                    except ValueError:
                        pass
            if maturing_soon:
                mat_list = ", ".join(f"<strong>{n}</strong> ({d} days)" for n, d in sorted(maturing_soon, key=lambda x: x[1]))
                warn_c = COLORS["warning"]
                insights.append(f"<span style='color:{warn_c}'>Maturing within 1 year: {mat_list}</span>")
            # Best / worst performing
            if len(policies) > 1 and total_premiums > 0:
                pol_returns = [(p["name"], (p["current_value"] - p["total_premiums_paid"]) / p["total_premiums_paid"] * 100)
                              for p in policies if p["total_premiums_paid"] > 0]
                if pol_returns:
                    best = max(pol_returns, key=lambda x: x[1])
                    worst = min(pol_returns, key=lambda x: x[1])
                    insights.append(f"Best performing: <strong>{best[0]}</strong> ({best[1]:+.1f}%), Weakest: <strong>{worst[0]}</strong> ({worst[1]:+.1f}%).")
            # Term vs investment allocation
            term_value = sum(p["current_value"] for p in policies if p["policy_type"] == "Term")
            invest_value = sum(p["current_value"] for p in policies if p["policy_type"] in ("ULIP", "Endowment", "Money Back"))
            if invest_value > 0 and term_value > 0:
                insights.append(f"Investment-type policies hold <strong>{fmt_inr(invest_value)}</strong> ({invest_value/total_value*100:.0f}%), term policies: <strong>{fmt_inr(term_value)}</strong>.")
            # Net worth context
            all_src = db.get_sources()
            nw = sum(db.get_latest_balance(src["id"]) for src in all_src)
            if nw > 0:
                pol_pct = total_value / nw * 100
                insights.append(f"Insurance policies represent <strong>{pol_pct:.1f}%</strong> of your net worth.")

            insight_box(insights, "Insurance Insights")
        else:
            st.markdown(
                f'<div style="background:{COLORS["card"]};border:1px solid {COLORS["card_border"]};border-radius:16px;'
                f'padding:48px 32px;text-align:center;margin-top:20px">'
                f'<div style="font-size:3rem;margin-bottom:12px">&#x1f6e1;</div>'
                f'<div style="font-size:1.1rem;font-weight:700;color:{COLORS["text"]};margin-bottom:6px">No Policies Yet</div>'
                f'<div style="font-size:0.88rem;color:{COLORS["text_muted"]}">Head to the "Add Policy" tab to add your first insurance policy.</div>'
                f'</div>',
                unsafe_allow_html=True,
            )

    # ========== POLICIES TAB (Detailed Cards) ==========
    with pol_tab_policies:
        if policies:
            # Quick update
            st.markdown(
                f'<div style="background:linear-gradient(135deg,{COLORS["surface"]},#EEF2FF);border:1px solid {COLORS["card_border"]};'
                f'border-radius:14px;padding:16px 20px;margin-bottom:16px">'
                f'<div style="font-size:0.78rem;font-weight:700;text-transform:uppercase;letter-spacing:0.06em;'
                f'color:{COLORS["accent"]};margin-bottom:10px">&#x1f504; Quick Update Fund Value</div></div>',
                unsafe_allow_html=True,
            )
            upd_cols = st.columns([2, 1, 1])
            policy_map = {f"{p['name']} ({p['provider']})": p for p in policies}
            with upd_cols[0]:
                sel_upd = st.selectbox("Select policy", [""] + list(policy_map.keys()), key="pol_quick_upd")
            if sel_upd and sel_upd in policy_map:
                sel_p = policy_map[sel_upd]
                with upd_cols[1]:
                    new_val = st.number_input("New Fund Value (Rs.)", value=float(sel_p["current_value"]),
                                              min_value=0.0, step=1000.0, format="%.2f", key="pol_new_val")
                with upd_cols[2]:
                    st.markdown("<div style='height:28px'></div>", unsafe_allow_html=True)
                    if st.button("Update Value", type="primary", use_container_width=True, key="pol_upd_btn"):
                        db.update_policy_value(sel_p["id"], new_val)
                        st.success(f"Updated {sel_p['name']} to {fmt_inr_full(new_val)}")
                        st.rerun()

            st.markdown("<div style='height:8px'></div>", unsafe_allow_html=True)

            # Policy Cards
            for p in policies:
                gain = p["current_value"] - p["total_premiums_paid"]
                gain_pct_item = (gain / p["total_premiums_paid"] * 100) if p["total_premiums_paid"] > 0 else 0
                gc = COLORS["success"] if gain >= 0 else COLORS["danger"]
                tc = type_colors.get(p["policy_type"], COLORS["text_muted"])
                pc = prov_colors.get(p["provider"], COLORS["accent"])

                # Maturity info
                mat_html = ""
                if p["maturity_date"]:
                    try:
                        mat_d = date.fromisoformat(p["maturity_date"])
                        days_left = (mat_d - date.today()).days
                        if days_left > 0:
                            yrs = days_left / 365.25
                            mat_html = (f'<span style="font-size:0.75rem;color:{COLORS["text_muted"]}">'
                                        f'Matures: {p["maturity_date"]} ({yrs:.1f} yrs)</span>')
                        else:
                            mat_html = (f'<span style="font-size:0.75rem;color:{COLORS["success"]};font-weight:600">'
                                        f'Matured on {p["maturity_date"]}</span>')
                    except ValueError:
                        mat_html = f'<span style="font-size:0.75rem;color:{COLORS["text_muted"]}">Matures: {p["maturity_date"]}</span>'

                note_html = f'<div style="font-size:0.75rem;color:{COLORS["text_muted"]};margin-top:4px;font-style:italic">{p["note"]}</div>' if p["note"] else ""

                st.markdown(
                    f'<div style="background:{COLORS["card"]};border:1px solid {COLORS["card_border"]};border-radius:14px;'
                    f'padding:18px 22px;margin-bottom:10px;box-shadow:{COLORS["card_shadow"]};border-left:4px solid {pc};'
                    f'transition:transform 0.15s;position:relative">'
                    # Header row
                    f'<div style="display:flex;justify-content:space-between;align-items:flex-start;margin-bottom:10px">'
                    f'<div>'
                    f'<div style="display:flex;align-items:center;gap:8px;flex-wrap:wrap">'
                    f'<span style="font-size:1rem;font-weight:800;color:{COLORS["text"]}">{p["name"]}</span>'
                    f'<span style="background:{tc}15;color:{tc};padding:2px 10px;border-radius:10px;font-size:0.72rem;font-weight:700">{p["policy_type"]}</span>'
                    f'</div>'
                    f'<div style="font-size:0.78rem;color:{COLORS["text_muted"]};margin-top:2px">'
                    f'{p["provider"]} {" | #" + p["policy_number"] if p["policy_number"] else ""}</div>'
                    f'</div>'
                    f'<div style="text-align:right">'
                    f'<div style="font-size:1.15rem;font-weight:800;color:{COLORS["text"]}">{fmt_inr(p["current_value"])}</div>'
                    f'<div style="font-size:0.82rem;font-weight:600;color:{gc}">{"+" if gain>=0 else ""}{fmt_inr(gain)} ({gain_pct_item:+.1f}%)</div>'
                    f'</div></div>'
                    # Detail grid
                    f'<div style="display:flex;gap:24px;flex-wrap:wrap;font-size:0.82rem;padding-top:8px;border-top:1px solid {COLORS["card_border"]}">'
                    f'<div><span style="color:{COLORS["text_muted"]}">Premium:</span> '
                    f'<span style="font-weight:600;color:{COLORS["text"]}">{fmt_inr(p["premium_amount"])}</span>'
                    f'<span style="color:{COLORS["text_muted"]}"> / {p["premium_frequency"]}</span></div>'
                    f'<div><span style="color:{COLORS["text_muted"]}">Total Paid:</span> '
                    f'<span style="font-weight:600;color:{COLORS["text"]}">{fmt_inr(p["total_premiums_paid"])}</span></div>'
                    f'<div><span style="color:{COLORS["text_muted"]}">Sum Assured:</span> '
                    f'<span style="font-weight:600;color:{COLORS["text"]}">{fmt_inr(p["sum_assured"]) if p["sum_assured"] else "--"}</span></div>'
                    f'{mat_html}'
                    f'</div>'
                    f'{note_html}'
                    f'</div>',
                    unsafe_allow_html=True,
                )
        else:
            st.info("No policies added yet. Go to the 'Add Policy' tab to get started.")

    # ========== MANAGE TAB ==========
    with pol_tab_manage:
        if policies:
            section_header("Edit / Remove Policies", "&#x270f;")
            pol_names = {f"{p['name']} ({p['provider']}) - {p['policy_number'] or 'No #'}": p for p in policies}
            sel_pol = st.selectbox("Select policy to edit/remove", [""] + list(pol_names.keys()), key="pol_edit_select")

            if sel_pol and sel_pol in pol_names:
                p = pol_names[sel_pol]
                with st.form("edit_policy"):
                    e_cols = st.columns([2, 2, 1, 1])
                    with e_cols[0]:
                        e_name = st.text_input("Name", value=p["name"])
                    with e_cols[1]:
                        e_provider = st.text_input("Provider", value=p["provider"])
                    with e_cols[2]:
                        e_number = st.text_input("Policy #", value=p["policy_number"] or "")
                    with e_cols[3]:
                        type_opts = ["Endowment", "ULIP", "Term", "Whole Life", "Money Back", "Pension", "Other"]
                        e_type = st.selectbox("Type", type_opts, index=type_opts.index(p["policy_type"]) if p["policy_type"] in type_opts else 0)

                    e_cols2 = st.columns([1, 1, 1, 1, 1])
                    with e_cols2[0]:
                        e_prem = st.number_input("Premium (Rs.)", value=float(p["premium_amount"]), min_value=0.0, step=500.0, format="%.2f")
                    with e_cols2[1]:
                        freq_opts = ["Yearly", "Half-Yearly", "Quarterly", "Monthly", "One-Time"]
                        e_freq = st.selectbox("Frequency", freq_opts, index=freq_opts.index(p["premium_frequency"]) if p["premium_frequency"] in freq_opts else 0)
                    with e_cols2[2]:
                        e_sa = st.number_input("Sum Assured", value=float(p["sum_assured"] or 0), min_value=0.0, step=10000.0, format="%.2f")
                    with e_cols2[3]:
                        e_cv = st.number_input("Fund Value", value=float(p["current_value"]), min_value=0.0, step=1000.0, format="%.2f")
                    with e_cols2[4]:
                        e_tp = st.number_input("Total Paid", value=float(p["total_premiums_paid"]), min_value=0.0, step=1000.0, format="%.2f")

                    e_cols3 = st.columns([1, 1, 2])
                    with e_cols3[0]:
                        e_start = st.date_input("Start Date", value=date.fromisoformat(p["start_date"]) if p["start_date"] else None, key="pol_edit_start")
                    with e_cols3[1]:
                        e_mat = st.date_input("Maturity Date", value=date.fromisoformat(p["maturity_date"]) if p["maturity_date"] else None, key="pol_edit_mat")
                    with e_cols3[2]:
                        e_note = st.text_input("Note", value=p["note"] or "")

                    btn_cols = st.columns(2)
                    with btn_cols[0]:
                        if st.form_submit_button("Update Policy", type="primary", use_container_width=True):
                            start_str = e_start.isoformat() if e_start else None
                            mat_str = e_mat.isoformat() if e_mat else None
                            db.update_policy(p["id"], e_name, e_provider, e_number, e_type, e_prem, e_freq,
                                             e_sa, e_cv, e_tp, start_str, mat_str, e_note)
                            st.success("Updated!")
                            st.rerun()
                    with btn_cols[1]:
                        if st.form_submit_button("Remove Policy", use_container_width=True):
                            db.deactivate_policy(p["id"])
                            st.warning("Removed.")
                            st.rerun()
        else:
            st.info("No policies to manage. Add policies first.")

# ======================== LENT OUT ========================
elif page == "Lent Out":
    page_title("Lent Out", "Track money lent to individuals with repayment history")

    # --- Add New Loan ---
    section_header("Lend Money", "&#x2795;")
    with st.form("add_loan", clear_on_submit=True):
        l_cols = st.columns([2, 1, 1, 1, 2])
        with l_cols[0]:
            ln_borrower = st.text_input("Borrower Name *", placeholder="e.g. Ravi, Suresh")
        with l_cols[1]:
            ln_amount = st.number_input("Amount Lent (Rs.) *", min_value=0.0, step=1000.0, format="%.2f")
        with l_cols[2]:
            ln_date = st.date_input("Lent Date", value=date.today(), key="ln_date")
        with l_cols[3]:
            ln_return = st.date_input("Expected Return", value=None, key="ln_return")
        with l_cols[4]:
            ln_note = st.text_input("Note (optional)", placeholder="Purpose, terms, etc.")

        if st.form_submit_button("Add Loan", type="primary", use_container_width=True):
            if ln_borrower and ln_amount > 0:
                ret_str = ln_return.isoformat() if ln_return else None
                db.add_loan(ln_borrower, ln_amount, ln_date.isoformat(), ret_str, ln_note)
                st.success(f"Added: Rs. {ln_amount:,.2f} lent to {ln_borrower}")
                st.rerun()
            else:
                st.error("Please fill in Borrower Name and Amount.")

    # --- Overview ---
    loans = db.get_loans()
    if loans:
        section_header("Receivables Overview", "&#x1f4ca;")

        total_lent = sum(l["original_amount"] for l in loans)
        total_outstanding = sum(l["outstanding"] for l in loans)
        total_recovered = total_lent - total_outstanding
        recovery_pct = (total_recovered / total_lent * 100) if total_lent > 0 else 0
        active_count = sum(1 for l in loans if l["status"] in ("Active", "Partially Paid"))
        settled_count = sum(1 for l in loans if l["status"] == "Fully Paid")

        metric_row(
            ("Total Lent Out", fmt_inr_full(total_lent), f"{len(loans)} loans", "blue", "&#x1f4b8;"),
            ("Outstanding", fmt_inr_full(total_outstanding), f"{active_count} active", "amber" if total_outstanding > 0 else "green", "&#x23f3;"),
            ("Recovered", fmt_inr_full(total_recovered), f"{recovery_pct:.1f}% recovered", "green", "&#x2705;"),
            ("Settled", str(settled_count), f"of {len(loans)} loans", "green" if settled_count > 0 else "blue", "&#x1f4cb;"),
        )

        # --- Record Repayment ---
        section_header("Record Repayment", "&#x1f4b0;")
        active_loans = [l for l in loans if l["status"] in ("Active", "Partially Paid")]
        if active_loans:
            loan_map = {f"{l['borrower']} — Outstanding: Rs. {l['outstanding']:,.2f}": l for l in active_loans}
            rp_cols = st.columns([2, 1, 1, 2])
            with rp_cols[0]:
                sel_loan = st.selectbox("Select Loan", [""] + list(loan_map.keys()), key="rp_select")
            if sel_loan and sel_loan in loan_map:
                sel_l = loan_map[sel_loan]
                with rp_cols[1]:
                    rp_amount = st.number_input("Payment Amount (Rs.)", min_value=0.01, max_value=float(sel_l["outstanding"]),
                                                value=float(sel_l["outstanding"]), step=500.0, format="%.2f", key="rp_amt")
                with rp_cols[2]:
                    rp_date = st.date_input("Payment Date", value=date.today(), key="rp_date")
                with rp_cols[3]:
                    rp_note = st.text_input("Payment Note", placeholder="Mode of payment, etc.", key="rp_note")

                if st.button("Record Payment", type="primary", use_container_width=True, key="rp_btn"):
                    db.add_loan_payment(sel_l["id"], rp_amount, rp_date.isoformat(), rp_note)
                    remaining = sel_l["outstanding"] - rp_amount
                    if remaining <= 0:
                        st.success(f"Payment of {fmt_inr_full(rp_amount)} recorded. Loan from {sel_l['borrower']} is FULLY PAID!")
                    else:
                        st.success(f"Payment of {fmt_inr_full(rp_amount)} recorded. Remaining: {fmt_inr_full(remaining)}")
                    st.rerun()
        else:
            st.success("All loans are fully settled!")

        # --- Detailed Table ---
        section_header("All Loans", "&#x1f4cb;")

        # Status filter
        filter_col1, filter_col2 = st.columns([1, 3])
        with filter_col1:
            status_filter = st.selectbox("Filter by Status", ["All", "Active", "Partially Paid", "Fully Paid", "Written Off"], key="ln_filter")

        filtered_loans = loans if status_filter == "All" else [l for l in loans if l["status"] == status_filter]

        loan_rows = ""
        for l in filtered_loans:
            recovered = l["original_amount"] - l["outstanding"]
            rec_pct = (recovered / l["original_amount"] * 100) if l["original_amount"] > 0 else 0

            # Status badge colors
            status_colors = {
                "Active": (COLORS["warning"], COLORS["warning_light"]),
                "Partially Paid": ("#2563EB", "#EFF6FF"),
                "Fully Paid": (COLORS["success"], COLORS["success_light"]),
                "Written Off": (COLORS["danger"], COLORS["danger_light"]),
            }
            s_fg, s_bg = status_colors.get(l["status"], (COLORS["text_muted"], COLORS["surface2"]))

            # Overdue check
            overdue_tag = ""
            if l["expected_return_date"] and l["status"] in ("Active", "Partially Paid"):
                try:
                    exp_date = date.fromisoformat(l["expected_return_date"])
                    if exp_date < date.today():
                        days_over = (date.today() - exp_date).days
                        overdue_tag = f"<br><span style='font-size:0.75rem;color:{COLORS['danger']};font-weight:600'>Overdue by {days_over}d</span>"
                except ValueError:
                    pass

            # Progress bar
            bar_width = min(rec_pct, 100)
            bar_color = COLORS["success"] if rec_pct >= 100 else COLORS["primary_light"] if rec_pct > 50 else COLORS["warning"]
            progress_bar = f"""<div style="background:{COLORS['surface2']};border-radius:4px;height:6px;width:100%;margin-top:4px">
                <div style="background:{bar_color};border-radius:4px;height:6px;width:{bar_width}%"></div></div>
                <span style="font-size:0.75rem;color:{COLORS['text_muted']}">{rec_pct:.0f}%</span>"""

            loan_rows += f"""
            <tr>
                <td style="font-weight:500;color:{COLORS['text']}">{l['borrower']}</td>
                <td class="amount">{fmt_inr_full(l['original_amount'])}</td>
                <td class="amount" style="font-weight:600;color:{COLORS['danger'] if l['outstanding'] > 0 else COLORS['success']}">{fmt_inr_full(l['outstanding'])}</td>
                <td class="amount" style="color:{COLORS['success']}">{fmt_inr_full(recovered)}</td>
                <td>{progress_bar}</td>
                <td style="text-align:center"><span style="background:{s_bg};color:{s_fg};
                    padding:2px 10px;border-radius:10px;font-size:0.8rem;font-weight:600">{l['status']}</span></td>
                <td style="font-size:0.85rem;color:{COLORS['text_muted']}">{l['lent_date']}</td>
                <td style="font-size:0.85rem">{l['expected_return_date'] or '--'}{overdue_tag}</td>
                <td style="font-size:0.85rem;color:{COLORS['text_muted']}">{l['note'] or '--'}</td>
            </tr>"""

        st.markdown(f"""
        <table class="styled-table">
            <thead><tr>
                <th>Borrower</th><th>Amount Lent</th><th>Outstanding</th><th>Recovered</th>
                <th>Progress</th><th>Status</th><th>Lent Date</th><th>Expected Return</th><th>Note</th>
            </tr></thead>
            <tbody>{loan_rows}</tbody>
        </table>
        """, unsafe_allow_html=True)

        # --- Financial Insights ---
        insights = []
        insights.append(f"Total lent: <strong>{fmt_inr_full(total_lent)}</strong> across {len(loans)} loans. Outstanding: <strong>{fmt_inr_full(total_outstanding)}</strong>.")
        insights.append(f"Recovery rate: <strong>{recovery_pct:.1f}%</strong> — {fmt_inr_full(total_recovered)} recovered, {settled_count} loans fully settled.")
        # Overdue analysis
        overdue_loans = []
        for l in loans:
            if l["expected_return_date"] and l["status"] in ("Active", "Partially Paid"):
                try:
                    exp = date.fromisoformat(l["expected_return_date"])
                    if exp < date.today():
                        overdue_loans.append((l["borrower"], l["outstanding"], (date.today() - exp).days))
                except ValueError:
                    pass
        if overdue_loans:
            overdue_total = sum(o[1] for o in overdue_loans)
            insights.append(f"<span style='color:{COLORS['danger']}'><strong>{len(overdue_loans)} overdue loan(s)</strong> totalling {fmt_inr_full(overdue_total)}: "
                          + ", ".join(f"{o[0]} ({o[2]} days)" for o in sorted(overdue_loans, key=lambda x: x[2], reverse=True)) + "</span>")
        elif active_count > 0:
            insights.append(f"<span style='color:{COLORS['success']}'>No overdue loans — all {active_count} active loans are within expected return dates.</span>")
        # Largest outstanding
        if active_count > 0:
            active_list = [(l["borrower"], l["outstanding"]) for l in loans if l["status"] in ("Active", "Partially Paid")]
            if active_list:
                largest = max(active_list, key=lambda x: x[1])
                insights.append(f"Largest outstanding: <strong>{largest[0]}</strong> with {fmt_inr_full(largest[1])} ({largest[1]/total_outstanding*100:.0f}% of receivables).")
        # Net worth context
        if total_outstanding > 0:
            all_src = db.get_sources()
            nw = sum(db.get_latest_balance(src["id"]) for src in all_src)
            if nw > 0:
                insights.append(f"Outstanding loans are <strong>{total_outstanding/nw*100:.1f}%</strong> of net worth — this capital is not earning returns.")

        insight_box(insights, "Receivables Insights")

        # --- Payment History for a loan ---
        section_header("Payment History", "&#x1f4dc;")
        hist_map = {f"{l['borrower']} — Rs. {l['original_amount']:,.2f} ({l['lent_date']})": l for l in loans}
        sel_hist = st.selectbox("Select loan to view payments", [""] + list(hist_map.keys()), key="ln_hist")

        if sel_hist and sel_hist in hist_map:
            sel_loan_hist = hist_map[sel_hist]
            payments = db.get_loan_payments(sel_loan_hist["id"])
            if payments:
                pay_rows = ""
                for pay in payments:
                    pay_rows += f"""
                    <tr>
                        <td>{pay['payment_date']}</td>
                        <td class="amount" style="color:{COLORS['success']};font-weight:500">{fmt_inr_full(pay['amount'])}</td>
                        <td style="color:{COLORS['text_muted']}">{pay['note'] or '--'}</td>
                    </tr>"""
                st.markdown(f"""
                <table class="styled-table">
                    <thead><tr><th>Date</th><th>Amount</th><th>Note</th></tr></thead>
                    <tbody>{pay_rows}</tbody>
                </table>
                """, unsafe_allow_html=True)
            else:
                st.info("No payments recorded for this loan yet.")

        # --- Manage Loans ---
        section_header("Manage Loans", "&#x270f;")
        edit_map = {f"{l['borrower']} — Rs. {l['original_amount']:,.2f} ({l['status']})": l for l in loans}
        sel_edit = st.selectbox("Select loan to edit/remove", [""] + list(edit_map.keys()), key="ln_edit")

        if sel_edit and sel_edit in edit_map:
            l = edit_map[sel_edit]
            with st.form("edit_loan"):
                e_cols = st.columns([2, 1, 1, 1])
                with e_cols[0]:
                    e_borrower = st.text_input("Borrower", value=l["borrower"])
                with e_cols[1]:
                    e_orig = st.number_input("Original Amount", value=float(l["original_amount"]), min_value=0.0, step=1000.0, format="%.2f")
                with e_cols[2]:
                    e_out = st.number_input("Outstanding", value=float(l["outstanding"]), min_value=0.0, step=1000.0, format="%.2f")
                with e_cols[3]:
                    status_opts = ["Active", "Partially Paid", "Fully Paid", "Written Off"]
                    e_status = st.selectbox("Status", status_opts, index=status_opts.index(l["status"]) if l["status"] in status_opts else 0)
                e_cols2 = st.columns([1, 1, 2])
                with e_cols2[0]:
                    e_lent_dt = st.date_input("Lent Date", value=date.fromisoformat(l["lent_date"]), key="ln_edit_date")
                with e_cols2[1]:
                    e_ret_dt = st.date_input("Expected Return", value=date.fromisoformat(l["expected_return_date"]) if l["expected_return_date"] else None, key="ln_edit_ret")
                with e_cols2[2]:
                    e_note = st.text_input("Note", value=l["note"] or "")
                btn_cols = st.columns(2)
                with btn_cols[0]:
                    if st.form_submit_button("Update Loan", type="primary", use_container_width=True):
                        ret_str = e_ret_dt.isoformat() if e_ret_dt else None
                        db.update_loan(l["id"], e_borrower, e_orig, e_out, e_lent_dt.isoformat(), ret_str, e_status, e_note)
                        st.success("Updated!")
                        st.rerun()
                with btn_cols[1]:
                    if st.form_submit_button("Remove Loan", use_container_width=True):
                        db.deactivate_loan(l["id"])
                        st.warning("Removed.")
                        st.rerun()
    else:
        st.info("No loans recorded yet. Add your first loan above.")

# ======================== GOLD SCHEMES ========================
elif page == "Gold Schemes":
    page_title("Gold Schemes", "Track monthly gold savings with Malabar, Kalyan & other jewellers")

    from dateutil.relativedelta import relativedelta

    schemes = db.get_gold_schemes()

    # --- Tabs: clean flow ---
    tab_overview, tab_add_payment, tab_add_scheme, tab_manage = st.tabs(
        ["\u2001📊\u2002Overview", "\u2001💰\u2002Record Payment", "\u2001➕\u2002Add New Scheme", "\u2001⚙️\u2002Manage"])

    # ========== ADD SCHEME TAB ==========
    with tab_add_scheme:
        st.markdown(f"""
        <div style="background:linear-gradient(135deg,#FFFBEB,#FEF3C7);border:1px solid #F59E0B30;border-radius:14px;
            padding:18px 22px;margin-bottom:20px;display:flex;align-items:center;gap:14px">
            <div style="font-size:1.8rem">&#x1f4b3;</div>
            <div>
                <div style="font-size:0.95rem;font-weight:700;color:{COLORS['text']}">Start a New Gold Savings Scheme</div>
                <div style="font-size:0.82rem;color:{COLORS['text_secondary']}">Enter scheme details below. The end date and preview update live as you type.</div>
            </div>
        </div>
        """, unsafe_allow_html=True)

        # Use a version counter to force fresh widgets after each add
        if "gs_form_ver" not in st.session_state:
            st.session_state["gs_form_ver"] = 0
        fv = st.session_state["gs_form_ver"]

        # Use regular widgets (not form) so preview updates reactively
        gs_cols = st.columns([3, 1, 1])
        with gs_cols[0]:
            gs_jeweller = st.text_input("Jeweller Name *", placeholder="e.g. Malabar Gold, Kalyan Jewellers", key=f"gs_jeweller_{fv}")
        with gs_cols[1]:
            gs_monthly = st.number_input("Monthly Amount (Rs.) *", min_value=100.0, step=500.0, value=1000.0, format="%.2f", key=f"gs_monthly_amt_{fv}")
        with gs_cols[2]:
            gs_months = st.number_input("Duration (Months)", min_value=1, max_value=36, value=11, step=1, key=f"gs_duration_{fv}")

        gs_cols2 = st.columns([1, 1, 2])
        with gs_cols2[0]:
            gs_start = st.date_input("Start Date", value=date.today(), key=f"gs_start_{fv}")
        with gs_cols2[1]:
            gs_end_date = gs_start + relativedelta(months=int(gs_months))
            st.date_input("End Date (auto)", value=gs_end_date, disabled=True, key=f"gs_end_display_{fv}")
        with gs_cols2[2]:
            gs_note = st.text_input("Note (optional)", placeholder="Branch, terms, etc.", key=f"gs_note_input_{fv}")

        # Live preview — updates reactively as user changes values
        gs_total_expected = gs_monthly * gs_months
        st.markdown(f"""
        <div style="background:{COLORS['card']};border:1px solid {COLORS['card_border']};border-radius:12px;
            padding:16px 20px;margin:10px 0;box-shadow:{COLORS['card_shadow']};border-left:4px solid {COLORS['gold_accent']}">
            <div style="font-size:0.68rem;font-weight:700;text-transform:uppercase;letter-spacing:0.07em;color:{COLORS['gold']};margin-bottom:8px">Scheme Preview</div>
            <div style="display:flex;gap:24px;flex-wrap:wrap;align-items:center">
                <div>
                    <span style="font-size:0.75rem;color:{COLORS['text_muted']}">Monthly</span>
                    <div style="font-size:1.15rem;font-weight:800;color:{COLORS['text']}">{fmt_inr_full(gs_monthly)}</div>
                </div>
                <div style="font-size:1.2rem;color:{COLORS['text_muted']}">×</div>
                <div>
                    <span style="font-size:0.75rem;color:{COLORS['text_muted']}">Duration</span>
                    <div style="font-size:1.15rem;font-weight:800;color:{COLORS['text']}">{gs_months} months</div>
                </div>
                <div style="font-size:1.2rem;color:{COLORS['text_muted']}">=</div>
                <div>
                    <span style="font-size:0.75rem;color:{COLORS['text_muted']}">Total Commitment</span>
                    <div style="font-size:1.15rem;font-weight:800;color:{COLORS['primary']}">{fmt_inr_full(gs_total_expected)}</div>
                    <div style="font-size:0.72rem;color:{COLORS['text_muted']}">{fmt_inr_words(gs_total_expected)}</div>
                </div>
                <div style="margin-left:auto;text-align:right">
                    <span style="font-size:0.75rem;color:{COLORS['text_muted']}">Period</span>
                    <div style="font-size:0.95rem;font-weight:600;color:{COLORS['text_secondary']}">{gs_start.strftime('%b %Y')} → {gs_end_date.strftime('%b %Y')}</div>
                </div>
            </div>
        </div>
        """, unsafe_allow_html=True)

        # Optional: pre-load existing payments if migrating
        with st.expander("Already have payments? (for migrating existing schemes)"):
            mig_cols = st.columns(2)
            with mig_cols[0]:
                gs_paid = st.number_input("Months Already Paid", min_value=0, max_value=36, value=0, step=1, key=f"gs_mig_paid_{fv}")
            with mig_cols[1]:
                gs_deposited = st.number_input("Total Already Deposited (Rs.)", min_value=0.0, step=500.0, format="%.2f", key=f"gs_mig_dep_{fv}")

        # Show success message from previous add
        if st.session_state.get("gs_added_msg"):
            st.success(st.session_state.pop("gs_added_msg"))

        if st.button("Add Scheme", type="primary", use_container_width=True, key="gs_add_btn"):
            if gs_jeweller and gs_monthly > 0:
                deposited = gs_deposited if gs_deposited > 0 else gs_paid * gs_monthly
                mat_date = gs_end_date.isoformat()
                db.add_gold_scheme(gs_jeweller, "", gs_monthly, gs_months, gs_start.isoformat(), gs_note,
                                   months_paid=int(gs_paid), total_deposited=deposited)
                # Also set maturity date
                new_schemes = db.get_gold_schemes()
                if new_schemes:
                    latest = max(new_schemes, key=lambda s: s["id"])
                    db.update_gold_scheme(latest["id"], gs_jeweller, "", gs_monthly, gs_months,
                                          0, gs_start.isoformat(), mat_date,
                                          "Active" if int(gs_paid) < gs_months else "Matured", gs_note)
                # Store success message and clear form for next entry
                st.session_state["gs_added_msg"] = f"Added: {gs_jeweller} — {fmt_inr_full(gs_monthly)}/month for {gs_months} months ({gs_start.strftime('%b %Y')} → {gs_end_date.strftime('%b %Y')})"
                # Increment form version to force fresh widgets with default values
                st.session_state["gs_form_ver"] = fv + 1
                st.rerun()
            else:
                st.error("Please fill in Jeweller Name and Monthly Amount.")

    # ========== OVERVIEW TAB ==========
    with tab_overview:
        if schemes:
            # --- Aggregated Totals ---
            total_deposited = sum(s["total_deposited"] for s in schemes)
            total_expected = sum(s["monthly_amount"] * s["total_months"] for s in schemes)
            total_bonus = sum(s["bonus_amount"] for s in schemes)
            active_count = sum(1 for s in schemes if s["status"] == "Active")
            active_schemes = [s for s in schemes if s["status"] == "Active"]
            monthly_total = sum(s["monthly_amount"] for s in active_schemes)
            remaining_total = total_expected - total_deposited
            overall_progress = (total_deposited / total_expected * 100) if total_expected > 0 else 0
            pct_int = int(overall_progress)

            # ── Hero Summary Banner with SVG Ring ──
            ring_radius = 54
            ring_circumference = 2 * 3.14159 * ring_radius
            ring_offset = ring_circumference * (1 - overall_progress / 100)
            ring_color = COLORS["success"] if overall_progress >= 100 else COLORS["gold_accent"] if overall_progress >= 50 else COLORS["primary_light"]

            st.markdown(f"""
            <div style="background:linear-gradient(135deg, #FFFBEB 0%, #FEF3C7 40%, #FDE68A 100%);
                border:1px solid #F59E0B30;border-radius:18px;padding:28px 32px;margin-bottom:24px;
                display:flex;align-items:center;gap:32px;flex-wrap:wrap;
                box-shadow:0 4px 24px rgba(245,158,11,0.10),0 1px 3px rgba(0,0,0,0.04)">
                <!-- SVG Progress Ring -->
                <div style="flex-shrink:0">
                    <svg width="140" height="140" viewBox="0 0 140 140">
                        <circle cx="70" cy="70" r="{ring_radius}" fill="none" stroke="#E2E8F0" stroke-width="10"/>
                        <circle cx="70" cy="70" r="{ring_radius}" fill="none" stroke="{ring_color}" stroke-width="10"
                            stroke-dasharray="{ring_circumference}" stroke-dashoffset="{ring_offset}"
                            stroke-linecap="round" transform="rotate(-90 70 70)"
                            style="transition:stroke-dashoffset 0.8s ease"/>
                        <text x="70" y="64" text-anchor="middle" font-size="28" font-weight="800"
                            fill="{COLORS['text']}" font-family="Inter,sans-serif">{pct_int}%</text>
                        <text x="70" y="82" text-anchor="middle" font-size="10" font-weight="600"
                            fill="{COLORS['text_muted']}" font-family="Inter,sans-serif" text-transform="uppercase">COMPLETE</text>
                    </svg>
                </div>
                <!-- Key Figures Grid -->
                <div style="flex:1;display:grid;grid-template-columns:repeat(auto-fit,minmax(150px,1fr));gap:16px 28px">
                    <div>
                        <div style="font-size:0.68rem;font-weight:700;text-transform:uppercase;letter-spacing:0.07em;color:{COLORS['gold']};margin-bottom:3px">Active Schemes</div>
                        <div style="font-size:1.65rem;font-weight:800;color:{COLORS['text']};line-height:1.1">{active_count} <span style="font-size:0.85rem;font-weight:500;color:{COLORS['text_muted']}">of {len(schemes)}</span></div>
                    </div>
                    <div>
                        <div style="font-size:0.68rem;font-weight:700;text-transform:uppercase;letter-spacing:0.07em;color:{COLORS['gold']};margin-bottom:3px">Total Deposited</div>
                        <div style="font-size:1.65rem;font-weight:800;color:{COLORS['primary']};line-height:1.1">{fmt_inr(total_deposited)}</div>
                        <div style="font-size:0.75rem;color:{COLORS['text_muted']}">{fmt_inr_words(total_deposited)}</div>
                    </div>
                    <div>
                        <div style="font-size:0.68rem;font-weight:700;text-transform:uppercase;letter-spacing:0.07em;color:{COLORS['gold']};margin-bottom:3px">Remaining</div>
                        <div style="font-size:1.65rem;font-weight:800;color:{COLORS['warning'] if remaining_total > 0 else COLORS['success']};line-height:1.1">{fmt_inr(remaining_total) if remaining_total > 0 else 'Done!'}</div>
                        <div style="font-size:0.75rem;color:{COLORS['text_muted']}">{fmt_inr(monthly_total)}/month commitment</div>
                    </div>
                    <div>
                        <div style="font-size:0.68rem;font-weight:700;text-transform:uppercase;letter-spacing:0.07em;color:{COLORS['gold']};margin-bottom:3px">Redeemable Value</div>
                        <div style="font-size:1.65rem;font-weight:800;color:{COLORS['success']};line-height:1.1">{fmt_inr(total_deposited + total_bonus)}</div>
                        <div style="font-size:0.75rem;color:{COLORS['text_muted']}">{'Includes ' + fmt_inr(total_bonus) + ' bonus' if total_bonus > 0 else 'No bonus set yet'}</div>
                    </div>
                </div>
            </div>
            """, unsafe_allow_html=True)

            # ── Scheme-wise Cards ──
            section_header("Your Schemes", "&#x1f4b3;")

            # Build cards in a 2-column layout using Streamlit
            scheme_pairs = [schemes[i:i+2] for i in range(0, len(schemes), 2)]
            for pair in scheme_pairs:
                cols = st.columns(len(pair))
                for idx, s in enumerate(pair):
                    expected_total = s["monthly_amount"] * s["total_months"]
                    remaining = expected_total - s["total_deposited"]
                    progress = (s["months_paid"] / s["total_months"] * 100) if s["total_months"] > 0 else 0
                    redeemable = s["total_deposited"] + s["bonus_amount"]
                    bar_width = min(progress, 100)
                    bar_color = COLORS["success"] if progress >= 100 else COLORS["gold_accent"] if progress > 50 else COLORS["primary_light"]

                    status_colors = {
                        "Active": (COLORS["success"], COLORS["success_light"]),
                        "Matured": ("#7C3AED", "#F3E8FF"),
                        "Redeemed": (COLORS["primary"], "#EFF6FF"),
                        "Cancelled": (COLORS["danger"], COLORS["danger_light"]),
                    }
                    s_fg, s_bg = status_colors.get(s["status"], (COLORS["text_muted"], COLORS["surface2"]))

                    # Date range
                    start_str = "--"
                    end_str = "--"
                    days_left_str = ""
                    if s["start_date"]:
                        try:
                            start_str = date.fromisoformat(s["start_date"]).strftime("%b %Y")
                        except ValueError:
                            pass
                    if s["maturity_date"]:
                        try:
                            ed = date.fromisoformat(s["maturity_date"])
                            end_str = ed.strftime("%b %Y")
                            dl = (ed - date.today()).days
                            if dl > 0 and s["status"] == "Active":
                                days_left_str = f'<span style="font-size:0.72rem;color:{COLORS["warning"]};font-weight:600;margin-left:6px">({dl}d left)</span>'
                        except ValueError:
                            pass

                    # Last payment
                    payments = db.get_scheme_payments(s["id"])
                    last_pay = payments[0] if payments else None
                    lp_html = f'<span style="color:{COLORS["success"]}">{last_pay["payment_date"]}</span> — {fmt_inr_full(last_pay["amount"])}' if last_pay else f'<span style="color:{COLORS["text_muted"]}">No payments yet</span>'

                    # Mini SVG ring for individual card
                    c_r = 28
                    c_circ = 2 * 3.14159 * c_r
                    c_off = c_circ * (1 - progress / 100)

                    bonus_html = f'<span style="font-weight:600;color:{COLORS["gold"]}">Bonus: {fmt_inr_full(s["bonus_amount"])}</span>' if s["bonus_amount"] > 0 else ''
                    rem_color = COLORS['warning'] if remaining > 0 else COLORS['success']
                    rem_text = fmt_inr_full(remaining) if remaining > 0 else 'Done!'

                    card_html = (
                        f'<div style="background:{COLORS["card"]};border:1px solid {COLORS["card_border"]};border-radius:16px;'
                        f'padding:22px 20px;box-shadow:{COLORS["card_shadow"]};border-top:3px solid {COLORS["gold_accent"]}">'
                        f'<div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:16px">'
                        f'<div style="display:flex;align-items:center;gap:12px">'
                        f'<svg width="64" height="64" viewBox="0 0 64 64">'
                        f'<circle cx="32" cy="32" r="{c_r}" fill="none" stroke="{COLORS["surface2"]}" stroke-width="6"/>'
                        f'<circle cx="32" cy="32" r="{c_r}" fill="none" stroke="{bar_color}" stroke-width="6"'
                        f' stroke-dasharray="{c_circ}" stroke-dashoffset="{c_off}"'
                        f' stroke-linecap="round" transform="rotate(-90 32 32)"/>'
                        f'<text x="32" y="35" text-anchor="middle" font-size="13" font-weight="800"'
                        f' fill="{COLORS["text"]}" font-family="Inter,sans-serif">{s["months_paid"]}</text>'
                        f'</svg>'
                        f'<div>'
                        f'<div style="font-size:1.05rem;font-weight:700;color:{COLORS["text"]};line-height:1.2">{s["jeweller"]}</div>'
                        f'<div style="font-size:0.78rem;color:{COLORS["text_muted"]}">{start_str} &rarr; {end_str} {days_left_str}</div>'
                        f'</div></div>'
                        f'<span style="background:{s_bg};color:{s_fg};padding:3px 12px;border-radius:20px;'
                        f'font-size:0.72rem;font-weight:700;letter-spacing:0.03em">{s["status"]}</span>'
                        f'</div>'
                        f'<div style="margin-bottom:16px">'
                        f'<div style="display:flex;justify-content:space-between;margin-bottom:5px">'
                        f'<span style="font-size:0.72rem;font-weight:600;color:{COLORS["text_muted"]}">{s["months_paid"]} of {s["total_months"]} months</span>'
                        f'<span style="font-size:0.72rem;font-weight:700;color:{bar_color}">{progress:.0f}%</span>'
                        f'</div>'
                        f'<div style="background:{COLORS["surface2"]};border-radius:8px;height:8px;overflow:hidden">'
                        f'<div style="background:linear-gradient(90deg,{COLORS["gold_accent"]},{bar_color});height:100%;width:{bar_width}%;'
                        f'border-radius:8px"></div></div></div>'
                        f'<div style="display:grid;grid-template-columns:1fr 1fr;gap:10px 16px;margin-bottom:14px">'
                        f'<div style="background:{COLORS["surface2"]};border-radius:10px;padding:10px 12px">'
                        f'<div style="font-size:0.65rem;font-weight:600;text-transform:uppercase;letter-spacing:0.06em;color:{COLORS["text_muted"]}">Monthly</div>'
                        f'<div style="font-size:0.95rem;font-weight:700;color:{COLORS["text"]}">{fmt_inr_full(s["monthly_amount"])}</div></div>'
                        f'<div style="background:{COLORS["surface2"]};border-radius:10px;padding:10px 12px">'
                        f'<div style="font-size:0.65rem;font-weight:600;text-transform:uppercase;letter-spacing:0.06em;color:{COLORS["text_muted"]}">Deposited</div>'
                        f'<div style="font-size:0.95rem;font-weight:700;color:{COLORS["primary"]}">{fmt_inr_full(s["total_deposited"])}</div></div>'
                        f'<div style="background:{COLORS["surface2"]};border-radius:10px;padding:10px 12px">'
                        f'<div style="font-size:0.65rem;font-weight:600;text-transform:uppercase;letter-spacing:0.06em;color:{COLORS["text_muted"]}">Remaining</div>'
                        f'<div style="font-size:0.95rem;font-weight:700;color:{rem_color}">{rem_text}</div></div>'
                        f'<div style="background:linear-gradient(135deg,#FFFBEB,#FEF3C7);border-radius:10px;padding:10px 12px;border:1px solid #F59E0B20">'
                        f'<div style="font-size:0.65rem;font-weight:600;text-transform:uppercase;letter-spacing:0.06em;color:{COLORS["gold"]}">Redeemable</div>'
                        f'<div style="font-size:0.95rem;font-weight:700;color:{COLORS["gold"]}">{fmt_inr_full(redeemable)}</div></div>'
                        f'</div>'
                        f'<div style="padding-top:10px;border-top:1px solid {COLORS["card_border"]};'
                        f'font-size:0.78rem;color:{COLORS["text_muted"]};display:flex;justify-content:space-between;align-items:center">'
                        f'<span>Last: {lp_html}</span>{bonus_html}</div>'
                        f'</div>'
                    )

                    with cols[idx]:
                        st.markdown(card_html, unsafe_allow_html=True)

            # ── Analytics Section (two columns: chart + timeline) ──
            all_payments = []
            for s in schemes:
                pays = db.get_scheme_payments(s["id"])
                for p in pays:
                    all_payments.append({
                        "jeweller": s["jeweller"],
                        "month": p["month_number"],
                        "date": p["payment_date"],
                        "amount": p["amount"],
                        "note": p["note"] or "",
                    })

            if all_payments:
                all_payments.sort(key=lambda x: x["date"], reverse=True)

                chart_col, timeline_col = st.columns([1, 1])

                with chart_col:
                    section_header("Deposit Distribution", "&#x1f4ca;")
                    # Donut chart — scheme-wise deposit split
                    scheme_deposits = {}
                    for s in schemes:
                        scheme_deposits[s["jeweller"]] = s["total_deposited"]
                    fig_donut = px.pie(
                        names=list(scheme_deposits.keys()),
                        values=list(scheme_deposits.values()),
                        hole=0.55,
                        color_discrete_sequence=["#F59E0B", "#2563EB", "#059669", "#7C3AED", "#DC2626", "#0D9488", "#DB2777"]
                    )
                    fig_donut.update_traces(
                        textposition="outside", textinfo="label+percent",
                        textfont_size=12, textfont_color=COLORS["text_secondary"],
                        marker=dict(line=dict(color=COLORS["white"], width=2)),
                        hovertemplate="<b>%{label}</b><br>Deposited: Rs. %{value:,.0f}<br>Share: %{percent}<extra></extra>",
                    )
                    fig_donut.update_layout(
                        showlegend=False,
                        paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
                        font=dict(family="Inter,sans-serif", color=COLORS["text_muted"]),
                        margin=dict(t=10, b=10, l=10, r=10), height=300,
                        annotations=[dict(text=f"<b>{fmt_inr(total_deposited)}</b>", x=0.5, y=0.5,
                                         font_size=16, font_color=COLORS["text"], showarrow=False)]
                    )
                    st.plotly_chart(fig_donut, use_container_width=True)

                with timeline_col:
                    section_header("Recent Payments", "&#x1f4c5;")
                    # Show last 8 payments as styled cards instead of table
                    recent = all_payments[:8]
                    for p in recent:
                        st.markdown(f"""
                        <div style="display:flex;align-items:center;gap:12px;padding:8px 12px;margin-bottom:6px;
                            background:{COLORS['card']};border:1px solid {COLORS['card_border']};border-radius:10px;
                            box-shadow:0 1px 2px rgba(0,0,0,0.03)">
                            <div style="width:36px;height:36px;border-radius:50%;background:linear-gradient(135deg,#FEF3C7,#FDE68A);
                                display:flex;align-items:center;justify-content:center;flex-shrink:0;
                                font-size:0.75rem;font-weight:800;color:{COLORS['gold']}">{p['month']}</div>
                            <div style="flex:1;min-width:0">
                                <div style="font-size:0.85rem;font-weight:600;color:{COLORS['text']}">{p['jeweller']}</div>
                                <div style="font-size:0.72rem;color:{COLORS['text_muted']}">{p['date']}{(' — ' + p['note']) if p['note'] else ''}</div>
                            </div>
                            <div style="font-size:0.92rem;font-weight:700;color:{COLORS['success']};white-space:nowrap">{fmt_inr_full(p['amount'])}</div>
                        </div>
                        """, unsafe_allow_html=True)
                    if len(all_payments) > 8:
                        st.markdown(f"<div style='text-align:center;font-size:0.8rem;color:{COLORS['text_muted']};margin-top:4px'>+ {len(all_payments) - 8} more payments</div>", unsafe_allow_html=True)

                # ── Payment Trend Chart ──
                if len(all_payments) > 1:
                    section_header("Monthly Payment Trend", "&#x1f4c8;")
                    pay_df = pd.DataFrame(all_payments)
                    # Aggregate by month
                    pay_df["month_key"] = pd.to_datetime(pay_df["date"]).dt.to_period("M").astype(str)
                    monthly_agg = pay_df.groupby(["month_key", "jeweller"])["amount"].sum().reset_index()
                    monthly_agg = monthly_agg.sort_values("month_key")

                    fig_trend = px.bar(monthly_agg, x="month_key", y="amount", color="jeweller",
                                       labels={"month_key": "Month", "amount": "Amount (Rs.)", "jeweller": "Scheme"},
                                       color_discrete_sequence=["#F59E0B", "#2563EB", "#059669", "#7C3AED", "#DC2626"],
                                       barmode="stack")
                    fig_trend.update_traces(
                        marker_line_width=0,
                        hovertemplate="<b>%{x}</b><br>%{data.name}: Rs. %{y:,.0f}<extra></extra>",
                    )
                    apply_chart_theme(fig_trend, height=280,
                        xaxis=dict(title="", tickangle=-45),
                        yaxis=dict(title=""),
                        legend=dict(orientation="h", y=1.12),
                    )
                    st.plotly_chart(fig_trend, use_container_width=True)

            else:
                st.info("No payments recorded yet. Use the 'Record Payment' tab to add your first payment.")

            # ── Financial Insights ──
            insights = []
            insights.append(f"Total deposited across <strong>{len(schemes)} scheme(s)</strong>: <strong>{fmt_inr_full(total_deposited)}</strong> of {fmt_inr_full(total_expected)} total commitment (<strong>{overall_progress:.1f}%</strong> complete).")
            if monthly_total > 0:
                insights.append(f"Active monthly commitment: <strong>{fmt_inr_full(monthly_total)}</strong>/month across {active_count} scheme(s).")
            if remaining_total > 0 and monthly_total > 0:
                months_est = remaining_total / monthly_total
                insights.append(f"Remaining to pay: <strong>{fmt_inr_full(remaining_total)}</strong> (~{months_est:.0f} months to complete all schemes).")
            if total_bonus > 0:
                bonus_pct = total_bonus / total_deposited * 100 if total_deposited > 0 else 0
                insights.append(f"<span style='color:{COLORS['success']}'>Bonus earned: <strong>{fmt_inr_full(total_bonus)}</strong> ({bonus_pct:.1f}% effective return) — free gold value!</span>")
            else:
                insights.append("No bonus amounts set yet — update scheme details in 'Manage' tab once confirmed by the jeweller.")
            # Average payment regularity
            if all_payments and len(all_payments) >= 2:
                pay_dates = sorted([date.fromisoformat(p["date"]) for p in all_payments])
                gaps = [(pay_dates[i+1] - pay_dates[i]).days for i in range(len(pay_dates)-1)]
                avg_gap = sum(gaps) / len(gaps) if gaps else 0
                if avg_gap > 0:
                    regularity = "Excellent" if avg_gap <= 35 else "Good" if avg_gap <= 45 else "Needs attention"
                    reg_color = COLORS['success'] if avg_gap <= 35 else COLORS['warning'] if avg_gap <= 45 else COLORS['danger']
                    insights.append(f"Payment regularity: <strong style='color:{reg_color}'>{regularity}</strong> (avg. {avg_gap:.0f} days between payments).")
            # Nearing completion
            near_complete = [s for s in schemes if s["status"] == "Active" and s["months_paid"] >= s["total_months"] - 2 and s["months_paid"] < s["total_months"]]
            if near_complete:
                names = ", ".join(f"<strong>{s['jeweller']}</strong> ({s['months_paid']}/{s['total_months']})" for s in near_complete)
                insights.append(f"<span style='color:{COLORS['gold']}'>Nearing maturity: {names} — start planning your gold purchase!</span>")
            # Missed payment detection
            for s in active_schemes:
                if s["start_date"] and s["months_paid"] > 0:
                    try:
                        start_d = date.fromisoformat(s["start_date"])
                        expected_months = max(0, (date.today().year - start_d.year) * 12 + date.today().month - start_d.month)
                        if expected_months > s["months_paid"] + 1:
                            gap = expected_months - s["months_paid"]
                            insights.append(f"<span style='color:{COLORS['danger']}'><strong>{s['jeweller']}</strong>: {gap} payment(s) may be overdue (started {start_d.strftime('%b %Y')}, expected ~{expected_months} months, paid {s['months_paid']}).</span>")
                    except ValueError:
                        pass
            # Net worth context
            all_src = db.get_sources()
            nw = sum(db.get_latest_balance(src["id"]) for src in all_src)
            if nw > 0 and total_deposited > 0:
                gs_pct = total_deposited / nw * 100
                insights.append(f"Gold schemes represent <strong>{gs_pct:.1f}%</strong> of your total net worth.")

            insight_box(insights, "Gold Scheme Insights & Analysis")

        else:
            st.markdown(f"""
            <div style="text-align:center;padding:60px 20px;background:{COLORS['card']};border-radius:16px;
                border:1px dashed {COLORS['card_border']};margin:20px 0">
                <div style="font-size:3rem;margin-bottom:12px">&#x1f4b3;</div>
                <div style="font-size:1.15rem;font-weight:700;color:{COLORS['text']};margin-bottom:6px">No Gold Schemes Yet</div>
                <div style="font-size:0.9rem;color:{COLORS['text_muted']}">Go to the <strong>Add New Scheme</strong> tab to start your first gold savings scheme.</div>
            </div>
            """, unsafe_allow_html=True)

    # ========== RECORD PAYMENT TAB ==========
    with tab_add_payment:
        active_schemes_pay = [s for s in schemes if s["status"] == "Active"]
        if active_schemes_pay:
            scheme_labels = {}
            for s in active_schemes_pay:
                remaining_m = s["total_months"] - s["months_paid"]
                label = f"{s['jeweller']} — Month {s['months_paid'] + 1} of {s['total_months']} ({remaining_m} left)"
                scheme_labels[label] = s

            sel_label = st.selectbox("Select Scheme", list(scheme_labels.keys()), key="gs_pay_select")
            sel_s = scheme_labels[sel_label]

            # Scheme context card with progress
            expected_total = sel_s["monthly_amount"] * sel_s["total_months"]
            sel_progress = (sel_s["months_paid"] / sel_s["total_months"] * 100) if sel_s["total_months"] > 0 else 0
            sel_bar_color = COLORS["success"] if sel_progress >= 100 else COLORS["gold_accent"] if sel_progress > 50 else COLORS["primary_light"]
            sel_remaining = expected_total - sel_s["total_deposited"]

            st.markdown(f"""
            <div style="background:{COLORS['card']};border:1px solid {COLORS['card_border']};border-radius:14px;
                padding:20px;margin:10px 0 18px 0;box-shadow:{COLORS['card_shadow']};border-left:4px solid {COLORS['gold_accent']}">
                <div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:14px">
                    <span style="font-size:1.05rem;font-weight:700;color:{COLORS['text']}">{sel_s['jeweller']}</span>
                    <span style="font-size:0.85rem;font-weight:600;color:{COLORS['gold']}">Month {sel_s['months_paid'] + 1} of {sel_s['total_months']}</span>
                </div>
                <div style="display:flex;gap:24px;margin-bottom:14px;flex-wrap:wrap">
                    <div>
                        <div style="font-size:0.65rem;font-weight:600;text-transform:uppercase;letter-spacing:0.06em;color:{COLORS['text_muted']}">Monthly Amount</div>
                        <div style="font-size:1.1rem;font-weight:700;color:{COLORS['text']}">{fmt_inr_full(sel_s['monthly_amount'])}</div>
                    </div>
                    <div>
                        <div style="font-size:0.65rem;font-weight:600;text-transform:uppercase;letter-spacing:0.06em;color:{COLORS['text_muted']}">Paid So Far</div>
                        <div style="font-size:1.1rem;font-weight:700;color:{COLORS['primary']}">{fmt_inr_full(sel_s['total_deposited'])}</div>
                    </div>
                    <div>
                        <div style="font-size:0.65rem;font-weight:600;text-transform:uppercase;letter-spacing:0.06em;color:{COLORS['text_muted']}">Remaining</div>
                        <div style="font-size:1.1rem;font-weight:700;color:{COLORS['warning']}">{fmt_inr_full(sel_remaining)}</div>
                    </div>
                    <div>
                        <div style="font-size:0.65rem;font-weight:600;text-transform:uppercase;letter-spacing:0.06em;color:{COLORS['text_muted']}">Expected Total</div>
                        <div style="font-size:1.1rem;font-weight:700;color:{COLORS['text_secondary']}">{fmt_inr_full(expected_total)}</div>
                    </div>
                </div>
                <div style="display:flex;align-items:center;gap:10px">
                    <div style="flex:1;background:{COLORS['surface2']};border-radius:6px;height:8px;overflow:hidden">
                        <div style="background:linear-gradient(90deg,{COLORS['gold_accent']},{sel_bar_color});height:100%;width:{min(sel_progress,100)}%;border-radius:6px"></div>
                    </div>
                    <span style="font-size:0.82rem;font-weight:700;color:{sel_bar_color}">{sel_progress:.0f}%</span>
                </div>
            </div>
            """, unsafe_allow_html=True)

            pay_cols = st.columns([1, 1, 2])
            with pay_cols[0]:
                gs_pay_amt = st.number_input("Payment Amount (Rs.)", value=float(sel_s["monthly_amount"]),
                                              min_value=0.01, step=100.0, format="%.2f", key="gs_pay_amt")
            with pay_cols[1]:
                gs_pay_date = st.date_input("Payment Date", value=date.today(), key="gs_pay_date",
                                            help="You can select past dates for backdating payments")
            with pay_cols[2]:
                gs_pay_note = st.text_input("Note (optional)", placeholder="Receipt #, payment mode, etc.", key="gs_pay_note")

            if st.button("Record Payment", type="primary", use_container_width=True, key="gs_pay_btn"):
                db.add_scheme_payment(sel_s["id"], gs_pay_amt, gs_pay_date.isoformat(), gs_pay_note)
                new_month = sel_s["months_paid"] + 1
                if new_month >= sel_s["total_months"]:
                    st.success(f"Month {new_month}/{sel_s['total_months']} paid! Scheme has MATURED!")
                else:
                    st.success(f"Month {new_month}/{sel_s['total_months']} paid — {fmt_inr_full(gs_pay_amt)}")
                st.rerun()

            # Show this scheme's payment history with edit/delete
            payments = db.get_scheme_payments(sel_s["id"])
            if payments:
                st.markdown(f"<div style='height:12px'></div>", unsafe_allow_html=True)
                section_header(f"Payment History — {sel_s['jeweller']}", "&#x1f4dc;")

                # Check if we're editing a payment
                editing_id = st.session_state.get("gs_editing_pay_id")

                for pay in payments:
                    pid = pay["id"]

                    # EDIT MODE for this payment
                    if editing_id == pid:
                        st.markdown(f"""
                        <div style="padding:14px 18px;margin-bottom:8px;background:linear-gradient(135deg,#EEF2FF,#E0E7FF);
                            border:2px solid {COLORS['accent']};border-radius:12px">
                            <div style="font-size:0.72rem;font-weight:700;text-transform:uppercase;letter-spacing:0.06em;
                                color:{COLORS['accent']};margin-bottom:8px">Editing Payment #{pay['month_number'] or '?'}</div>
                        </div>
                        """, unsafe_allow_html=True)
                        edit_cols = st.columns([1, 1, 2])
                        with edit_cols[0]:
                            edit_amt = st.number_input("Amount", value=float(pay["amount"]),
                                                       min_value=0.01, step=100.0, format="%.2f", key=f"edit_amt_{pid}")
                        with edit_cols[1]:
                            edit_date = st.date_input("Date", value=date.fromisoformat(pay["payment_date"]), key=f"edit_date_{pid}")
                        with edit_cols[2]:
                            edit_note = st.text_input("Note", value=pay["note"] or "", key=f"edit_note_{pid}")
                        btn_cols = st.columns([1, 1, 4])
                        with btn_cols[0]:
                            if st.button("Save", type="primary", key=f"save_pay_{pid}", use_container_width=True):
                                db.update_scheme_payment(pid, edit_amt, edit_date.isoformat(), edit_note)
                                st.session_state.pop("gs_editing_pay_id", None)
                                st.rerun()
                        with btn_cols[1]:
                            if st.button("Cancel", key=f"cancel_pay_{pid}", use_container_width=True):
                                st.session_state.pop("gs_editing_pay_id", None)
                                st.rerun()
                    else:
                        # DISPLAY MODE — card with edit/delete buttons
                        card_cols = st.columns([12, 1, 1])
                        with card_cols[0]:
                            st.markdown(f"""
                            <div style="display:flex;align-items:center;gap:12px;padding:10px 14px;
                                background:{COLORS['card']};border:1px solid {COLORS['card_border']};border-radius:10px">
                                <div style="width:38px;height:38px;border-radius:50%;background:linear-gradient(135deg,{COLORS['primary']},#3B82F6);
                                    display:flex;align-items:center;justify-content:center;flex-shrink:0;
                                    font-size:0.82rem;font-weight:800;color:white">{pay['month_number'] or '?'}</div>
                                <div style="flex:1">
                                    <div style="font-size:0.85rem;font-weight:600;color:{COLORS['text']}">{pay['payment_date']}</div>
                                    <div style="font-size:0.72rem;color:{COLORS['text_muted']}">{pay['note'] or 'No note'}</div>
                                </div>
                                <div style="font-size:0.95rem;font-weight:700;color:{COLORS['success']}">{fmt_inr_full(pay['amount'])}</div>
                            </div>
                            """, unsafe_allow_html=True)
                        with card_cols[1]:
                            if st.button("✏️", key=f"editbtn_{pid}", help="Edit this payment"):
                                st.session_state["gs_editing_pay_id"] = pid
                                st.rerun()
                        with card_cols[2]:
                            if st.button("🗑️", key=f"delbtn_{pid}", help="Delete this payment"):
                                st.session_state["gs_confirm_del_pay"] = pid
                                st.rerun()

                        # Delete confirmation inline
                        if st.session_state.get("gs_confirm_del_pay") == pid:
                            st.warning(f"Delete payment #{pay['month_number']} — {fmt_inr_full(pay['amount'])} on {pay['payment_date']}?")
                            del_cols = st.columns([1, 1, 4])
                            with del_cols[0]:
                                if st.button("Yes, Delete", type="primary", key=f"confirm_del_{pid}", use_container_width=True):
                                    db.delete_scheme_payment(pid)
                                    st.session_state.pop("gs_confirm_del_pay", None)
                                    st.rerun()
                            with del_cols[1]:
                                if st.button("Cancel", key=f"cancel_del_{pid}", use_container_width=True):
                                    st.session_state.pop("gs_confirm_del_pay", None)
                                    st.rerun()
        elif schemes:
            st.markdown(f"""
            <div style="text-align:center;padding:40px 20px;background:linear-gradient(135deg,#D1FAE5,#A7F3D0);border-radius:14px;margin:12px 0">
                <div style="font-size:2rem;margin-bottom:8px">&#x2705;</div>
                <div style="font-size:1rem;font-weight:700;color:{COLORS['success']}">All Schemes Complete!</div>
                <div style="font-size:0.85rem;color:{COLORS['text_secondary']}">All your gold schemes have matured. No active schemes to pay.</div>
            </div>
            """, unsafe_allow_html=True)
        else:
            st.info("No schemes yet. Add a scheme first in the 'Add New Scheme' tab.")

    # ========== MANAGE TAB ==========
    with tab_manage:
        if schemes:
            section_header("Edit Scheme Details", "&#x270f;")
            edit_map = {f"{s['jeweller']} — {s['months_paid']}/{s['total_months']} months ({s['status']})": s for s in schemes}
            sel_edit = st.selectbox("Select scheme to edit/remove", [""] + list(edit_map.keys()), key="gs_edit")

            if sel_edit and sel_edit in edit_map:
                s = edit_map[sel_edit]
                with st.form("edit_gold_scheme"):
                    e_cols = st.columns([3, 1, 1])
                    with e_cols[0]:
                        e_jeweller = st.text_input("Jeweller", value=s["jeweller"])
                    with e_cols[1]:
                        e_monthly = st.number_input("Monthly (Rs.)", value=float(s["monthly_amount"]), min_value=100.0, step=500.0, format="%.2f")
                    with e_cols[2]:
                        e_months = st.number_input("Total Months", value=int(s["total_months"]), min_value=1, max_value=36, step=1)
                    e_cols2 = st.columns([1, 1, 1, 1])
                    with e_cols2[0]:
                        e_bonus = st.number_input("Bonus Amount (Rs.)", value=float(s["bonus_amount"]), min_value=0.0, step=500.0, format="%.2f",
                                                  help="Bonus month amount given by jeweller")
                    with e_cols2[1]:
                        e_start = st.date_input("Start Date", value=date.fromisoformat(s["start_date"]) if s["start_date"] else date.today(), key="gs_edit_start")
                    with e_cols2[2]:
                        e_mat = st.date_input("End Date", value=date.fromisoformat(s["maturity_date"]) if s["maturity_date"] else None, key="gs_edit_mat")
                    with e_cols2[3]:
                        status_opts = ["Active", "Matured", "Redeemed", "Cancelled"]
                        e_status = st.selectbox("Status", status_opts, index=status_opts.index(s["status"]) if s["status"] in status_opts else 0)
                    e_note = st.text_input("Note", value=s["note"] or "")
                    btn_cols = st.columns(2)
                    with btn_cols[0]:
                        if st.form_submit_button("Update Scheme", type="primary", use_container_width=True):
                            start_str = e_start.isoformat() if e_start else None
                            mat_str = e_mat.isoformat() if e_mat else None
                            db.update_gold_scheme(s["id"], e_jeweller, "", e_monthly, e_months,
                                                  e_bonus, start_str, mat_str, e_status, e_note)
                            st.success("Updated!")
                            st.rerun()
                    with btn_cols[1]:
                        if st.form_submit_button("Remove Scheme", use_container_width=True):
                            db.deactivate_gold_scheme(s["id"])
                            st.warning("Removed.")
                            st.rerun()
        else:
            st.info("No gold schemes yet. Add your first scheme in the 'Add New Scheme' tab.")
