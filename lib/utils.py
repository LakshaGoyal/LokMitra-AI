"""Shared utilities and design system helpers for LokMitra AI."""

from __future__ import annotations

import html
import re
import time
import uuid
from pathlib import Path
from typing import Optional

import streamlit as st


def sanitize_text(text: str, max_length: int = 2000) -> str:
    """Sanitize user-provided text input."""
    if not isinstance(text, str):
        return ""
    cleaned = re.sub(r"(?is)<(script|style).*?>.*?</\1>", "", text)
    cleaned = re.sub(r"<[^>]+>", "", cleaned)
    cleaned = re.sub(r"[\x00-\x08\x0b\x0c\x0e-\x1f\x7f]", "", cleaned)
    cleaned = re.sub(r"[ \t]+", " ", cleaned)
    cleaned = re.sub(r"\n{3,}", "\n\n", cleaned)
    cleaned = cleaned.strip()
    return cleaned[:max_length]


def escape_html(value: object) -> str:
    """Escape a value before inserting it into custom HTML markup."""
    return html.escape(str(value), quote=True)


def validate_complaint_form(
    category: str,
    location: str,
    description: str,
) -> tuple[bool, Optional[str]]:
    """Validate the complaint/issue report form inputs."""
    if not category or category.strip() == "":
        return False, "Please select an issue category."
    if not location or len(location.strip()) < 3:
        return False, "Please enter a valid location (at least 3 characters)."
    if len(location.strip()) > 200:
        return False, "Location is too long (maximum 200 characters)."
    if not description or len(description.strip()) < 10:
        return False, "Please provide a description (at least 10 characters)."
    if len(description.strip()) > 2000:
        return False, "Description is too long (maximum 2000 characters)."
    return True, None


def validate_scheme_form(
    age: int,
    occupation: str,
    income_bracket: str,
    state: str,
) -> tuple[bool, Optional[str]]:
    """Validate the scheme recommendation intake form."""
    if not isinstance(age, int) or age < 1 or age > 120:
        return False, "Please enter a valid age (1-120)."
    if not occupation or occupation.strip() == "":
        return False, "Please select an occupation."
    if not income_bracket or income_bracket.strip() == "":
        return False, "Please select an income bracket."
    if not state or state.strip() == "":
        return False, "Please select your state."
    return True, None


def check_rate_limit(
    key: str = "last_api_call",
    cooldown_seconds: float = 2.0,
) -> tuple[bool, float]:
    """Check whether the user is within the rate limit."""
    now = time.time()
    last_call = st.session_state.get(key, 0.0)
    elapsed = now - last_call
    if elapsed < cooldown_seconds:
        return False, round(cooldown_seconds - elapsed, 1)
    st.session_state[key] = now
    return True, 0.0


def generate_complaint_id() -> str:
    """Generate a unique complaint ID in the format ``LM-XXXXXXXX``."""
    return f"LM-{uuid.uuid4().hex[:8].upper()}"


def get_status_display(status: str) -> str:
    """Return a human-friendly status string."""
    status_map = {
        "Submitted": "Submitted",
        "In Review": "In Review",
        "In Progress": "In Progress",
        "Resolved": "Resolved",
    }
    return status_map.get(status, status)


def next_status(current_status: str) -> Optional[str]:
    """Return the next status in the complaint lifecycle."""
    progression = ["Submitted", "In Review", "In Progress", "Resolved"]
    try:
        idx = progression.index(current_status)
    except ValueError:
        return None
    if idx < len(progression) - 1:
        return progression[idx + 1]
    return None


