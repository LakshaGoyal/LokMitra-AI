"""Analytics dashboard page for LokMitra AI."""

from __future__ import annotations

import uuid
from collections import Counter

import pandas as pd
import streamlit as st
from dotenv import load_dotenv

from lib.db import (
    get_all_complaints,
    get_all_feedback,
    get_all_services,
    get_database,
    get_mongo_client,
    is_using_fallback,
    seed_services,
)
from lib.i18n import language_selector
from lib.utils import inject_custom_css, render_custom_sidebar, render_empty_state, render_page_header

load_dotenv()

st.set_page_config(page_title="Dashboard | LokMitra AI", page_icon="DB", layout="wide")
inject_custom_css()

if "session_id" not in st.session_state:
    st.session_state["session_id"] = str(uuid.uuid4())

language_selector()
render_custom_sidebar()

client = get_mongo_client()
db = get_database(client)
seed_services(db)

render_page_header(
    "Operations Dashboard",
    "A real-time command view for complaints, services, scheme coverage, severity distribution, and user feedback signals.",
    "GovTech analytics",
)

if is_using_fallback():
    st.info("Running in sandbox mode. Data is session-scoped until MongoDB is configured.")

complaints = get_all_complaints(db)
services = get_all_services(db)
feedback = get_all_feedback(db)

total_complaints = len(complaints)
resolved = sum(1 for c in complaints if c.get("status") == "Resolved")
in_progress = sum(1 for c in complaints if c.get("status") in ("In Review", "In Progress"))
pending = sum(1 for c in complaints if c.get("status") == "Submitted")
total_schemes = sum(1 for s in services if s.get("category") == "scheme")

cols = st.columns(5)
metrics = [
    ("Total complaints", total_complaints, f"{pending} pending" if pending else "No pending"),
    ("Resolved", resolved, f"{(resolved / total_complaints * 100):.0f}%" if total_complaints else "No data"),
    ("In progress", in_progress, "Active queue"),
    ("Services listed", len(services), "Seeded records"),
    ("Schemes", total_schemes, "Recommendation pool"),
]
for col, (label, value, delta) in zip(cols, metrics):
    with col:
        st.metric(label, value, delta)

if complaints:
    chart_col1, chart_col2 = st.columns(2)
    with chart_col1:
        st.markdown("### Complaints by category")
        cat_counts = Counter(c.get("category", "Unknown") for c in complaints)
        st.bar_chart(pd.DataFrame({"Category": cat_counts.keys(), "Count": cat_counts.values()}).set_index("Category"))
    with chart_col2:
        st.markdown("### Complaints by status")
        status_counts = Counter(c.get("status", "Unknown") for c in complaints)
        st.bar_chart(pd.DataFrame({"Status": status_counts.keys(), "Count": status_counts.values()}).set_index("Status"))

    st.markdown("### Severity distribution")
    sev_counts = Counter(c.get("severity", "Medium") for c in complaints)
    sev_cols = st.columns(4)
    for col, sev in zip(sev_cols, ["Low", "Medium", "High", "Critical"]):
        with col:
            count = sev_counts.get(sev, 0)
            pct = (count / total_complaints * 100) if total_complaints else 0
            st.metric(sev, count, f"{pct:.0f}%")

    st.markdown("### Recent complaints")
    table_data = []
    for c in complaints[:10]:
        created = c.get("created_at", "N/A")
        if isinstance(created, str) and "T" in created:
            created = created.split("T")[0]
        table_data.append(
            {
                "ID": c.get("complaint_id", "N/A"),
                "Category": c.get("category", "N/A"),
                "Location": c.get("location", "N/A"),
                "Status": c.get("status", "N/A"),
                "Severity": c.get("severity", "N/A"),
                "Date": created,
            }
        )
    st.dataframe(pd.DataFrame(table_data), use_container_width=True, hide_index=True)
else:
    render_empty_state("No complaint data yet", "Submit a report from the Report Issue page to populate analytics.")

if services:
    st.markdown("### Services vs schemes")
    svc_count = sum(1 for s in services if s.get("category") == "service")
    df_dist = pd.DataFrame({"Type": ["Services", "Schemes"], "Count": [svc_count, total_schemes]})
    st.bar_chart(df_dist.set_index("Type"))

if feedback:
    st.markdown("### Feedback summary")
    avg_rating = sum(f.get("rating", 0) for f in feedback) / len(feedback)
    st.metric("Average rating", f"{avg_rating:.1f}/5", f"{len(feedback)} reviews")
