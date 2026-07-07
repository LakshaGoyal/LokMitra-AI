"""MongoDB database module for LokMitra AI.

Provides a cached MongoDB client, database access, seeding,
and CRUD helpers for complaints, services, chat history, and feedback.

Falls back to an in-memory database (FallbackDatabase) when MongoDB
is unavailable — enabling deployment on Streamlit Community Cloud
without a MongoDB instance.
"""

import json
import os
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Optional

import streamlit as st

# Try importing pymongo; if MongoDB is not available, we use fallback
try:
    from pymongo import MongoClient
    from pymongo.database import Database
    from pymongo.errors import PyMongoError

    PYMONGO_AVAILABLE = True
except ImportError:
    PYMONGO_AVAILABLE = False
    PyMongoError = Exception  # type: ignore[misc, assignment]

from lib.fallback_db import FallbackDatabase


def _is_mongo_configured() -> bool:
    """Check if MongoDB URI is configured in environment.

    Returns:
        True if MONGO_URI is set and non-empty.
    """
    return bool(os.environ.get("MONGO_URI", "").strip())


@st.cache_resource
def get_mongo_client():
    """Create and cache a MongoDB client singleton.

    Reads the connection string from the ``MONGO_URI`` environment variable.
    Returns None if MongoDB is not configured or unavailable.

    Returns:
        A connected MongoClient instance, or None.
    """
    if not PYMONGO_AVAILABLE or not _is_mongo_configured():
        return None
    try:
        mongo_uri = os.environ["MONGO_URI"]
        client = MongoClient(mongo_uri, serverSelectionTimeoutMS=5000)
        # Test connection
        client.admin.command("ping")
        return client
    except Exception:
        return None


def get_database(client=None):
    """Get the LokMitra AI database.

    Falls back to FallbackDatabase (in-memory) if MongoDB is unavailable.

    Args:
        client: An optional MongoClient. If None, uses the cached client.

    Returns:
        The ``lokmitra_ai`` database instance (real or fallback).
    """
    if client is None:
        client = get_mongo_client()
    if client is not None:
        return client["lokmitra_ai"]
    # Fallback to in-memory database
    return FallbackDatabase()


def is_using_fallback() -> bool:
    """Check whether the app is using the fallback in-memory database.

    Returns:
        True if MongoDB is not available and fallback is in use.
    """
    client = get_mongo_client()
    return client is None


def seed_services(db) -> None:
    """Seed the services collection from the JSON data file.

    Only inserts data if the ``services`` collection is empty.

    Args:
        db: The database instance (real or fallback).
    """
    try:
        collection = db["services"]
        if collection.count_documents({}) == 0:
            seed_path = Path(__file__).parent.parent / "data" / "seed_services.json"
            if seed_path.exists():
                with open(seed_path, "r", encoding="utf-8") as f:
                    services_data = json.load(f)
                if services_data:
                    collection.insert_many(services_data)
    except Exception:
        pass


def seed_helplines(db) -> None:
    """Seed the helplines collection from the JSON data file.

    Args:
        db: The database instance.
    """
    try:
        collection = db["helplines"]
        if collection.count_documents({}) == 0:
            seed_path = Path(__file__).parent.parent / "data" / "helplines.json"
            if seed_path.exists():
                with open(seed_path, "r", encoding="utf-8") as f:
                    helplines_data = json.load(f)
                if helplines_data:
                    collection.insert_many(helplines_data)
    except Exception:
        pass


def seed_quiz(db) -> None:
    """Seed the quiz collection from the JSON data file.

    Args:
        db: The database instance.
    """
    try:
        collection = db["quiz"]
        if collection.count_documents({}) == 0:
            seed_path = Path(__file__).parent.parent / "data" / "quiz_questions.json"
            if seed_path.exists():
                with open(seed_path, "r", encoding="utf-8") as f:
                    quiz_data = json.load(f)
                if quiz_data:
                    collection.insert_many(quiz_data)
    except Exception:
        pass


# --- Services CRUD ---


@st.cache_data(ttl=300, show_spinner=False)
def get_all_services(_db) -> list[dict[str, Any]]:
    """Retrieve all services/schemes from the database.

    Results are cached for 5 minutes.

    Args:
        _db: The database instance (underscore prefix for
             Streamlit cache compatibility).

    Returns:
        A list of service dictionaries.
    """
    try:
        collection = _db["services"]
        services = list(collection.find({}, {"_id": 0}))
        return services
    except Exception:
        return []


def search_services(
    db,
    query: str = "",
    category_filter: str = "all",
) -> list[dict[str, Any]]:
    """Search services by name/description and optionally filter by category.

    Args:
        db: The database instance.
        query: Text to search in name and description fields.
        category_filter: 'all', 'service', or 'scheme'.

    Returns:
        A list of matching service dictionaries.
    """
    try:
        collection = db["services"]
        mongo_filter: dict[str, Any] = {}

        if query.strip():
            safe_query = _escape_regex(query.strip())
            mongo_filter["$or"] = [
                {"name": {"$regex": safe_query, "$options": "i"}},
                {"description": {"$regex": safe_query, "$options": "i"}},
            ]

        if category_filter and category_filter.lower() != "all":
            mongo_filter["category"] = category_filter.lower()

        return list(collection.find(mongo_filter, {"_id": 0}))
    except Exception:
        return []


# --- Complaints CRUD ---