def inject_custom_css() -> None:
    """Inject the LokMitra AI production interface system."""
    st.markdown(
        """
        <style>
        @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&display=swap');

        :root {
            --lm-bg: #f6f7fb;
            --lm-panel: #ffffff;
            --lm-panel-strong: #f8fafc;
            --lm-ink: #111827;
            --lm-muted: #667085;
            --lm-border: #e6e8ef;
            --lm-blue: #1a73e8;
            --lm-blue-strong: #1557c0;
            --lm-green: #0f9d58;
            --lm-amber: #f59e0b;
            --lm-red: #d93025;
            --lm-shadow: 0 18px 50px rgba(15, 23, 42, 0.08);
            --lm-shadow-soft: 0 8px 24px rgba(15, 23, 42, 0.06);
            --lm-radius: 18px;
        }

        header, [data-testid="stHeader"] { background: transparent !important; height: 0 !important; }
        #MainMenu, footer, div[data-testid="stDecoration"], [data-testid="stSidebarNav"] { display: none !important; }

        .block-container {
            max-width: 1280px !important;
            padding: 2.1rem 2rem 3rem !important;
        }

        html, body, [data-testid="stAppViewContainer"] {
            font-family: 'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif !important;
            color: var(--lm-ink) !important;
            background:
                radial-gradient(circle at 12% -10%, rgba(26,115,232,0.14), transparent 34%),
                radial-gradient(circle at 92% 0%, rgba(15,157,88,0.10), transparent 28%),
                linear-gradient(180deg, #fbfcff 0%, var(--lm-bg) 45%, #eef2f7 100%) !important;
        }

        h1, h2, h3, h4 { color: var(--lm-ink) !important; letter-spacing: 0 !important; }
        h1 { font-size: clamp(2rem, 4vw, 4.1rem) !important; line-height: 1.02 !important; font-weight: 800 !important; }
        h2 { font-weight: 760 !important; }
        h3 { font-weight: 700 !important; }
        p, span, label, li { color: var(--lm-muted); }
        a { color: var(--lm-blue) !important; font-weight: 650; text-decoration: none !important; }
        a:hover { color: var(--lm-blue-strong) !important; text-decoration: underline !important; }
        hr { margin: 1.5rem 0 !important; border-color: var(--lm-border) !important; }

        .gov-banner {
            height: 4px;
            width: 100%;
            background: linear-gradient(90deg, #ff8f00, #ffffff 44%, #0f9d58 72%, #1a73e8);
            border-radius: 999px;
            box-shadow: var(--lm-shadow-soft);
            margin: 0 0 1.35rem;
        }

        .brand-header-container {
            min-height: 420px;
            border: 1px solid rgba(230,232,239,0.92);
            border-radius: 28px;
            padding: clamp(1.5rem, 5vw, 4rem);
            background:
                linear-gradient(135deg, rgba(255,255,255,0.92), rgba(248,250,252,0.82)),
                radial-gradient(circle at 85% 12%, rgba(26,115,232,0.16), transparent 28%),
                radial-gradient(circle at 82% 88%, rgba(15,157,88,0.12), transparent 30%);
            box-shadow: var(--lm-shadow);
            overflow: hidden;
            position: relative;
        }
        .brand-header-container:after {
            content: "";
            position: absolute;
            right: 5%;
            top: 12%;
            width: min(34vw, 430px);
            aspect-ratio: 1;
            border: 1px solid rgba(26,115,232,0.14);
            border-radius: 999px;
            background:
                linear-gradient(140deg, rgba(26,115,232,0.08), transparent),
                repeating-linear-gradient(90deg, rgba(17,24,39,0.04) 0 1px, transparent 1px 28px),
                repeating-linear-gradient(0deg, rgba(17,24,39,0.04) 0 1px, transparent 1px 28px);
            z-index: 0;
        }
        .brand-header-container > * { position: relative; z-index: 1; max-width: 760px; }
        .brand-kicker, .lm-kicker {
            display: inline-flex;
            align-items: center;
            gap: .45rem;
            padding: .38rem .7rem;
            border-radius: 999px;
            border: 1px solid rgba(26,115,232,.18);
            background: rgba(26,115,232,.07);
            color: #174ea6 !important;
            font-size: .78rem;
            font-weight: 760;
            text-transform: uppercase;
        }
        .brand-logo-text { margin: 1rem 0 .85rem !important; }
        .brand-subtitle-text {
            color: #475467 !important;
            font-size: clamp(1.02rem, 1.5vw, 1.25rem);
            line-height: 1.7;
        }

        div[data-testid="stVerticalBlockBorder"] {
            border: 1px solid var(--lm-border) !important;
            background: rgba(255,255,255,0.88) !important;
            box-shadow: var(--lm-shadow-soft) !important;
            border-radius: var(--lm-radius) !important;
            padding: 1.15rem !important;
            transition: transform .18s ease, box-shadow .18s ease, border-color .18s ease !important;
        }
        div[data-testid="stVerticalBlockBorder"]:hover {
            transform: translateY(-2px);
            box-shadow: var(--lm-shadow) !important;
            border-color: rgba(26,115,232,0.22) !important;
        }

        .stTextInput input, .stTextArea textarea, .stSelectbox div[data-baseweb="select"], .stNumberInput input {
            border-radius: 12px !important;
            border: 1px solid var(--lm-border) !important;
            background: #ffffff !important;
            color: var(--lm-ink) !important;
            font-size: 0.95rem !important;
            min-height: 2.75rem;
            box-shadow: 0 1px 1px rgba(16,24,40,0.02) !important;
        }
        .stTextInput input:focus, .stTextArea textarea:focus, .stSelectbox div[data-baseweb="select"]:focus-within {
            border-color: var(--lm-blue) !important;
            box-shadow: 0 0 0 4px rgba(26,115,232,0.14) !important;
        }

        .stButton button, .stDownloadButton button, button[kind="primary"], button[kind="secondary"] {
            border-radius: 12px !important;
            min-height: 2.75rem;
            font-weight: 720 !important;
            letter-spacing: 0 !important;
        }
        button[kind="primary"], .stDownloadButton button {
            background: linear-gradient(180deg, #1a73e8, #1557c0) !important;
            color: #fff !important;
            border: none !important;
            box-shadow: 0 10px 24px rgba(26,115,232,.22) !important;
        }
        button[kind="primary"]:hover, .stDownloadButton button:hover {
            background: linear-gradient(180deg, #2b7de9, #174ea6) !important;
            box-shadow: 0 14px 30px rgba(26,115,232,.26) !important;
        }
        button[kind="secondary"] {
            background: #fff !important;
            color: var(--lm-ink) !important;
            border: 1px solid var(--lm-border) !important;
            box-shadow: 0 2px 6px rgba(15,23,42,.04) !important;
        }
        button[kind="secondary"]:hover {
            border-color: rgba(26,115,232,.28) !important;
            color: var(--lm-blue) !important;
        }

        [data-testid="stSidebar"] {
            background: rgba(255,255,255,.94) !important;
            border-right: 1px solid var(--lm-border) !important;
            box-shadow: 12px 0 36px rgba(15,23,42,.04);
        }
        [data-testid="stSidebar"] .stSelectbox label,
        [data-testid="stSidebar"] p,
        [data-testid="stSidebar"] span,
        [data-testid="stSidebar"] h1,
        [data-testid="stSidebar"] h2,
        [data-testid="stSidebar"] h3 {
            color: var(--lm-ink) !important;
        }
        [data-testid="stSidebar"] div[data-testid="stPageLink"] a {
            border-radius: 12px !important;
            padding: .58rem .7rem !important;
            color: #344054 !important;
            font-weight: 660 !important;
            margin: .1rem 0 !important;
            transition: background .16s ease, color .16s ease, transform .16s ease !important;
        }
        [data-testid="stSidebar"] div[data-testid="stPageLink"] a:hover {
            background: #eef4ff !important;
            color: var(--lm-blue) !important;
            transform: translateX(2px);
        }
        [data-testid="stSidebar"] div[data-testid="stPageLink"] a[aria-current="page"] {
            background: #e8f0fe !important;
            color: #174ea6 !important;
        }

        div[data-testid="stMetric"] {
            background: #fff !important;
            border: 1px solid var(--lm-border) !important;
            border-radius: var(--lm-radius) !important;
            padding: 1rem !important;
            box-shadow: var(--lm-shadow-soft) !important;
        }
        div[data-testid="stMetric"] label { color: var(--lm-muted) !important; font-weight: 700 !important; }
        div[data-testid="stMetric"] div[data-testid="stMetricValue"] { color: var(--lm-ink) !important; font-weight: 780 !important; }

        div[data-testid="stChatMessage"] {
            background: #fff !important;
            border: 1px solid var(--lm-border) !important;
            border-radius: 16px !important;
            box-shadow: var(--lm-shadow-soft) !important;
        }
        .stAlert {
            border-radius: 14px !important;
            border: 1px solid var(--lm-border) !important;
            box-shadow: var(--lm-shadow-soft) !important;
        }

        .lm-section { margin: 1.4rem 0; }
        .lm-page-hero {
            border: 1px solid var(--lm-border);
            border-radius: 24px;
            background: linear-gradient(135deg, #fff, #f8fafc);
            box-shadow: var(--lm-shadow-soft);
            padding: clamp(1.25rem, 3vw, 2.25rem);
            margin-bottom: 1.25rem;
        }
        .lm-page-hero h1 {
            font-size: clamp(1.8rem, 3vw, 3.1rem) !important;
            margin: .55rem 0 .7rem !important;
        }
        .lm-page-hero p {
            max-width: 780px;
            font-size: 1.02rem;
            line-height: 1.7;
            margin: 0;
        }
        .lm-card {
            border: 1px solid var(--lm-border);
            border-radius: var(--lm-radius);
            background: rgba(255,255,255,.9);
            box-shadow: var(--lm-shadow-soft);
            padding: 1rem;
        }
        .lm-feature-card {
            min-height: 188px;
            display: flex;
            flex-direction: column;
            justify-content: space-between;
        }
        .lm-icon {
            width: 42px;
            height: 42px;
            border-radius: 12px;
            display: inline-flex;
            align-items: center;
            justify-content: center;
            background: #e8f0fe;
            color: #174ea6 !important;
            font-size: 1rem;
            font-weight: 800;
        }
        .lm-pill {
            display: inline-flex;
            align-items: center;
            gap: .4rem;
            padding: .3rem .62rem;
            border-radius: 999px;
            border: 1px solid var(--lm-border);
            background: #fff;
            color: #344054 !important;
            font-size: .78rem;
            font-weight: 720;
        }
        .lm-muted { color: var(--lm-muted) !important; }
        .lm-empty {
            border: 1px dashed #cbd5e1;
            background: rgba(255,255,255,.72);
            border-radius: 18px;
            padding: 2rem;
            text-align: center;
        }
        .lm-timeline {
            display: grid;
            grid-template-columns: repeat(4, minmax(0, 1fr));
            gap: .8rem;
            margin: 1rem 0;
        }
        .lm-step {
            border: 1px solid var(--lm-border);
            border-radius: 14px;
            padding: .8rem;
            background: #fff;
            min-height: 84px;
        }
        .lm-step.done { border-color: rgba(15,157,88,.35); background: #ecfdf3; }
        .lm-step.active { border-color: rgba(26,115,232,.38); background: #e8f0fe; }
        .pulse-skeleton {
            animation: pulse 1.5s ease-in-out infinite;
            background: linear-gradient(90deg, #eef2f7 25%, #f8fafc 50%, #eef2f7 75%);
            background-size: 200% 100%;
            border-radius: 10px;
        }
        @keyframes pulse {
            0%, 100% { opacity: .66; background-position: 0% 0; }
            50% { opacity: 1; background-position: 100% 0; }
        }
        @media (max-width: 768px) {
            .block-container { padding: 1.3rem 1rem 2rem !important; }
            .brand-header-container { min-height: auto; }
            .brand-header-container:after { display: none; }
            .lm-timeline { grid-template-columns: 1fr; }
        }
        </style>
        """,
        unsafe_allow_html=True,
    )


