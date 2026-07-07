"""Internationalization helpers for LokMitra AI.

The app currently keeps business workflows in English while allowing the
assistant to answer in a selected language. UI labels are intentionally concise
and ASCII-safe for predictable Streamlit Cloud rendering.
"""

from __future__ import annotations

from typing import Optional

import streamlit as st


SUPPORTED_LANGUAGES: dict[str, str] = {
    "English": "English",
    "Hindi": "Hindi",
    "Marathi": "Marathi",
    "Tamil": "Tamil",
    "Bengali": "Bengali",
}


_BASE_LABELS: dict[str, str | list[str]] = {
    "app_title": "LokMitra AI",
    "app_subtitle": "Premium AI civic platform for Indian public services.",
    "greeting": "How can LokMitra help you move a civic task forward today?",
    "language_label": "Response language",
    "loading": "Processing securely...",
    "error_generic": "Something went wrong. Please try again.",
    "success": "Success",
    "submit": "Submit",
    "search": "Search services, schemes, documents...",
    "back": "Back",
    "learn_more": "Generate AI brief",
    "home_title": "LokMitra AI",
    "home_description": "A modern GovTech command center for public services, grievance workflows, scheme discovery, RTI drafting, emergency help, and civic learning.",
    "chip_birth_cert": "Birth certificate documents",
    "chip_streetlight": "Report a broken streetlight",
    "chip_complaint": "Track my complaint",
    "card_assistant": "AI Civic Assistant",
    "card_assistant_desc": "Ask grounded questions about Indian services, documents, eligibility, and next steps.",
    "card_services": "Services Intelligence",
    "card_services_desc": "Search government services and schemes with documents, eligibility, and official links.",
    "card_report": "Issue Reporting",
    "card_report_desc": "Submit civic issues with AI classification, severity, and summaries.",
    "card_track": "Complaint Tracking",
    "card_track_desc": "Follow complaint status through a clear lifecycle timeline.",
    "card_schemes": "Scheme Matching",
    "card_schemes_desc": "Get personalized scheme recommendations from profile details.",
    "assistant_title": "AI Civic Assistant",
    "assistant_placeholder": "Ask about documents, eligibility, procedures, RTI, or civic issues...",
    "assistant_thinking": "LokMitra is grounding the answer...",
    "services_title": "Services Intelligence",
    "services_filter_all": "All",
    "services_filter_service": "Services",
    "services_filter_scheme": "Schemes",
    "services_required_docs": "Required documents",
    "services_eligibility": "Eligibility",
    "services_apply_link": "Official application link",
    "services_ai_summary": "AI brief",
    "report_title": "Report a Civic Issue",
    "report_category": "Issue category",
    "report_location": "Location or area",
    "report_description": "Issue description",
    "report_photo": "Attach photo evidence (optional)",
    "report_submit": "Submit report",
    "report_success": "Issue reported successfully.",
    "report_complaint_id": "Complaint ID",
    "report_save_id": "Save this ID. You will need it to track the complaint.",
    "report_categories": [
        "Roads & Potholes",
        "Street Lights",
        "Water Supply",
        "Garbage & Sanitation",
        "Drainage & Sewage",
        "Public Safety",
        "Other",
    ],
    "track_title": "Complaint Tracking",
    "track_search_label": "Enter complaint ID",
    "track_search_button": "Search",
    "track_session_title": "Recent reports from this session",
    "track_no_complaints": "No complaints found for this session yet.",
    "track_status_submitted": "Submitted",
    "track_status_in_review": "In Review",
    "track_status_in_progress": "In Progress",
    "track_status_resolved": "Resolved",
    "track_simulate": "Simulate next step",
    "track_complaint_id": "Complaint ID",
    "track_category": "Category",
    "track_location": "Location",
    "track_created": "Reported on",
    "track_status": "Status",
    "track_ai_summary": "AI summary",
    "schemes_title": "Scheme Matching",
    "schemes_age": "Age",
    "schemes_occupation": "Occupation",
    "schemes_income": "Annual income bracket",
    "schemes_state": "State",
    "schemes_find": "Find matching schemes",
    "schemes_results": "Recommended schemes",
    "schemes_why": "Why this fits",
    "schemes_occupations": [
        "Farmer",
        "Student",
        "Salaried Employee",
        "Self-Employed / Business",
        "Daily Wage Worker",
        "Homemaker",
        "Retired / Senior Citizen",
        "Unemployed",
        "Other",
    ],
    "schemes_income_brackets": [
        "Below Rs 1 Lakh",
        "Rs 1 Lakh - Rs 3 Lakh",
        "Rs 3 Lakh - Rs 6 Lakh",
        "Rs 6 Lakh - Rs 10 Lakh",
        "Rs 10 Lakh - Rs 18 Lakh",
        "Above Rs 18 Lakh",
    ],
}


_LABELS: dict[str, dict[str, str | list[str]]] = {
    language: dict(_BASE_LABELS) for language in SUPPORTED_LANGUAGES
}


INDIAN_STATES: list[str] = [
    "Andhra Pradesh",
    "Arunachal Pradesh",
    "Assam",
    "Bihar",
    "Chhattisgarh",
    "Goa",
    "Gujarat",
    "Haryana",
    "Himachal Pradesh",
    "Jharkhand",
    "Karnataka",
    "Kerala",
    "Madhya Pradesh",
    "Maharashtra",
    "Manipur",
    "Meghalaya",
    "Mizoram",
    "Nagaland",
    "Odisha",
    "Punjab",
    "Rajasthan",
    "Sikkim",
    "Tamil Nadu",
    "Telangana",
    "Tripura",
    "Uttar Pradesh",
    "Uttarakhand",
    "West Bengal",
    "Delhi",
    "Jammu & Kashmir",
    "Ladakh",
    "Puducherry",
    "Chandigarh",
    "Andaman & Nicobar Islands",
    "Lakshadweep",
    "Dadra & Nagar Haveli and Daman & Diu",
]


def get_label(key: str, language: Optional[str] = None) -> str | list[str]:
    """Return a translated UI label for the given key."""
    if language is None:
        language = st.session_state.get("language", "English")
    lang_labels = _LABELS.get(language, _LABELS["English"])
    return lang_labels.get(key, _LABELS["English"].get(key, key))


def language_selector() -> str:
    """Render and persist the response-language selector."""
    if "language" not in st.session_state:
        st.session_state["language"] = "English"

    options = list(SUPPORTED_LANGUAGES.keys())
    display_names = [
        f"{key} ({native})" if key != native else key
        for key, native in SUPPORTED_LANGUAGES.items()
    ]

    with st.sidebar:
        selected_idx = st.selectbox(
            label=get_label("language_label"),
            options=range(len(options)),
            format_func=lambda i: display_names[i],
            index=options.index(st.session_state["language"]),
            key="language_selector_widget",
        )
        st.session_state["language"] = options[selected_idx]

    return st.session_state["language"]
