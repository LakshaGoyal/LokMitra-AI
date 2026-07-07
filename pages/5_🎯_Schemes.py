"""Personalized scheme recommendation page."""

from __future__ import annotations

import uuid

import streamlit as st
from dotenv import load_dotenv

from lib.db import get_all_services, get_database, get_mongo_client
from lib.groq_client import recommend_schemes
from lib.i18n import INDIAN_STATES, get_label, language_selector
from lib.utils import (
    check_rate_limit,
    inject_custom_css,
    render_custom_sidebar,
    render_page_header,
    validate_scheme_form,
)

load_dotenv()

st.set_page_config(page_title="Schemes | LokMitra AI", page_icon="SC", layout="wide")
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
    get_label("schemes_title", lang),
    "Convert a citizen profile into a shortlist of relevant government schemes with a plain-language explanation for each recommendation.",
    "Eligibility matching",
)

occupations = get_label("schemes_occupations", lang)
income_brackets = get_label("schemes_income_brackets", lang)

profile_col, context_col = st.columns([2, 1])
with profile_col:
    with st.form("scheme_intake_form"):
        col1, col2 = st.columns(2)
        with col1:
            age = st.number_input(get_label("schemes_age", lang), min_value=1, max_value=120, value=30, step=1)
            occupation = st.selectbox(get_label("schemes_occupation", lang), options=occupations)
        with col2:
            income_bracket = st.selectbox(get_label("schemes_income", lang), options=income_brackets)
            state = st.selectbox(get_label("schemes_state", lang), options=INDIAN_STATES)
        submitted = st.form_submit_button(get_label("schemes_find", lang), use_container_width=True, type="primary")

with context_col:
    st.markdown("### Matching logic")
    st.info("LokMitra uses seeded scheme data plus your profile details, then asks the model to explain why each scheme may fit.")
    st.caption("Always verify final eligibility on official portals before applying.")

if submitted:
    is_valid, error_msg = validate_scheme_form(int(age), occupation, income_bracket, state)
    if not is_valid:
        st.error(f"Warning: {error_msg}")
    elif db is None:
        st.error("Database connection unavailable. Please try again later.")
    else:
        allowed, wait_time = check_rate_limit("schemes_rate_limit", cooldown_seconds=5.0)
        if not allowed:
            st.warning(f"Please wait {wait_time} seconds before requesting another recommendation.")
        else:
            with st.spinner(get_label("loading", lang)):
                profile = {
                    "age": int(age),
                    "occupation": occupation,
                    "income_bracket": income_bracket,
                    "state": state,
                }
                try:
                    recommendations = recommend_schemes(profile, get_all_services(db), language=lang)
                    st.markdown("### Recommended schemes")
                    with st.container(border=True):
                        st.markdown(
                            f"**Profile:** Age {age}, {occupation}, {income_bracket}, {state}"
                        )
                        st.markdown(recommendations)
                except Exception:
                    st.error(get_label("error_generic", lang))

st.info(
    "Recommendations are AI-generated from general eligibility signals. Confirm final eligibility, deadlines, and documents on official government portals."
)
