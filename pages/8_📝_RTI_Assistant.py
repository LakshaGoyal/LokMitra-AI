"""RTI draft assistant page."""

from __future__ import annotations

import uuid

import streamlit as st
from dotenv import load_dotenv

from lib.groq_client import get_groq_client
from lib.i18n import get_label, language_selector
from lib.utils import check_rate_limit, inject_custom_css, render_custom_sidebar, render_page_header, sanitize_text

load_dotenv()

st.set_page_config(page_title="RTI Drafting | LokMitra AI", page_icon="RT", layout="wide")
inject_custom_css()

if "session_id" not in st.session_state:
    st.session_state["session_id"] = str(uuid.uuid4())

lang = language_selector()
render_custom_sidebar()

render_page_header(
    "RTI Drafting",
    "Generate a formal Right to Information application with structured questions, applicant details, fee language, and a review-ready downloadable draft.",
    "Legal drafting assistant",
)

info_col1, info_col2, info_col3 = st.columns(3)
with info_col1:
    st.info("Application fee: Rs 10 for Central Government. BPL applicants are exempt.")
with info_col2:
    st.info("Response time: 30 days normally, 48 hours for life or liberty matters.")
with info_col3:
    st.info("Official filing: use rtionline.gov.in for eligible public authorities.")

with st.form("rti_form"):
    col1, col2 = st.columns(2)
    with col1:
        applicant_name = st.text_input("Your name", placeholder="Full name as on ID proof", max_chars=100)
        applicant_address = st.text_area("Your address", placeholder="Complete postal address", max_chars=300, height=100)
    with col2:
        department = st.text_input("Government department / authority", placeholder="Municipal Corporation, District Collector Office", max_chars=200)
        subject = st.text_input("Subject of RTI", placeholder="Status of road repair work in Ward 15", max_chars=200)

    information_sought = st.text_area(
        "Information you want to seek",
        placeholder="List specific records, dates, budgets, contracts, file movement, or responsible office details.",
        max_chars=2000,
        height=200,
    )
    time_period = st.text_input("Time period (optional)", placeholder="April 2024 to March 2025", max_chars=100)

    submitted = st.form_submit_button("Generate RTI draft", use_container_width=True, type="primary")

if submitted:
    errors = []
    if not applicant_name or len(applicant_name.strip()) < 2:
        errors.append("Please enter your name.")
    if not department or len(department.strip()) < 3:
        errors.append("Please specify the government department.")
    if not information_sought or len(information_sought.strip()) < 10:
        errors.append("Please describe the information you want to seek.")

    if errors:
        for err in errors:
            st.error(f"Warning: {err}")
    else:
        allowed, wait_time = check_rate_limit("rti_rate_limit", cooldown_seconds=5.0)
        if not allowed:
            st.warning(f"Please wait {wait_time} seconds.")
        else:
            with st.spinner("Drafting your RTI application..."):
                try:
                    client = get_groq_client()
                    clean_name = sanitize_text(applicant_name, 100)
                    clean_address = sanitize_text(applicant_address, 300)
                    clean_dept = sanitize_text(department, 200)
                    clean_subject = sanitize_text(subject, 200)
                    clean_info = sanitize_text(information_sought, 2000)
                    clean_period = sanitize_text(time_period, 100)

                    prompt = f"""Draft a formal Right to Information application under the RTI Act, 2005.

Applicant Name: {clean_name}
Applicant Address: {clean_address}
Department/Authority: {clean_dept}
Subject: {clean_subject}
Information Sought: {clean_info}
Time Period: {clean_period if clean_period else 'Not specified'}

Output language: {lang}

Requirements:
1. Use a formal letter format.
2. Mention the RTI Act, 2005.
3. Number each information request clearly.
4. Include standard Rs 10 fee language.
5. Ask for information by post/email where appropriate.
6. Include applicant name, address, date placeholder, and signature placeholder.
7. Do not invent officer names, phone numbers, file numbers, or fees beyond standard RTI guidance."""

                    response = client.chat.completions.create(
                        model="llama-3.3-70b-versatile",
                        messages=[
                            {
                                "role": "system",
                                "content": f"You draft accurate Indian RTI applications in {lang}. Stay formal, specific, and do not invent facts.",
                            },
                            {"role": "user", "content": prompt},
                        ],
                        max_tokens=1500,
                        temperature=0.35,
                    )
                    draft = response.choices[0].message.content or ""
                    st.markdown("### RTI application draft")
                    with st.container(border=True):
                        st.markdown(draft)
                    st.download_button(
                        label="Download RTI draft",
                        data=draft,
                        file_name="rti_application_draft.txt",
                        mime="text/plain",
                        use_container_width=True,
                    )
                    st.info("Review the draft, add date/signature, pay the applicable fee, and submit to the Public Information Officer or through rtionline.gov.in where supported.")
                except ValueError as e:
                    st.error(str(e))
                except Exception:
                    st.error(get_label("error_generic", lang))
