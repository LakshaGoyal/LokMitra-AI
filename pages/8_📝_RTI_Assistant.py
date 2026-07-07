"""RTI Draft Assistant page for LokMitra AI.

Helps citizens draft Right to Information (RTI) applications
using AI, with proper formatting and guidance.
"""

import uuid

import streamlit as st
from dotenv import load_dotenv

from lib.groq_client import get_groq_client
from lib.i18n import get_label, language_selector
from lib.utils import check_rate_limit, sanitize_text, inject_custom_css, render_custom_sidebar

load_dotenv()

st.set_page_config(
    page_title="RTI Assistant — LokMitra AI",
    page_icon="📝",
    layout="wide",
)

# --- Unified Custom CSS Injected ---
inject_custom_css()

if "session_id" not in st.session_state:
    st.session_state["session_id"] = str(uuid.uuid4())

lang = language_selector()

# --- Render Custom Sidebar Nav ---
render_custom_sidebar()

# --- Header ---
st.markdown(
    "<h1 style='color:#0F172A;'>📝 RTI Draft Assistant</h1>",
    unsafe_allow_html=True,
)
st.markdown(
    "<p style='color:#64748B;'>"
    "The Right to Information (RTI) Act, 2005 empowers every citizen to seek "
    "information from public authorities. Use this tool to draft an RTI application "
    "with AI assistance.</p>",
    unsafe_allow_html=True,
)

# --- RTI Info Cards ---
st.markdown("---")
info_col1, info_col2, info_col3 = st.columns(3)

with info_col1:
    with st.container(border=True):
        st.markdown(
            "**💰 Application Fee**\n\n"
            "₹10 for Central Government\n\n"
            "Varies for State Governments\n\n"
            "BPL applicants are exempt"
        )

with info_col2:
    with st.container(border=True):
        st.markdown(
            "**⏰ Response Time**\n\n"
            "30 days for normal requests\n\n"
            "48 hours for life/liberty matters\n\n"
            "First appeal within 30 days"
        )

with info_col3:
    with st.container(border=True):
        st.markdown(
            "**📌 Key Points**\n\n"
            "Can be filed in Hindi/English\n\n"
            "No reason required for seeking info\n\n"
            "Online filing via rtionline.gov.in"
        )

st.markdown("---")

# --- RTI Form ---
st.markdown("### 📋 Draft Your RTI Application")

with st.form("rti_form"):
    col1, col2 = st.columns(2)

    with col1:
        applicant_name = st.text_input(
            label="Your Name",
            placeholder="Full name as on ID proof",
            max_chars=100,
        )

        applicant_address = st.text_area(
            label="Your Address",
            placeholder="Complete postal address",
            max_chars=300,
            height=100,
        )

    with col2:
        department = st.text_input(
            label="Government Department / Authority",
            placeholder="e.g., Municipal Corporation, District Collector Office",
            max_chars=200,
        )

        subject = st.text_input(
            label="Subject of RTI",
            placeholder="e.g., Status of road repair work in Ward 15",
            max_chars=200,
        )

    information_sought = st.text_area(
        label="Information You Want to Seek",
        placeholder=(
            "Describe in detail what information you want. Be specific.\n"
            "Example: I want to know:\n"
            "1. The budget allocated for road repair in Ward 15 for 2024-25\n"
            "2. The name of the contractor assigned\n"
            "3. The expected completion date"
        ),
        max_chars=2000,
        height=200,
    )

    time_period = st.text_input(
        label="Time Period (optional)",
        placeholder="e.g., From April 2024 to March 2025",
        max_chars=100,
    )

    submitted = st.form_submit_button(
        "🤖 Generate RTI Draft",
        use_container_width=True,
        type="primary",
    )

if submitted:
    # Validate inputs
    errors = []
    if not applicant_name or len(applicant_name.strip()) < 2:
        errors.append("Please enter your name.")
    if not department or len(department.strip()) < 3:
        errors.append("Please specify the government department.")
    if not information_sought or len(information_sought.strip()) < 10:
        errors.append("Please describe the information you want to seek (at least 10 characters).")

    if errors:
        for err in errors:
            st.error(f"⚠️ {err}")
    else:
        allowed, wait_time = check_rate_limit("rti_rate_limit", cooldown_seconds=5.0)
        if not allowed:
            st.warning(f"Please wait {wait_time} seconds.")
        else:
            with st.spinner("🤖 Drafting your RTI application..."):
                try:
                    client = get_groq_client()

                    clean_name = sanitize_text(applicant_name, 100)
                    clean_address = sanitize_text(applicant_address, 300)
                    clean_dept = sanitize_text(department, 200)
                    clean_subject = sanitize_text(subject, 200)
                    clean_info = sanitize_text(information_sought, 2000)
                    clean_period = sanitize_text(time_period, 100)

                    prompt = f"""Draft a formal Right to Information (RTI) application under the RTI Act, 2005 with the following details:

Applicant Name: {clean_name}
Applicant Address: {clean_address}
Department/Authority: {clean_dept}
Subject: {clean_subject}
Information Sought: {clean_info}
Time Period: {clean_period if clean_period else 'Not specified'}

Generate a properly formatted RTI application in {lang} that includes:
1. Proper heading and addressing
2. Reference to RTI Act, 2005
3. Clearly numbered points of information sought
4. Declaration that the fee of ₹10 is enclosed/paid
5. Statement about preferring information in a specific format
6. Closing with applicant details

Make it professional, formal, and ready to submit. Use proper letter formatting."""

                    response = client.chat.completions.create(
                        model="llama-3.3-70b-versatile",
                        messages=[
                            {
                                "role": "system",
                                "content": f"You are an expert in Indian RTI Act, 2005. Draft formal RTI applications in {lang}.",
                            },
                            {"role": "user", "content": prompt},
                        ],
                        max_tokens=1500,
                        temperature=0.4,
                    )

                    draft = response.choices[0].message.content or ""

                    st.markdown("---")
                    st.markdown("### 📄 Your RTI Application Draft")

                    with st.container(border=True):
                        st.markdown(draft)

                    # Download
                    st.download_button(
                        label="📥 Download RTI Draft",
                        data=draft,
                        file_name="rti_application_draft.txt",
                        mime="text/plain",
                        use_container_width=True,
                    )

                    st.info(
                        "📌 **Next Steps:**\n"
                        "1. Review and customize the draft\n"
                        "2. Pay the ₹10 application fee\n"
                        "3. Submit to the PIO (Public Information Officer) of the concerned department\n"
                        "4. You can also file online at [rtionline.gov.in](https://rtionline.gov.in/)"
                    )

                except ValueError as e:
                    st.error(str(e))
                except Exception:
                    st.error(get_label("error_generic", lang))