def insert_complaint(db, complaint: dict[str, Any]) -> bool:
    """Insert a new complaint into the database.

    Args:
        db: The database instance.
        complaint: A dictionary with complaint fields.

    Returns:
        True if the insert succeeded, False otherwise.
    """
    try:
        complaint["created_at"] = datetime.now(timezone.utc).isoformat()
        if "status" not in complaint:
            complaint["status"] = "Submitted"
        db["complaints"].insert_one(complaint)
        return True
    except Exception:
        return False


def get_complaint_by_id(db, complaint_id: str) -> Optional[dict[str, Any]]:
    """Retrieve a complaint by its complaint_id.

    Args:
        db: The database instance.
        complaint_id: The unique complaint ID.

    Returns:
        The complaint dictionary if found, or None.
    """
    try:
        safe_id = _escape_regex(complaint_id.strip())
        result = db["complaints"].find_one(
            {"complaint_id": safe_id},
            {"_id": 0},
        )
        return result
    except Exception:
        return None


def get_complaints_by_session(db, session_id: str) -> list[dict[str, Any]]:
    """Retrieve all complaints for a given session.

    Args:
        db: The database instance.
        session_id: The session identifier.

    Returns:
        A list of complaint dictionaries, newest first.
    """
    try:
        results = list(
            db["complaints"]
            .find({"session_id": session_id}, {"_id": 0})
            .sort("created_at", -1)
        )
        return results
    except Exception:
        return []


def get_all_complaints(db) -> list[dict[str, Any]]:
    """Retrieve all complaints from the database.

    Args:
        db: The database instance.

    Returns:
        A list of all complaint dictionaries.
    """
    try:
        return list(db["complaints"].find({}, {"_id": 0}).sort("created_at", -1))
    except Exception:
        return []


def update_complaint_status(db, complaint_id: str, new_status: str) -> bool:
    """Update the status of a complaint.

    Args:
        db: The database instance.
        complaint_id: The unique complaint ID.
        new_status: The new status value.

    Returns:
        True if the update succeeded, False otherwise.
    """
    try:
        safe_id = _escape_regex(complaint_id.strip())
        result = db["complaints"].update_one(
            {"complaint_id": safe_id},
            {
                "$set": {
                    "status": new_status,
                    "updated_at": datetime.now(timezone.utc).isoformat(),
                }
            },
        )
        return result.modified_count > 0
    except Exception:
        return False


# --- Chat History CRUD ---


def save_chat_message(db, session_id: str, role: str, content: str) -> bool:
    """Save a chat message to the chat_history collection.

    Args:
        db: The database instance.
        session_id: The user/session identifier.
        role: The message role ('user' or 'assistant').
        content: The message content.

    Returns:
        True if the save succeeded, False otherwise.
    """
    try:
        db["chat_history"].insert_one(
            {
                "session_id": session_id,
                "role": role,
                "content": content,
                "timestamp": datetime.now(timezone.utc).isoformat(),
            }
        )
        return True
    except Exception:
        return False


def get_chat_history(db, session_id: str, limit: int = 50) -> list[dict[str, str]]:
    """Retrieve chat history for a session.

    Args:
        db: The database instance.
        session_id: The user/session identifier.
        limit: Maximum number of messages.

    Returns:
        A list of message dicts with 'role' and 'content' keys.
    """
    try:
        results = list(
            db["chat_history"]
            .find(
                {"session_id": session_id},
                {"_id": 0, "role": 1, "content": 1, "timestamp": 1},
            )
            .sort("timestamp", 1)
            .limit(limit)
        )
        return [{"role": r["role"], "content": r["content"]} for r in results]
    except Exception:
        return []


# --- Feedback CRUD ---


def save_feedback(
    db,
    session_id: str,
    page: str,
    rating: int,
    comment: str = "",
) -> bool:
    """Save user feedback.

    Args:
        db: The database instance.
        session_id: The session identifier.
        page: The page/feature being rated.
        rating: Rating score (1-5).
        comment: Optional comment.

    Returns:
        True if saved successfully.
    """
    try:
        db["feedback"].insert_one(
            {
                "session_id": session_id,
                "page": page,
                "rating": rating,
                "comment": comment,
                "timestamp": datetime.now(timezone.utc).isoformat(),
            }
        )
        return True
    except Exception:
        return False


def get_all_feedback(db) -> list[dict[str, Any]]:
    """Retrieve all feedback entries.

    Args:
        db: The database instance.

    Returns:
        A list of feedback dictionaries.
    """
    try:
        return list(db["feedback"].find({}, {"_id": 0}).sort("timestamp", -1))
    except Exception:
        return []


# --- Helplines ---


def get_all_helplines(db) -> list[dict[str, Any]]:
    """Retrieve all emergency helplines.

    Args:
        db: The database instance.

    Returns:
        A list of helpline dictionaries.
    """
    try:
        return list(db["helplines"].find({}, {"_id": 0}))
    except Exception:
        return []


# --- Quiz ---


def get_quiz_questions(db) -> list[dict[str, Any]]:
    """Retrieve all quiz questions.

    Args:
        db: The database instance.

    Returns:
        A list of quiz question dictionaries.
    """
    try:
        return list(db["quiz"].find({}, {"_id": 0}))
    except Exception:
        return []


# --- Helpers ---


def _escape_regex(text: str) -> str:
    """Escape special regex characters in a string.

    Args:
        text: The raw input string.

    Returns:
        The escaped string safe for regex queries.
    """
    special_chars = r"\.^$*+?{}[]|()"
    escaped = ""
    for char in text:
        if char in special_chars:
            escaped += "\\" + char
        else:
            escaped += char
    return escaped
