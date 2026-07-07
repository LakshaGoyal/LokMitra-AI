"""Government services explorer page for LokMitra AI."""

from __future__ import annotations

import uuid

import streamlit as st
from dotenv import load_dotenv

from lib.db import get_all_services, get_database, get_mongo_client, search_services
from lib.groq_client import summarize_service
from lib.i18n import get_label, language_selector
from lib.utils import (
    check_rate_limit,
    escape_html,
    inject_custom_css,
    render_custom_sidebar,
    render_empty_state,
    render_page_header,
    sanitize_text,
)

load_dotenv()

st.set_page_config(page_title="Services | LokMitra AI", page_icon="SV", layout="wide")
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
    st.error(get_label("error_generic", lang))

render_page_header(
    get_label("services_title", lang),
    "Search civic services and schemes, inspect eligibility and document requirements, then generate a concise AI brief before moving to the official portal.",
    "Services intelligence",
)

col_search, col_filter = st.columns([3, 1])
with col_search:
    search_query = st.text_input(
        label=get_label("search", lang),
        placeholder="Try PAN, Aadhaar, PM-KISAN, passport, ration card...",
        key="services_search",
    )
with col_filter:
    filter_options = {
        get_label("services_filter_all", lang): "all",
        get_label("services_filter_service", lang): "service",
        get_label("services_filter_scheme", lang): "scheme",
    }
    selected_filter_label = st.selectbox(
        label="Type",
        options=list(filter_options.keys()),
        key="services_category_filter",
    )
selected_filter = filter_options[selected_filter_label]

services = []
if db is not None:
    clean_query = sanitize_text(search_query, max_length=200) if search_query else ""
    services = (
        search_services(db, clean_query, selected_filter)
        if clean_query or selected_filter != "all"
        else get_all_services(db)
    )

if not services and db is not None:
    render_empty_state("No matching services", "Try a broader query or switch the filter to All.")
elif not services:
    st.warning("Unable to load services. Please check the database connection.")

for i, service in enumerate(services):
    category = service.get("category", "service")
    badge = "Service" if category == "service" else "Scheme"
    with st.container(border=True):
        top_cols = st.columns([4, 1])
        with top_cols[0]:
            st.markdown(f"### {escape_html(service.get('name', 'Unknown Service'))}")
            st.markdown(escape_html(service.get("description", "")))
        with top_cols[1]:
            st.markdown(f"<span class='lm-pill'>{badge}</span>", unsafe_allow_html=True)

        meta_cols = st.columns(3)
        with meta_cols[0]:
            docs = service.get("required_documents", [])
            st.metric("Documents", len(docs))
        with meta_cols[1]:
            st.metric("Type", badge)
        with meta_cols[2]:
            st.metric("AI brief", "Ready")

        docs = service.get("required_documents", [])
        if docs:
            with st.expander(get_label("services_required_docs", lang)):
                for doc in docs:
                    st.markdown(f"- {doc}")

        eligibility = service.get("eligibility", "")
        if eligibility:
            with st.expander(get_label("services_eligibility", lang)):
                st.markdown(eligibility)

        link = service.get("how_to_apply_link", "")
        if link:
            st.markdown(f"[{get_label('services_apply_link', lang)}]({link})")

        summary_key = f"summary_{i}"
        if st.button(get_label("learn_more", lang), key=f"btn_summary_{i}"):
            allowed, wait_time = check_rate_limit("services_rate_limit", cooldown_seconds=3.0)
            if not allowed:
                st.warning(f"Please wait {wait_time} seconds before requesting another summary.")
            else:
                with st.spinner(get_label("loading", lang)):
                    st.session_state[summary_key] = summarize_service(service, language=lang)

        if summary_key in st.session_state:
            st.markdown(f"**{get_label('services_ai_summary', lang)}**")
            st.markdown(st.session_state[summary_key])
