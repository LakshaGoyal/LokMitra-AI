"""Feedback page for LokMitra AI."""

from __future__ import annotations

import uuid

import streamlit as st
from dotenv import load_dotenv

from lib.db import get_database, get_mongo_client, save_feedback
from lib.i18n import language_selector
from lib.utils import check_rate_limit, inject_custom_css, render_custom_sidebar, render_page_header, sanitize_text

load_dotenv()

st.set_page_config(page_title="Feedback | LokMitra AI", page_icon="FB", layout="wide")
inject_custom_css()

if "session_id" not in st.session_state:
    st.session_state["session_id"] = str(uuid.uuid4())

language_selector()
render_custom_sidebar()

client = get_mongo_client()
db = get_database(client)

render_page_header(
    "Feedback & Support",
    "Rate the civic workflows and share product feedback. Signals are stored through the same MongoDB or sandbox adapter as the rest of the app.",
    "Quality loop",
)

with st.form("feedback_form"):
    st.markdown("### Rate core workflows")
    features = {
        "AI Chat Assistant": "AI",
        "Government Services Explorer": "Services",
        "Issue Reporting": "Reports",
        "Complaint Tracking": "Tracking",
        "Scheme Recommendations": "Schemes",
        "Overall Experience": "Overall",
    }

    ratings = {}
    cols = st.columns(2)
    for i, (feature, label) in enumerate(features.items()):
        with cols[i % 2]:
            ratings[feature] = st.slider(label=f"{label}: {feature}", min_value=1, max_value=5, value=4)

    comment = st.text_area(
        "Additional comments",
        placeholder="What worked well? What confused you? What should the next version include?",
        max_chars=1000,
        height=120,
    )
    would_recommend = st.radio(
        "Would you recommend LokMitra AI to other citizens?",
        ["Yes, definitely", "Maybe", "Not yet"],
        horizontal=True,
    )
    submitted = st.form_submit_button("Submit feedback", use_container_width=True, type="primary")

if submitted:
    allowed, wait_time = check_rate_limit("feedback_rate_limit", cooldown_seconds=10.0)
    if not allowed:
        st.warning(f"Please wait {wait_time} seconds before submitting again.")
    else:
        clean_comment = sanitize_text(comment, max_length=1000)
        overall_rating = ratings.get("Overall Experience", 4)
        all_saved = True
        for feature, rating in ratings.items():
            success = save_feedback(
                db,
                st.session_state["session_id"],
                page=feature,
                rating=rating,
                comment=clean_comment if feature == "Overall Experience" else "",
            )
            if not success:
                all_saved = False

        if all_saved:
            st.success("Thank you. Your feedback has been recorded.")
            with st.container(border=True):
                st.metric("Overall rating", f"{overall_rating}/5", would_recommend)
                if clean_comment:
                    st.markdown(f"**Comment:** {clean_comment}")
        else:
            st.error("Something went wrong. Please try again.")
