"""Tests for lib/fallback_db.py — in-memory MongoDB-compatible storage."""

import pytest
import streamlit as st

from lib.fallback_db import FallbackCollection, FallbackCursor, FallbackDatabase


@pytest.fixture(autouse=True)
def clear_session_state():
    """Clear session state before each test."""
    if hasattr(st, "session_state"):
        keys_to_remove = [k for k in st.session_state if k.startswith("_fallback")]
        for k in keys_to_remove:
            del st.session_state[k]
    yield


class TestFallbackDatabase:
    """Tests for the FallbackDatabase class."""

    def test_get_collection(self) -> None:
        """Accessing a collection should return a FallbackCollection."""
        db = FallbackDatabase()
        collection = db["test_collection"]
        assert isinstance(collection, FallbackCollection)

    def test_different_collections(self) -> None:
        """Different names should return different collections."""
        db = FallbackDatabase()
        c1 = db["collection_a"]
        c2 = db["collection_b"]
        assert c1.name != c2.name


class TestFallbackCollection:
    """Tests for the FallbackCollection class."""

    def test_insert_one_and_find_one(self) -> None:
        """Inserting a document should make it findable."""
        db = FallbackDatabase()
        db["test"].insert_one({"name": "Test", "value": 42})
        result = db["test"].find_one({"name": "Test"})
        assert result is not None
        assert result["value"] == 42

    def test_insert_many(self) -> None:
        """Inserting multiple documents should work."""
        db = FallbackDatabase()
        docs = [{"id": i, "name": f"Doc {i}"} for i in range(5)]
        db["test"].insert_many(docs)
        assert db["test"].count_documents({}) == 5

    def test_find_returns_cursor(self) -> None:
        """find() should return a FallbackCursor."""
        db = FallbackDatabase()
        db["test"].insert_one({"x": 1})
        cursor = db["test"].find({})
        assert isinstance(cursor, FallbackCursor)

    def test_find_with_filter(self) -> None:
        """find() should filter documents correctly."""
        db = FallbackDatabase()
        db["test"].insert_many([
            {"category": "A", "val": 1},
            {"category": "B", "val": 2},
            {"category": "A", "val": 3},
        ])
        results = list(db["test"].find({"category": "A"}))
        assert len(results) == 2

    def test_find_with_regex(self) -> None:
        """find() should support $regex queries."""
        db = FallbackDatabase()
        db["test"].insert_many([
            {"name": "PAN Card"},
            {"name": "Aadhaar Card"},
            {"name": "Voter ID"},
        ])
        results = list(db["test"].find(
            {"name": {"$regex": "card", "$options": "i"}}
        ))
        assert len(results) == 2

    def test_find_with_or(self) -> None:
        """find() should support $or queries."""
        db = FallbackDatabase()
        db["test"].insert_many([
            {"name": "A", "category": "x"},
            {"name": "B", "category": "y"},
            {"name": "C", "category": "z"},
        ])
        results = list(db["test"].find({
            "$or": [{"category": "x"}, {"category": "z"}]
        }))
        assert len(results) == 2

    def test_find_one_not_found(self) -> None:
        """find_one should return None when no match."""
        db = FallbackDatabase()
        result = db["test"].find_one({"name": "nonexistent"})
        assert result is None

    def test_update_one(self) -> None:
        """update_one should modify a matching document."""
        db = FallbackDatabase()
        db["test"].insert_one({"id": "NS-001", "status": "Submitted"})
        result = db["test"].update_one(
            {"id": "NS-001"},
            {"$set": {"status": "Resolved"}}
        )
        assert result.modified_count == 1
        updated = db["test"].find_one({"id": "NS-001"})
        assert updated["status"] == "Resolved"

    def test_update_one_no_match(self) -> None:
        """update_one should return 0 modified when no match."""
        db = FallbackDatabase()
        result = db["test"].update_one(
            {"id": "nonexistent"},
            {"$set": {"status": "Done"}}
        )
        assert result.modified_count == 0

    def test_count_documents(self) -> None:
        """count_documents should return correct counts."""
        db = FallbackDatabase()
        db["test"].insert_many([{"a": 1}, {"a": 2}, {"a": 1}])
        assert db["test"].count_documents({}) == 3
        assert db["test"].count_documents({"a": 1}) == 2

    def test_projection_include(self) -> None:
        """Projection with include should only return specified fields."""
        db = FallbackDatabase()
        db["test"].insert_one({"name": "Test", "value": 42, "secret": "hidden"})
        result = db["test"].find_one({}, {"name": 1, "value": 1})
        assert "name" in result
        assert "secret" not in result


class TestFallbackCursor:
    """Tests for the FallbackCursor class."""

    def test_sort_ascending(self) -> None:
        """sort() should order documents ascending."""
        db = FallbackDatabase()
        db["test"].insert_many([
            {"name": "C", "order": 3},
            {"name": "A", "order": 1},
            {"name": "B", "order": 2},
        ])
        results = list(db["test"].find({}).sort("order", 1))
        names = [r["name"] for r in results]
        assert names == ["A", "B", "C"]

    def test_sort_descending(self) -> None:
        """sort() should order documents descending."""
        db = FallbackDatabase()
        db["test"].insert_many([
            {"name": "A", "order": 1},
            {"name": "C", "order": 3},
            {"name": "B", "order": 2},
        ])
        results = list(db["test"].find({}).sort("order", -1))
        names = [r["name"] for r in results]
        assert names == ["C", "B", "A"]

    def test_limit(self) -> None:
        """limit() should cap results."""
        db = FallbackDatabase()
        db["test"].insert_many([{"i": i} for i in range(10)])
        results = list(db["test"].find({}).limit(3))
        assert len(results) == 3

    def test_sort_and_limit_chain(self) -> None:
        """sort() and limit() should chain correctly."""
        db = FallbackDatabase()
        db["test"].insert_many([
            {"val": 5}, {"val": 1}, {"val": 3}, {"val": 2}, {"val": 4}
        ])
        results = list(db["test"].find({}).sort("val", -1).limit(3))
        vals = [r["val"] for r in results]
        assert vals == [5, 4, 3]