def render_skeleton_loader(lines: int = 3, height: int = 20) -> None:
    """Render a lightweight skeleton loader."""
    html_str = (
        "<div style='padding:1rem;border:1px solid #e6e8ef;border-radius:18px;"
        "background:rgba(255,255,255,.8);'>"
    )
    for i in range(lines):
        width = "100%" if i < lines - 1 else "60%"
        html_str += (
            f"<div class='pulse-skeleton' style='height:{height}px;width:{width};"
            "margin-bottom:.75rem;'></div>"
        )
    html_str += "</div>"
    st.markdown(html_str, unsafe_allow_html=True)


def render_page_header(title: str, subtitle: str, kicker: str = "LokMitra AI") -> None:
    """Render a reusable page header."""
    st.markdown(
        f"""
        <section class="lm-page-hero">
            <span class="lm-kicker">{escape_html(kicker)}</span>
            <h1>{escape_html(title)}</h1>
            <p>{escape_html(subtitle)}</p>
        </section>
        """,
        unsafe_allow_html=True,
    )


def render_empty_state(title: str, body: str) -> None:
    """Render an accessible empty state block."""
    st.markdown(
        f"""
        <div class="lm-empty" role="status">
            <h3>{escape_html(title)}</h3>
            <p>{escape_html(body)}</p>
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_custom_sidebar() -> None:
    """Render the product sidebar using Streamlit page links."""
    st.sidebar.markdown(
        """
        <div style="padding:.25rem 0 1rem;">
            <div style="display:flex;align-items:center;gap:.7rem;">
                <div style="width:42px;height:42px;border-radius:14px;background:linear-gradient(135deg,#1a73e8,#0f9d58);display:flex;align-items:center;justify-content:center;color:#fff;font-weight:800;">LM</div>
                <div>
                    <div style="font-size:1.05rem;font-weight:820;color:#111827;">LokMitra AI</div>
                    <div style="font-size:.76rem;color:#667085;">Civic intelligence platform</div>
                </div>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    st.sidebar.markdown(
        "<p style='font-size:.72rem;font-weight:800;color:#98a2b3;text-transform:uppercase;margin:.25rem 0 .4rem;'>Workspace</p>",
        unsafe_allow_html=True,
    )
    st.sidebar.page_link("app.py", label="Command Center", icon=":material/home:")

    pages_dir = Path(__file__).resolve().parent.parent / "pages"
    nav_items = [
        ("1_", "AI Assistant", ":material/auto_awesome:"),
        ("2_", "Services", ":material/account_balance:"),
        ("3_", "Report Issue", ":material/report:"),
        ("4_", "Track Complaints", ":material/timeline:"),
        ("5_", "Schemes", ":material/target:"),
        ("6_", "Dashboard", ":material/query_stats:"),
        ("7_", "Checklist", ":material/checklist:"),
        ("8_", "RTI Drafting", ":material/edit_document:"),
        ("9_", "Helplines", ":material/emergency:"),
        ("10_", "Compare", ":material/compare_arrows:"),
        ("11_", "Civic Quiz", ":material/psychology:"),
        ("12_", "Feedback", ":material/star:"),
    ]
    for prefix, label, icon in nav_items:
        matches = sorted(pages_dir.glob(f"{prefix}*.py"))
        if matches:
            st.sidebar.page_link(str(matches[0]), label=label, icon=icon)

    from lib.db import is_using_fallback

    mode_text = "Sandbox Environment" if is_using_fallback() else "Production Cloud DB"
    st.sidebar.markdown("---")
    st.sidebar.markdown(
        f"<div style='padding:.85rem;background:#f8fafc;border:1px solid #e6e8ef;border-radius:14px;'>"
        f"<p style='font-size:.72rem;margin:0;text-transform:uppercase;color:#98a2b3;font-weight:800;'>System Mode</p>"
        f"<p style='font-size:.86rem;margin:.15rem 0 0;font-weight:760;color:#111827;'>{escape_html(mode_text)}</p>"
        f"<div style='display:flex;align-items:center;gap:.4rem;margin-top:.55rem;'>"
        f"<span style='width:7px;height:7px;background:#0f9d58;border-radius:50%;display:inline-block;'></span>"
        f"<span style='color:#0f9d58;font-size:.76rem;font-weight:760;'>Operational</span>"
        f"</div></div>",
        unsafe_allow_html=True,
    )
