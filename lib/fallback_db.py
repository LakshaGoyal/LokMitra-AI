"""Fallback in-memory database for LokMitra AI.

Provides a MongoDB-compatible storage layer using st.session_state
so the app runs on Streamlit Community Cloud without a MongoDB instance.
Data persists within a user session but not across sessions.
"""

from datetime import datetime, timezone
from typing import Any, Optional

import streamlit as st


def _get_store() -> dict[str, list[dict[str, Any]]]:
    """Get or initialize the in-memory data store.

    Returns:
        The session-state backed dictionary acting as a database.
    """
    if "_fallback_db" not in st.session_state:
        st.session_state["_fallback_db"] = {
            "services": [],
            "complaints": [],
            "chat_history": [],
            "feedback": [],
        }
    return st.session_state["_fallback_db"]


class FallbackCollection:
    """In-memory collection that mimics basic MongoDB collection operations.

    Args:
        name: The collection name.
    """

    def __init__(self, name: str) -> None:
        self.name = name

    def _data(self) -> list[dict[str, Any]]:
        """Get the list of documents in this collection."""
        store = _get_store()
        if self.name not in store:
            store[self.name] = []
        return store[self.name]

    def insert_one(self, document: dict[str, Any]) -> None:
        """Insert a single document.

        Args:
            document: The document to insert.
        """
        doc = dict(document)
        doc.pop("_id", None)
        self._data().append(doc)

    def insert_many(self, documents: list[dict[str, Any]]) -> None:
        """Insert multiple documents.

        Args:
            documents: The list of documents to insert.
        """
        for doc in documents:
            self.insert_one(doc)

    def find_one(
        self,
        filter_dict: Optional[dict[str, Any]] = None,
        projection: Optional[dict[str, int]] = None,
    ) -> Optional[dict[str, Any]]:
        """Find a single document matching the filter.

        Args:
            filter_dict: Key-value pairs to match.
            projection: Fields to include/exclude (simplified).

        Returns:
            The first matching document, or None.
        """
        for doc in self._data():
            if self._matches(doc, filter_dict or {}):
                result = dict(doc)
                result.pop("_id", None)
                return self._apply_projection(result, projection)
        return None

    def find(
        self,
        filter_dict: Optional[dict[str, Any]] = None,
        projection: Optional[dict[str, int]] = None,
    ) -> "FallbackCursor":
        """Find documents matching the filter.

        Args:
            filter_dict: Key-value pairs to match.
            projection: Fields to include/exclude.

        Returns:
            A FallbackCursor over matching documents.
        """
        results = []
        for doc in self._data():
            if self._matches(doc, filter_dict or {}):
                result = dict(doc)
                result.pop("_id", None)
                results.append(self._apply_projection(result, projection))
        return FallbackCursor(results)

    def update_one(
        self,
        filter_dict: dict[str, Any],
        update: dict[str, Any],
    ) -> "FallbackUpdateResult":
        """Update a single document matching the filter.

        Args:
            filter_dict: Key-value pairs to match.
            update: The update operations (supports $set).

        Returns:
            A FallbackUpdateResult with modified_count.
        """
        for doc in self._data():
            if self._matches(doc, filter_dict):
                if "$set" in update:
                    doc.update(update["$set"])
                return FallbackUpdateResult(modified_count=1)
        return FallbackUpdateResult(modified_count=0)

    def count_documents(self, filter_dict: Optional[dict[str, Any]] = None) -> int:
        """Count documents matching the filter.

        Args:
            filter_dict: Key-value pairs to match.

        Returns:
            The count of matching documents.
        """
        if not filter_dict:
            return len(self._data())
        return sum(1 for d in self._data() if self._matches(d, filter_dict))

    def _matches(self, doc: dict[str, Any], filter_dict: dict[str, Any]) -> bool:
        """Check if a document matches the filter criteria.

        Supports basic equality, $or, and $regex operators.

        Args:
            doc: The document to check.
            filter_dict: The filter criteria.

        Returns:
            True if the document matches.
        """
        import re as re_module

        for key, value in filter_dict.items():
            if key == "$or":
                if not any(self._matches(doc, clause) for clause in value):
                    return False
            elif isinstance(value, dict):
                if "$regex" in value:
                    pattern = value["$regex"]
                    flags = 0
                    if value.get("$options", "") == "i":
                        flags = re_module.IGNORECASE
                    if not re_module.search(pattern, str(doc.get(key, "")), flags):
                        return False
            else:
                if doc.get(key) != value:
                    return False
        return True

    @staticmethod
    def _apply_projection(
        doc: dict[str, Any],
        projection: Optional[dict[str, int]],
    ) -> dict[str, Any]:
        """Apply field projection to a document.

        Args:
            doc: The document.
            projection: Fields to include (1) or exclude (0).

        Returns:
            The projected document.
        """
        if not projection:
            return doc
        # Check if it's an inclusion or exclusion projection
        include_fields = {k for k, v in projection.items() if v == 1 and k != "_id"}
        exclude_fields = {k for k, v in projection.items() if v == 0}
        if include_fields:
            return {k: v for k, v in doc.items() if k in include_fields}
        if exclude_fields:
            return {k: v for k, v in doc.items() if k not in exclude_fields}
        return doc


class FallbackCursor:
    """Mimics a MongoDB cursor with sort and limit.

    Args:
        documents: The list of documents to iterate over.
    """

    def __init__(self, documents: list[dict[str, Any]]) -> None:
        self._docs = documents

    def sort(self, key: str, direction: int = 1) -> "FallbackCursor":
        """Sort documents by a key.

        Args:
            key: The field to sort by.
            direction: 1 for ascending, -1 for descending.

        Returns:
            Self for chaining.
        """
        self._docs.sort(
            key=lambda d: d.get(key, ""),
            reverse=(direction == -1),
        )
        return self

    def limit(self, count: int) -> "FallbackCursor":
        """Limit the number of results.

        Args:
            count: Maximum number of documents.

        Returns:
            Self for chaining.
        """
        self._docs = self._docs[:count]
        return self

    def __iter__(self):
        return iter(self._docs)

    def __len__(self):
        return len(self._docs)


class FallbackUpdateResult:
    """Mimics a MongoDB UpdateResult.

    Args:
        modified_count: Number of documents modified.
    """

    def __init__(self, modified_count: int = 0) -> None:
        self.modified_count = modified_count


class FallbackDatabase:
    """In-memory database that mimics a MongoDB Database object.

    Automatically creates collections on access.
    """

    def __getitem__(self, name: str) -> FallbackCollection:
        """Get a collection by name.

        Args:
            name: The collection name.

        Returns:
            A FallbackCollection instance.
        """
        return FallbackCollection(name)
