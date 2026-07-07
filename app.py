"""LokMitra AI command center."""

from __future__ import annotations

import uuid

import streamlit as st
from dotenv import load_dotenv

from lib.db import (
    get_all_complaints,
    get_all_feedback,
    get_all_services,
    get_database,
    get_mongo_client,
    is_using_fallback,
    seed_helplines,
    seed_quiz,
    seed_services,
)
from lib.i18n import get_label, language_selector
from lib.utils import escape_html, inject_custom_css, render_custom_sidebar

load_dotenv()

st.set_page_config(
    page_title="LokMitra AI | Civic Command Center",
    page_icon="LM",
    layout="wide",
    initial_sidebar_state="expanded",
)

inject_custom_css()

if "session_id" not in st.session_state:
    st.session_state["session_id"] = str(uuid.uuid4())

lang = language_selector()
render_custom_sidebar()

client = get_mongo_client()
db = get_database(client)
seed_services(db)
seed_helplines(db)
seed_quiz(db)

services = get_all_services(db)
complaints = get_all_complaints(db)
feedback = get_all_feedback(db)
schemes = [s for s in services if s.get("category") == "scheme"]
resolved = sum(1 for c in complaints if c.get("status") == "Resolved")

st.markdown('<div class="gov-banner"></div>', unsafe_allow_html=True)
st.markdown(
    f"""
    <section class="brand-header-container">
        <span class="brand-kicker">PromptWars Hackathon GovTech SaaS</span>
        <h1 class="brand-logo-text">{escape_html(get_label("app_title", lang))}</h1>
        <p class="brand-subtitle-text">{escape_html(get_label("home_description", lang))}</p>
        <div style="display:flex;gap:.7rem;flex-wrap:wrap;margin-top:1.5rem;">
            <span class="lm-pill">Grounded AI workflows</span>
            <span class="lm-pill">MongoDB or sandbox fallback</span>
            <span class="lm-pill">Multilingual responses</span>
            <span class="lm-pill">Deployment ready</span>
        </div>
    </section>
    """,
    unsafe_allow_html=True,
)

stat_cols = st.columns(5)
stats = [
    ("Services", len(services), "Verified civic records"),
    ("Schemes", len(schemes), "Eligibility discovery"),
    ("Complaints", len(complaints), "Tracked reports"),
    ("Resolved", resolved, "Lifecycle completions"),
    ("Feedback", len(feedback), "Experience signals"),
]
for col, (label, value, help_text) in zip(stat_cols, stats):
    with col:
        st.metric(label=label, value=value, help=help_text)

st.markdown("### Civic workflows")

features = [
    ("AI Assistant", "Ask for official-process guidance, document lists, and eligibility steps.", "pages/1_", "AI"),
    ("Services", "Search services and schemes with AI summaries and official links.", "pages/2_", "SV"),
    ("Report Issue", "Submit civic incidents with severity and category classification.", "pages/3_", "RP"),
    ("Track", "Monitor report status through a four-stage timeline.", "pages/4_", "TR"),
    ("Schemes", "Match a citizen profile to relevant public schemes.", "pages/5_", "SC"),
    ("Dashboard", "Inspect civic operations, feedback, and complaint distribution.", "pages/6_", "DB"),
    ("Checklist", "Generate service-specific document readiness checklists.", "pages/7_", "CK"),
    ("RTI Drafting", "Draft formal RTI applications with structured prompts.", "pages/8_", "RT"),
    ("Helplines", "Search emergency and government helpline numbers.", "pages/9_", "HL"),
    ("Compare", "Compare services and documents side by side.", "pages/10_", "CM"),
    ("Civic Quiz", "Learn rights and procedures through guided quiz flows.", "pages/11_", "QZ"),
    ("Feedback", "Capture ratings and product-improvement signals.", "pages/12_", "FB"),
]

pages_root = __import__("pathlib").Path(__file__).resolve().parent / "pages"
for row_start in range(0, len(features), 4):
    cols = st.columns(4)
    for col, (title, desc, prefix, initials) in zip(cols, features[row_start : row_start + 4]):
        with col:
            matches = sorted(pages_root.glob(f"{prefix.split('/')[-1]}*.py"))
            href = f"pages/{matches[0].name}" if matches else None
            st.markdown(
                f"""
                <div class="lm-card lm-feature-card">
                    <div>
                        <span class="lm-icon">{escape_html(initials)}</span>
                        <h3 style="margin:.9rem 0 .35rem;">{escape_html(title)}</h3>
                        <p>{escape_html(desc)}</p>
                    </div>
                </div>
                """,
                unsafe_allow_html=True,
            )
            if href:
                st.page_link(href, label=f"Open {title}", icon=":material/arrow_forward:")

st.markdown("### Operational readiness")
mode = "Sandbox fallback" if is_using_fallback() else "MongoDB connected"
readiness_cols = st.columns(3)
with readiness_cols[0]:
    st.info(f"Storage mode: **{mode}**")
with readiness_cols[1]:
    st.info("AI provider: **Groq LLaMA 3.3** when `GROQ_API_KEY` is configured.")
with readiness_cols[2]:
    st.info("Deployment target: **Streamlit Community Cloud** with zero-setup fallback.")
