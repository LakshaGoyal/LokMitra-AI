"""Civic knowledge quiz page."""

from __future__ import annotations

import random
import uuid

import streamlit as st
from dotenv import load_dotenv

from lib.db import get_database, get_mongo_client, get_quiz_questions, seed_quiz
from lib.i18n import language_selector
from lib.utils import inject_custom_css, render_custom_sidebar, render_page_header

load_dotenv()

st.set_page_config(page_title="Civic Quiz | LokMitra AI", page_icon="QZ", layout="wide")
inject_custom_css()

if "session_id" not in st.session_state:
    st.session_state["session_id"] = str(uuid.uuid4())

language_selector()
render_custom_sidebar()

client = get_mongo_client()
db = get_database(client)
seed_quiz(db)

render_page_header(
    "Civic Knowledge Quiz",
    "Practice government-service knowledge, emergency numbers, public rights, and document workflows with immediate feedback.",
    "Citizen learning",
)

defaults = {
    "quiz_started": False,
    "quiz_questions": [],
    "quiz_current": 0,
    "quiz_score": 0,
    "quiz_answers": [],
    "quiz_answered": False,
}
for key, value in defaults.items():
    st.session_state.setdefault(key, value)

all_questions = get_quiz_questions(db)

if not st.session_state["quiz_started"]:
    with st.container(border=True):
        st.markdown("### Ready to test your civic knowledge?")
        st.markdown("You will get 10 randomized questions with explanations after each answer.")
        if st.button("Start quiz", key="start_quiz", use_container_width=True, type="primary"):
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
    questions = st.session_state["quiz_questions"]
    current_idx = st.session_state["quiz_current"]
    question = questions[current_idx]
    total = len(questions)

    st.progress(current_idx / total)
    st.markdown(f"**Question {current_idx + 1} of {total}** | Score: {st.session_state['quiz_score']}/{current_idx}")
    st.markdown(f"<span class='lm-pill'>{question.get('category', 'General')}</span>", unsafe_allow_html=True)
    st.markdown(f"### {question.get('question', 'N/A')}")

    options = question.get("options", [])
    correct_idx = question.get("correct", 0)

    if not st.session_state["quiz_answered"]:
        for i, option in enumerate(options):
            if st.button(f"{chr(65 + i)}. {option}", key=f"quiz_option_{current_idx}_{i}", use_container_width=True):
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
        last_answer = st.session_state["quiz_answers"][-1]
        selected = last_answer["selected"]
        for i, option in enumerate(options):
            if i == correct_idx:
                st.success(f"{chr(65 + i)}. {option}")
            elif i == selected and not last_answer["is_correct"]:
                st.error(f"{chr(65 + i)}. {option}")
            else:
                st.write(f"{chr(65 + i)}. {option}")

        explanation = question.get("explanation", "")
        if explanation:
            st.info(f"Explanation: {explanation}")

        if st.button("Next question" if current_idx < total - 1 else "See results", key=f"quiz_next_{current_idx}", type="primary", use_container_width=True):
            st.session_state["quiz_current"] += 1
            st.session_state["quiz_answered"] = False
            st.rerun()

else:
    score = st.session_state["quiz_score"]
    total = len(st.session_state["quiz_questions"])
    pct = (score / total * 100) if total else 0
    grade = "A+" if pct >= 90 else "A" if pct >= 70 else "B" if pct >= 50 else "C"

    with st.container(border=True):
        st.markdown("### Quiz complete")
        st.metric("Score", f"{score}/{total}", f"Grade {grade} - {pct:.0f}%")

    st.markdown("### Answer review")
    for i, ans in enumerate(st.session_state["quiz_answers"]):
        q = st.session_state["quiz_questions"][i]
        status = "Correct" if ans["is_correct"] else "Review"
        st.markdown(
            f"**{status} - Q{i + 1}:** {ans['question']}\n\n"
            f"Your answer: {q['options'][ans['selected']]} | Correct: {q['options'][ans['correct']]}"
        )

    if st.button("Take quiz again", key="restart_quiz", use_container_width=True, type="primary"):
        st.session_state["quiz_started"] = False
        st.session_state["quiz_current"] = 0
        st.session_state["quiz_score"] = 0
        st.session_state["quiz_answers"] = []
        st.session_state["quiz_answered"] = False
        st.rerun()
