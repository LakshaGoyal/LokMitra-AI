"""Civic Knowledge Quiz page for LokMitra AI.

Gamified quiz to test and improve citizens' knowledge of
government services, schemes, and civic rights.
"""

import random
import uuid

import streamlit as st
from dotenv import load_dotenv

from lib.db import get_database, get_mongo_client, get_quiz_questions, seed_quiz
from lib.i18n import get_label, language_selector
from lib.utils import inject_custom_css, render_custom_sidebar

load_dotenv()

st.set_page_config(
    page_title="Civic Quiz — LokMitra AI",
    page_icon="🧠",
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
seed_quiz(db)

# --- Header ---
st.markdown(
    "<h1 style='color:#0F172A;'>🧠 Civic Knowledge Quiz</h1>",
    unsafe_allow_html=True,
)
st.markdown(
    "<p style='color:#64748B;'>"
    "Test your knowledge of Indian government services, schemes, "
    "and citizen rights! Learn something new with every question.</p>",
    unsafe_allow_html=True,
)
st.markdown("---")

# --- Quiz State ---
if "quiz_started" not in st.session_state:
    st.session_state["quiz_started"] = False
if "quiz_questions" not in st.session_state:
    st.session_state["quiz_questions"] = []
if "quiz_current" not in st.session_state:
    st.session_state["quiz_current"] = 0
if "quiz_score" not in st.session_state:
    st.session_state["quiz_score"] = 0
if "quiz_answers" not in st.session_state:
    st.session_state["quiz_answers"] = []
if "quiz_answered" not in st.session_state:
    st.session_state["quiz_answered"] = False

# --- Load Questions ---
all_questions = get_quiz_questions(db)

if not st.session_state["quiz_started"]:
    # Start screen
    st.markdown(
        "<div style='text-align:center; padding:2rem;'>"
        "<div style='font-size:4rem;'>🧠</div>"
        "<h2>Ready to Test Your Civic Knowledge?</h2>"
        "<p style='color:#64748B; font-size:1.1rem;'>"
        "15 questions about government services, schemes, "
        "emergency numbers, and citizen rights.</p>"
        "</div>",
        unsafe_allow_html=True,
    )

    col_l, col_c, col_r = st.columns([1, 1, 1])
    with col_c:
        if st.button(
            "🚀 Start Quiz",
            key="start_quiz",
            use_container_width=True,
            type="primary",
        ):
            questions = list(all_questions)
            random.shuffle(questions)
            st.session_state["quiz_questions"] = questions[:10]
            st.session_state["quiz_current"] = 0
            st.session_state["quiz_score"] = 0
            st.session_state["quiz_answers"] = []
            st.session_state["quiz_answered"] = False
            st.session_state["quiz_started"] = True
            st.rerun()

elif st.session_state["quiz_current"] < len(st.session_state["quiz_questions"]):
    # Active quiz
    questions = st.session_state["quiz_questions"]
    current_idx = st.session_state["quiz_current"]
    question = questions[current_idx]
    total = len(questions)

    # Progress
    st.progress((current_idx) / total)
    st.markdown(
        f"**Question {current_idx + 1} of {total}** | "
        f"Score: {st.session_state['quiz_score']}/{current_idx}"
    )

    st.markdown("---")

    # Category badge
    cat = question.get("category", "General")
    st.markdown(
        f"<span style='background:#EFF6FF; color:#2563EB; "
        f"padding:0.3rem 0.8rem; border-radius:12px; "
        f"font-size:0.85rem;'>{cat}</span>",
        unsafe_allow_html=True,
    )

    # Question
    st.markdown(f"### {question.get('question', 'N/A')}")

    # Options
    options = question.get("options", [])
    correct_idx = question.get("correct", 0)

    if not st.session_state["quiz_answered"]:
        for i, option in enumerate(options):
            if st.button(
                f"{chr(65 + i)}. {option}",
                key=f"quiz_option_{current_idx}_{i}",
                use_container_width=True,
            ):
                st.session_state["quiz_answered"] = True
                is_correct = i == correct_idx
                if is_correct:
                    st.session_state["quiz_score"] += 1
                st.session_state["quiz_answers"].append(
                    {
                        "question": question.get("question", ""),
                        "selected": i,
                        "correct": correct_idx,
                        "is_correct": is_correct,
                    }
                )
                st.rerun()
    else:
        # Show result
        last_answer = st.session_state["quiz_answers"][-1]
        selected = last_answer["selected"]

        for i, option in enumerate(options):
            if i == correct_idx:
                st.markdown(
                    f"<div style='background:#DCFCE7; padding:0.75rem 1rem; "
                    f"border-radius:8px; border-left:4px solid #22C55E; "
                    f"margin:0.5rem 0;'>"
                    f"✅ {chr(65 + i)}. {option}</div>",
                    unsafe_allow_html=True,
                )
            elif i == selected and not last_answer["is_correct"]:
                st.markdown(
                    f"<div style='background:#FEE2E2; padding:0.75rem 1rem; "
                    f"border-radius:8px; border-left:4px solid #EF4444; "
                    f"margin:0.5rem 0;'>"
                    f"❌ {chr(65 + i)}. {option}</div>",
                    unsafe_allow_html=True,
                )
            else:
                st.markdown(
                    f"<div style='background:#F8FAFC; padding:0.75rem 1rem; "
                    f"border-radius:8px; margin:0.5rem 0;'>"
                    f"{chr(65 + i)}. {option}</div>",
                    unsafe_allow_html=True,
                )

        # Explanation
        explanation = question.get("explanation", "")
        if explanation:
            st.info(f"💡 **Explanation:** {explanation}")

        # Next button
        if st.button(
            "Next Question ➡️" if current_idx < total - 1 else "See Results 🏆",
            key=f"quiz_next_{current_idx}",
            type="primary",
            use_container_width=True,
        ):
            st.session_state["quiz_current"] += 1
            st.session_state["quiz_answered"] = False
            st.rerun()

else:
    # Results screen
    score = st.session_state["quiz_score"]
    total = len(st.session_state["quiz_questions"])
    pct = (score / total * 100) if total > 0 else 0

    # Grade
    if pct >= 90:
        grade, emoji, msg = "A+", "🏆", "Outstanding! You're a civic knowledge champion!"
    elif pct >= 70:
        grade, emoji, msg = "A", "🌟", "Great job! You know your rights well!"
    elif pct >= 50:
        grade, emoji, msg = "B", "👍", "Good effort! Keep learning about your rights!"
    else:
        grade, emoji, msg = "C", "📚", "Keep learning! Every citizen should know these!"

    st.markdown(
        f"<div style='text-align:center; padding:2rem;'>"
        f"<div style='font-size:5rem;'>{emoji}</div>"
        f"<h1 style='color:#0F172A;'>Quiz Complete!</h1>"
        f"<div style='font-size:3rem; font-weight:700; color:#2563EB;'>"
        f"{score}/{total}</div>"
        f"<div style='font-size:1.5rem; color:#64748B;'>"
        f"Grade: {grade} ({pct:.0f}%)</div>"
        f"<p style='color:#475569; margin-top:1rem;'>{msg}</p>"
        f"</div>",
        unsafe_allow_html=True,
    )

    # Answer review
    st.markdown("---")
    st.markdown("### 📋 Answer Review")

    for i, ans in enumerate(st.session_state["quiz_answers"]):
        q = st.session_state["quiz_questions"][i]
        icon = "✅" if ans["is_correct"] else "❌"
        st.markdown(
            f"{icon} **Q{i + 1}:** {ans['question']}\n\n"
            f"Your answer: {q['options'][ans['selected']]} | "
            f"Correct: {q['options'][ans['correct']]}"
        )

    # Restart
    st.markdown("---")
    col_l, col_c, col_r = st.columns([1, 1, 1])
    with col_c:
        if st.button(
            "🔄 Take Quiz Again",
            key="restart_quiz",
            use_container_width=True,
            type="primary",
        ):
            st.session_state["quiz_started"] = False
            st.session_state["quiz_current"] = 0
            st.session_state["quiz_score"] = 0
            st.session_state["quiz_answers"] = []
            st.session_state["quiz_answered"] = False
            st.rerun()
