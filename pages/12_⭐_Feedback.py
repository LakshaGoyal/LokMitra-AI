"""Feedback page for LokMitra AI.

Allows users to rate their experience and provide feedback
to continuously improve the platform.
"""

import uuid

import streamlit as st
from dotenv import load_dotenv

from lib.db import get_database, get_mongo_client, save_feedback
from lib.i18n import get_label, language_selector
from lib.utils import check_rate_limit, sanitize_text, inject_custom_css, render_custom_sidebar

load_dotenv()

st.set_page_config(
    page_title="Feedback — LokMitra AI",
    page_icon="⭐",
    layout="wide",
)

# --- Unified Custom CSS Injected ---
inject_custom_css()

if "session_id" not in st.session_state:
    st.session_state["session_id"] = str(uuid.uuid4())

lang = language_selector()

# --- Render Custom Sidebar Nav ---
render_custom_sidebar()

client = get_mongo_client()
db = get_database(client)

# --- Header ---
st.markdown(
    "<h1 style='color:#0F172A;'>⭐ Your Feedback Matters</h1>",
    unsafe_allow_html=True,
)
st.markdown(
    "<p style='color:#64748B;'>"
    "Help us improve LokMitra AI! Rate your experience and "
    "share your suggestions.</p>",
    unsafe_allow_html=True,
)
st.markdown("---")

# --- Feedback Form ---
with st.form("feedback_form"):
    # Feature rating
    st.markdown("### How would you rate these features?")

    features = {
        "AI Chat Assistant": "💬",
        "Government Services Explorer": "🏛️",
        "Issue Reporting": "📢",
        "Complaint Tracking": "📋",
        "Scheme Recommendations": "🎯",
        "Overall Experience": "🌟",
    }

    ratings = {}
    cols = st.columns(2)
    for i, (feature, icon) in enumerate(features.items()):
        with cols[i % 2]:
            ratings[feature] = st.slider(
                label=f"{icon} {feature}",
                min_value=1,
                max_value=5,
                value=4,
                key=f"rating_{feature}",
            )
            stars = "⭐" * ratings[feature]
            st.markdown(
                f"<div style='color:#F59E0B; margin-top:-0.5rem; "
                f"margin-bottom:1rem;'>{stars}</div>",
                unsafe_allow_html=True,
            )

    st.markdown("---")

    # Written feedback
    st.markdown("### 💭 Additional Comments")
    comment = st.text_area(
        label="Share your thoughts, suggestions, or report any issues",
        placeholder=(
            "What did you like? What can we improve?\n"
            "Any features you'd like to see added?"
        ),
        max_chars=1000,
        height=120,
        key="feedback_comment",
    )

    # Usefulness
    would_recommend = st.radio(
        label="Would you recommend LokMitra AI to other citizens?",
        options=["Yes, definitely!", "Maybe", "Not yet"],
        horizontal=True,
        key="feedback_recommend",
    )

    submitted = st.form_submit_button(
        "📨 Submit Feedback",
        use_container_width=True,
        type="primary",
    )

if submitted:
    allowed, wait_time = check_rate_limit("feedback_rate_limit", cooldown_seconds=10.0)
    if not allowed:
        st.warning(f"Please wait {wait_time} seconds before submitting again.")
    else:
        clean_comment = sanitize_text(comment, max_length=1000)
        overall_rating = ratings.get("Overall Experience", 4)

        # Save each feature rating
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
            st.balloons()
            st.success("🎉 Thank you for your feedback! Your input helps us improve.")

            # Display thank you message
            with st.container(border=True):
                st.markdown(
                    f"<div style='text-align:center; padding:1rem;'>"
                    f"<div style='font-size:3rem;'>🙏</div>"
                    f"<h3>Thank You!</h3>"
                    f"<p style='color:#64748B;'>"
                    f"Your overall rating: {'⭐' * overall_rating} ({overall_rating}/5)<br>"
                    f"Recommendation: {would_recommend}</p>"
                    f"</div>",
                    unsafe_allow_html=True,
                )
        else:
            st.error("Something went wrong. Please try again.")
