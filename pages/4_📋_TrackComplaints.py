"""Track complaints page for LokMitra AI."""

from __future__ import annotations

import uuid

import streamlit as st
from dotenv import load_dotenv

from lib.db import (
    get_complaint_by_id,
    get_complaints_by_session,
    get_database,
    get_mongo_client,
    update_complaint_status,
)
from lib.i18n import get_label, language_selector
from lib.utils import (
    escape_html,
    inject_custom_css,
    next_status,
    render_custom_sidebar,
    render_empty_state,
    render_page_header,
    sanitize_text,
)

load_dotenv()

st.set_page_config(page_title="Track Complaints | LokMitra AI", page_icon="TR", layout="wide")
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
    get_label("track_title", lang),
    "Search a complaint ID or review recent session reports. The timeline exposes the same four lifecycle stages used by the civic operations dashboard.",
    "Lifecycle tracking",
)


def _render_timeline(status: str, lang: str) -> None:
    labels = {
        "Submitted": get_label("track_status_submitted", lang),
        "In Review": get_label("track_status_in_review", lang),
        "In Progress": get_label("track_status_in_progress", lang),
        "Resolved": get_label("track_status_resolved", lang),
    }
    statuses = ["Submitted", "In Review", "In Progress", "Resolved"]
    try:
        current_idx = statuses.index(status)
    except ValueError:
        current_idx = 0
    html = '<div class="lm-timeline">'
    for idx, item in enumerate(statuses):
        cls = "done" if idx < current_idx else "active" if idx == current_idx else ""
        state = "Complete" if idx < current_idx else "Current" if idx == current_idx else "Pending"
        html += (
            f'<div class="lm-step {cls}">'
            f"<strong>{escape_html(labels.get(item, item))}</strong>"
            f"<p style='margin:.35rem 0 0;'>{escape_html(state)}</p>"
            "</div>"
        )
    html += "</div>"
    st.markdown(html, unsafe_allow_html=True)


def _render_complaint_card(complaint: dict, lang: str, db, show_simulate: bool = True) -> None:
    cid = complaint.get("complaint_id", "N/A")
    status = complaint.get("status", "Unknown")
    with st.container(border=True):
        top = st.columns([3, 1])
        with top[0]:
            st.markdown(f"### {escape_html(cid)}")
            st.caption(complaint.get("ai_summary", "Complaint record"))
        with top[1]:
            st.metric(get_label("track_status", lang), status)

        _render_timeline(status, lang)

        detail_cols = st.columns(4)
        with detail_cols[0]:
            st.metric(get_label("track_category", lang), complaint.get("category", "N/A"))
        with detail_cols[1]:
            st.metric("Severity", complaint.get("severity", "Medium"))
        with detail_cols[2]:
            st.metric(get_label("track_location", lang), complaint.get("location", "N/A"))
        with detail_cols[3]:
            created = complaint.get("created_at", "N/A")
            if isinstance(created, str) and "T" in created:
                created = created.split("T")[0]
            st.metric(get_label("track_created", lang), created)

        if show_simulate and status != "Resolved" and db is not None:
            new_status = next_status(status)
            if new_status and st.button(get_label("track_simulate", lang), key=f"simulate_{cid}"):
                if update_complaint_status(db, cid, new_status):
                    st.success(f"Status updated to: {new_status}")
                    st.rerun()
                else:
                    st.error(get_label("error_generic", lang))


search_col, button_col = st.columns([3, 1])
with search_col:
    search_id = st.text_input(
        label=get_label("track_search_label", lang),
        placeholder="LM-XXXXXXXX",
        max_chars=20,
        key="track_search_input",
    )
with button_col:
    st.write("")
    search_clicked = st.button(
        get_label("track_search_button", lang),
        key="track_search_btn",
        use_container_width=True,
        type="primary",
    )

if search_clicked and search_id:
    clean_id = sanitize_text(search_id, max_length=20).strip()
    if db is not None:
        complaint = get_complaint_by_id(db, clean_id)
        if complaint:
            _render_complaint_card(complaint, lang, db)
        else:
            st.warning(f"No complaint found with ID: `{clean_id}`. Please check the ID and try again.")
    else:
        st.error("Database connection unavailable.")

st.markdown("### Recent reports")
if db is not None:
    session_complaints = get_complaints_by_session(db, st.session_state["session_id"])
    if session_complaints:
        for complaint in session_complaints:
            _render_complaint_card(complaint, lang, db)
    else:
        render_empty_state("No session complaints", get_label("track_no_complaints", lang))
else:
    st.warning("Database connection unavailable.")
