"""AI Chat Assistant page for LokMitra AI."""

from __future__ import annotations

import uuid

import streamlit as st
from dotenv import load_dotenv

from lib.db import get_chat_history, get_database, get_mongo_client, save_chat_message
from lib.groq_client import chat_with_assistant
from lib.i18n import get_label, language_selector
from lib.utils import (
    check_rate_limit,
    inject_custom_css,
    render_custom_sidebar,
    render_page_header,
    sanitize_text,
)

load_dotenv()

st.set_page_config(page_title="AI Assistant | LokMitra AI", page_icon="AI", layout="wide")
inject_custom_css()

if "session_id" not in st.session_state:
    st.session_state["session_id"] = str(uuid.uuid4())
if "chat_messages" not in st.session_state:
    st.session_state["chat_messages"] = []

lang = language_selector()
render_custom_sidebar()

db = None
try:
    client = get_mongo_client()
    db = get_database(client)
except Exception:
    pass

if not st.session_state["chat_messages"] and db is not None:
    try:
        history = get_chat_history(db, st.session_state["session_id"])
        if history:
            st.session_state["chat_messages"] = history
    except Exception:
        pass

render_page_header(
    get_label("assistant_title", lang),
    "Ask grounded questions about Indian public services, documents, eligibility, RTI, and civic issue resolution. LokMitra answers in your selected language and nudges users toward official verification.",
    "Grounded AI workflow",
)

guide_cols = st.columns(3)
with guide_cols[0]:
    st.info("Best for: documents, eligibility, steps, portals, and RTI preparation.")
with guide_cols[1]:
    st.info("Guardrails: no fabricated local contacts, fees, or unofficial promises.")
with guide_cols[2]:
    st.info("Tip: include your state, city, age, income bracket, or service name.")

for msg in st.session_state["chat_messages"]:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])

user_input = st.chat_input(placeholder=get_label("assistant_placeholder", lang))

if user_input:
    clean_input = sanitize_text(user_input, max_length=1000)

    if not clean_input:
        st.warning("Please enter a valid question.")
    else:
        allowed, wait_time = check_rate_limit("chat_rate_limit", cooldown_seconds=2.0)
        if not allowed:
            st.warning(f"Please wait {wait_time} seconds before sending another message.")
        else:
            st.session_state["chat_messages"].append({"role": "user", "content": clean_input})
            with st.chat_message("user"):
                st.markdown(clean_input)

            if db is not None:
                save_chat_message(db, st.session_state["session_id"], "user", clean_input)

            with st.chat_message("assistant"):
                with st.spinner(get_label("assistant_thinking", lang)):
                    try:
                        response = chat_with_assistant(
                            st.session_state["chat_messages"],
                            language=lang,
                        )
                        st.markdown(response)
                        st.session_state["chat_messages"].append(
                            {"role": "assistant", "content": response}
                        )
                        if db is not None:
                            save_chat_message(
                                db,
                                st.session_state["session_id"],
                                "assistant",
                                response,
                            )
                    except ValueError as e:
                        st.error(str(e))
                    except Exception:
                        st.error(get_label("error_generic", lang))
