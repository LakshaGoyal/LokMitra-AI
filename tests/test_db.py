"""Tests for lib/db.py — CRUD operations with mongomock."""

import json
from pathlib import Path

import mongomock
import pytest

from lib.db import (
    _escape_regex,
    get_complaint_by_id,
    get_complaints_by_session,
    insert_complaint,
    get_chat_history,
    save_chat_message,
    search_services,
    seed_services,
    update_complaint_status,
)


@pytest.fixture
def mock_db():
    """Create a mongomock database for testing.

    Returns:
        A mongomock database instance.
    """
    client = mongomock.MongoClient()
    db = client["lokmitra_ai_test"]
    yield db
    client.close()


@pytest.fixture
def seeded_db(mock_db):
    """Create a mock database pre-seeded with services data.

    Returns:
        A mongomock database with services already loaded.
    """
    seed_path = Path(__file__).parent.parent / "data" / "seed_services.json"
    if seed_path.exists():
        with open(seed_path, "r", encoding="utf-8") as f:
            services = json.load(f)
        if services:
            mock_db["services"].insert_many(services)
    return mock_db


class TestSeedServices:
    """Tests for the seed_services function."""

    def test_seeds_empty_collection(self, mock_db) -> None:
        """Seed data should be inserted when the collection is empty."""
        seed_services(mock_db)
        count = mock_db["services"].count_documents({})
        # Should have some services if the JSON file exists
        seed_path = Path(__file__).parent.parent / "data" / "seed_services.json"
        if seed_path.exists():
            assert count > 0

    def test_does_not_re_seed(self, mock_db) -> None:
        """Seeding should be skipped if the collection already has data."""
        mock_db["services"].insert_one({"name": "Test Service"})
        initial_count = mock_db["services"].count_documents({})
        seed_services(mock_db)
        final_count = mock_db["services"].count_documents({})
        assert final_count == initial_count


class TestComplaintsCRUD:
    """Tests for complaint CRUD operations."""

    def test_insert_complaint(self, mock_db) -> None:
        """A complaint should be inserted successfully."""
        complaint = {
            "complaint_id": "NS-TEST0001",
            "session_id": "test-session",
            "category": "Roads & Potholes",
            "location": "MG Road",
            "description": "Large pothole near bus stop",
            "ai_summary": "Pothole on MG Road",
        }
        result = insert_complaint(mock_db, complaint)
        assert result is True

        # Verify it's in the database
        found = mock_db["complaints"].find_one(
            {"complaint_id": "NS-TEST0001"}
        )
        assert found is not None
        assert found["status"] == "Submitted"
        assert "created_at" in found

    def test_get_complaint_by_id(self, mock_db) -> None:
        """Retrieving a complaint by ID should work."""
        mock_db["complaints"].insert_one(
            {
                "complaint_id": "NS-FIND0001",
                "category": "Street Lights",
                "status": "Submitted",
            }
        )
        result = get_complaint_by_id(mock_db, "NS-FIND0001")
        assert result is not None
        assert result["category"] == "Street Lights"

    def test_get_complaint_by_id_not_found(self, mock_db) -> None:
        """Retrieving a non-existent complaint should return None."""
        result = get_complaint_by_id(mock_db, "NS-NONEXIST")
        assert result is None

    def test_get_complaints_by_session(self, mock_db) -> None:
        """All complaints for a session should be returned."""
        for i in range(3):
            mock_db["complaints"].insert_one(
                {
                    "complaint_id": f"NS-SESS000{i}",
                    "session_id": "session-abc",
                    "category": "Water Supply",
                    "status": "Submitted",
                    "created_at": f"2025-01-0{i + 1}T00:00:00Z",
                }
            )
        # Add one from a different session
        mock_db["complaints"].insert_one(
            {
                "complaint_id": "NS-OTHER001",
                "session_id": "session-xyz",
                "category": "Roads",
                "status": "Submitted",
                "created_at": "2025-01-01T00:00:00Z",
            }
        )
        results = get_complaints_by_session(mock_db, "session-abc")
        assert len(results) == 3

    def test_update_complaint_status(self, mock_db) -> None:
        """Updating complaint status should succeed."""
        mock_db["complaints"].insert_one(
            {
                "complaint_id": "NS-UPDT0001",
                "status": "Submitted",
            }
        )
        result = update_complaint_status(mock_db, "NS-UPDT0001", "In Review")
        assert result is True

        # Verify update
        updated = mock_db["complaints"].find_one(
            {"complaint_id": "NS-UPDT0001"}
        )
        assert updated["status"] == "In Review"
        assert "updated_at" in updated

    def test_update_nonexistent_complaint(self, mock_db) -> None:
        """Updating a non-existent complaint should return False."""
        result = update_complaint_status(mock_db, "NS-NOEXIST1", "In Review")
        assert result is False


class TestChatHistoryCRUD:
    """Tests for chat history CRUD operations."""

    def test_save_and_get_chat_message(self, mock_db) -> None:
        """Saved messages should be retrievable."""
        save_chat_message(mock_db, "session-chat", "user", "Hello!")
        save_chat_message(mock_db, "session-chat", "assistant", "Hi there!")

        history = get_chat_history(mock_db, "session-chat")
        assert len(history) == 2
        assert history[0]["role"] == "user"
        assert history[0]["content"] == "Hello!"
        assert history[1]["role"] == "assistant"

    def test_get_empty_history(self, mock_db) -> None:
        """Getting history for a session with no messages should return empty list."""
        history = get_chat_history(mock_db, "nonexistent-session")
        assert history == []

    def test_chat_history_limit(self, mock_db) -> None:
        """History should respect the limit parameter."""
        for i in range(20):
            save_chat_message(mock_db, "session-limit", "user", f"Message {i}")

        history = get_chat_history(mock_db, "session-limit", limit=5)
        assert len(history) == 5


class TestSearchServices:
    """Tests for the search_services function."""

    def test_search_by_name(self, seeded_db) -> None:
        """Searching by name should return matching services."""
        results = search_services(seeded_db, "PAN Card")
        assert len(results) > 0
        assert any("PAN" in s.get("name", "") for s in results)

    def test_search_case_insensitive(self, seeded_db) -> None:
        """Search should be case-insensitive."""
        results = search_services(seeded_db, "pan card")
        assert len(results) > 0

    def test_filter_by_category(self, seeded_db) -> None:
        """Filtering by category should return only matching items."""
        results = search_services(seeded_db, category_filter="scheme")
        for r in results:
            assert r.get("category") == "scheme"

    def test_empty_search(self, seeded_db) -> None:
        """Empty search with no filter should return all services."""
        results = search_services(seeded_db, "")
        assert len(results) > 0


class TestEscapeRegex:
    """Tests for the _escape_regex helper."""

    def test_escapes_special_chars(self) -> None:
        """Special regex characters should be escaped."""
        result = _escape_regex("test.file (v1)")
        assert "\\." in result
        assert "\\(" in result
        assert "\\)" in result

    def test_normal_text_unchanged(self) -> None:
        """Normal alphanumeric text should pass through unchanged."""
        assert _escape_regex("hello123") == "hello123"

    def test_empty_string(self) -> None:
        """Empty string should return empty string."""
        assert _escape_regex("") == ""
