"""Report a civic issue page for LokMitra AI."""

from __future__ import annotations

import uuid

import streamlit as st
from dotenv import load_dotenv

from lib.db import get_database, get_mongo_client, insert_complaint
from lib.groq_client import classify_issue
from lib.i18n import get_label, language_selector
from lib.utils import (
    check_rate_limit,
    generate_complaint_id,
    inject_custom_css,
    render_custom_sidebar,
    render_page_header,
    sanitize_text,
    validate_complaint_form,
)

load_dotenv()

st.set_page_config(page_title="Report Issue | LokMitra AI", page_icon="RP", layout="wide")
inject_custom_css()

if "session_id" not in st.session_state:
    st.session_state["session_id"] = str(uuid.uuid4())

lang = language_selector()
render_custom_sidebar()

db = None
try:
    client = get_mongo_client()
    db = get_database(client)
except Exception:
    pass

render_page_header(
    get_label("report_title", lang),
    "Capture a municipal issue with location, description, and optional photo metadata. LokMitra classifies severity and creates a trackable complaint record.",
    "Civic operations",
)

left, right = st.columns([2, 1])
with left:
    categories = get_label("report_categories", lang)
    with st.form("report_issue_form", clear_on_submit=True):
        category = st.selectbox(
            label=get_label("report_category", lang),
            options=categories,
            index=0,
            key="issue_category",
        )
        location = st.text_input(
            label=get_label("report_location", lang),
            placeholder="MG Road, Sector 15, near City Mall",
            max_chars=200,
            key="issue_location",
        )
        description = st.text_area(
            label=get_label("report_description", lang),
            placeholder="What is the issue, how long has it existed, and is there a safety risk?",
            max_chars=2000,
            height=160,
            key="issue_description",
        )
        uploaded_file = st.file_uploader(
            label=get_label("report_photo", lang),
            type=["jpg", "jpeg", "png"],
            key="issue_photo",
        )
        submitted = st.form_submit_button(
            get_label("report_submit", lang),
            use_container_width=True,
            type="primary",
        )

with right:
    st.markdown("### Intake quality")
    st.info("Add a precise landmark, public-safety impact, and duration to improve classification quality.")
    st.markdown("### Data handling")
    st.caption("Uploaded images are not persisted in this demo. Only metadata is stored with the complaint.")

if submitted:
    clean_location = sanitize_text(location, max_length=200)
    clean_description = sanitize_text(description, max_length=2000)
    is_valid, error_msg = validate_complaint_form(category, clean_location, clean_description)

    if not is_valid:
        st.error(f"Warning: {error_msg}")
    elif db is None:
        st.error("Database connection unavailable. Please try again later.")
    else:
        allowed, wait_time = check_rate_limit("report_rate_limit", cooldown_seconds=5.0)
        if not allowed:
            st.warning(f"Please wait {wait_time} seconds before submitting another report.")
        else:
            with st.spinner(get_label("loading", lang)):
                ai_result = classify_issue(clean_description)
                photo_metadata = None
                if uploaded_file is not None:
                    photo_metadata = {
                        "filename": uploaded_file.name,
                        "size_bytes": uploaded_file.size,
                        "type": uploaded_file.type,
                    }

                complaint_id = generate_complaint_id()
                complaint = {
                    "complaint_id": complaint_id,
                    "session_id": st.session_state["session_id"],
                    "category": category,
                    "location": clean_location,
                    "description": clean_description,
                    "status": "Submitted",
                    "severity": ai_result.get("severity", "Medium"),
                    "ai_category": ai_result.get("category", category),
                    "ai_summary": ai_result.get("summary", clean_description[:100]),
                    "photo_metadata": photo_metadata,
                }

                success = insert_complaint(db, complaint)

                if success:
                    st.session_state.setdefault("complaint_ids", []).append(complaint_id)
                    st.success(get_label("report_success", lang))
                    with st.container(border=True):
                        st.markdown(f"### {get_label('report_complaint_id', lang)}: `{complaint_id}`")
                        st.info(get_label("report_save_id", lang))
                        col_info1, col_info2, col_info3 = st.columns(3)
                        with col_info1:
                            st.metric(get_label("track_category", lang), category)
                        with col_info2:
                            st.metric("Severity", ai_result.get("severity", "Medium"))
                        with col_info3:
                            st.metric(get_label("track_status", lang), "Submitted")
                        st.markdown(f"**{get_label('track_location', lang)}:** {clean_location}")
                        st.markdown(f"**{get_label('track_ai_summary', lang)}:** {ai_result.get('summary', 'N/A')}")
                else:
                    st.error(get_label("error_generic", lang))
