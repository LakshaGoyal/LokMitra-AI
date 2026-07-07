"""Scheme Comparison Tool page for LokMitra AI.

Allows citizens to compare multiple government schemes
side-by-side to make informed decisions.
"""

import uuid

import streamlit as st
from dotenv import load_dotenv

from lib.db import get_all_services, get_database, get_mongo_client, seed_services
from lib.i18n import get_label, language_selector
from lib.utils import inject_custom_css, render_custom_sidebar

load_dotenv()

st.set_page_config(
    page_title="Compare Schemes — LokMitra AI",
    page_icon="🔄",
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
seed_services(db)

# --- Header ---
st.markdown(
    "<h1 style='color:#0F172A;'>🔄 Compare Schemes & Services</h1>",
    unsafe_allow_html=True,
)
st.markdown(
    "<p style='color:#64748B;'>"
    "Select 2 or 3 schemes to compare them side-by-side. "
    "Understand eligibility, documents, and benefits at a glance.</p>",
    unsafe_allow_html=True,
)
st.markdown("---")

# --- Load Services ---
services = get_all_services(db)
service_names = [s.get("name", "Unknown") for s in services]

# --- Selection ---
selected_names = st.multiselect(
    label="Select schemes/services to compare (2-3)",
    options=service_names,
    max_selections=3,
    key="compare_selection",
)

if len(selected_names) < 2:
    st.info("👆 Please select at least 2 schemes or services to compare.")
else:
    selected_services = [s for s in services if s.get("name") in selected_names]

    st.markdown("---")
    st.markdown("### 📊 Side-by-Side Comparison")

    # Header row
    cols = st.columns(len(selected_services) + 1)
    with cols[0]:
        st.markdown("**Attribute**")
    for i, svc in enumerate(selected_services):
        with cols[i + 1]:
            icon = "🏛️" if svc.get("category") == "service" else "🎯"
            st.markdown(f"**{icon} {svc.get('name', 'N/A')}**")

    st.markdown("---")

    # Category Row
    cols = st.columns(len(selected_services) + 1)
    with cols[0]:
        st.markdown("**Type**")
    for i, svc in enumerate(selected_services):
        with cols[i + 1]:
            cat = svc.get("category", "N/A").capitalize()
            color = "#2563EB" if cat == "Service" else "#059669"
            st.markdown(
                f"<span style='background:{color}; color:white; "
                f"padding:0.2rem 0.6rem; border-radius:8px; "
                f"font-size:0.8rem;'>{cat}</span>",
                unsafe_allow_html=True,
            )

    # Description Row
    cols = st.columns(len(selected_services) + 1)
    with cols[0]:
        st.markdown("**Description**")
    for i, svc in enumerate(selected_services):
        with cols[i + 1]:
            desc = svc.get("description", "N/A")
            st.markdown(
                f"<div style='font-size:0.9rem; color:#475569;'>{desc[:200]}...</div>"
                if len(desc) > 200
                else f"<div style='font-size:0.9rem; color:#475569;'>{desc}</div>",
                unsafe_allow_html=True,
            )

    st.markdown("---")

    # Eligibility Row
    cols = st.columns(len(selected_services) + 1)
    with cols[0]:
        st.markdown("**✅ Eligibility**")
    for i, svc in enumerate(selected_services):
        with cols[i + 1]:
            st.markdown(svc.get("eligibility", "N/A"))

    st.markdown("---")

    # Documents Row
    cols = st.columns(len(selected_services) + 1)
    with cols[0]:
        st.markdown("**📄 Documents**")
    for i, svc in enumerate(selected_services):
        with cols[i + 1]:
            docs = svc.get("required_documents", [])
            for doc in docs:
                st.markdown(f"• {doc}")
            st.markdown(f"**Total: {len(docs)} documents**")

    st.markdown("---")

    # Apply Link Row
    cols = st.columns(len(selected_services) + 1)
    with cols[0]:
        st.markdown("**🔗 Apply Link**")
    for i, svc in enumerate(selected_services):
        with cols[i + 1]:
            link = svc.get("how_to_apply_link", "N/A")
            if link and link != "N/A":
                st.markdown(f"[Apply Here]({link})")
            else:
                st.markdown("N/A")

    # Document overlap analysis
    st.markdown("---")
    st.markdown("### 📋 Document Overlap Analysis")

    all_docs_sets = []
    for svc in selected_services:
        docs = set(svc.get("required_documents", []))
        all_docs_sets.append(docs)

    if len(all_docs_sets) >= 2:
        common_docs = all_docs_sets[0]
        for ds in all_docs_sets[1:]:
            common_docs = common_docs.intersection(ds)

        if common_docs:
            with st.container(border=True):
                st.markdown("**📌 Common Documents (needed for ALL selected):**")
                for doc in sorted(common_docs):
                    st.markdown(f"✅ {doc}")
                st.markdown(
                    f"\n💡 *Prepare these {len(common_docs)} documents first — "
                    f"they're needed for all your selected services!*"
                )
        else:
            st.info("No common documents between the selected services.")

    # Download comparison
    st.markdown("---")
    comp_text = "SCHEME/SERVICE COMPARISON\n"
    comp_text += "=" * 50 + "\n\n"
    for svc in selected_services:
        comp_text += f"📌 {svc.get('name', 'N/A')}\n"
        comp_text += f"   Type: {svc.get('category', 'N/A').capitalize()}\n"
        comp_text += f"   Eligibility: {svc.get('eligibility', 'N/A')}\n"
        comp_text += f"   Documents: {', '.join(svc.get('required_documents', []))}\n"
        comp_text += f"   Apply: {svc.get('how_to_apply_link', 'N/A')}\n\n"
    comp_text += "\n--- Generated by LokMitra AI ---\n"

    st.download_button(
        label="📥 Download Comparison",
        data=comp_text,
        file_name="scheme_comparison.txt",
        mime="text/plain",
        use_container_width=True,
    )
