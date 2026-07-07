"""Tests for lib/utils.py — input validation, sanitization, and utilities."""

from lib.utils import (
    generate_complaint_id,
    get_status_display,
    next_status,
    sanitize_text,
    validate_complaint_form,
    validate_scheme_form,
)


class TestSanitizeText:
    """Tests for the sanitize_text function."""

    def test_strips_html_tags(self) -> None:
        """HTML tags should be removed from the input."""
        result = sanitize_text("<script>alert('xss')</script>Hello")
        assert "<script>" not in result
        assert "</script>" not in result
        assert "Hello" in result
        # Script contents are removed, not merely stripped of tags.
        assert "alert" not in result

    def test_strips_nested_html(self) -> None:
        """Nested HTML tags should be fully removed."""
        result = sanitize_text("<div><p>Some <b>bold</b> text</p></div>")
        assert "<" not in result
        assert ">" not in result
        assert "Some" in result
        assert "bold" in result

    def test_removes_control_characters(self) -> None:
        """Control characters (except newlines/tabs) should be removed."""
        result = sanitize_text("Hello\x00World\x07Test")
        assert "\x00" not in result
        assert "\x07" not in result
        assert "HelloWorldTest" in result

    def test_preserves_newlines(self) -> None:
        """Newlines should be preserved in the sanitized output."""
        result = sanitize_text("Line 1\nLine 2\nLine 3")
        assert "\n" in result

    def test_truncates_long_input(self) -> None:
        """Input exceeding max_length should be truncated."""
        long_text = "A" * 3000
        result = sanitize_text(long_text, max_length=100)
        assert len(result) == 100

    def test_custom_max_length(self) -> None:
        """Custom max_length should be respected."""
        result = sanitize_text("Hello World", max_length=5)
        assert len(result) == 5

    def test_strips_whitespace(self) -> None:
        """Leading and trailing whitespace should be stripped."""
        result = sanitize_text("   Hello World   ")
        assert result == "Hello World"

    def test_collapses_excessive_whitespace(self) -> None:
        """Multiple consecutive spaces should be collapsed to one."""
        result = sanitize_text("Hello     World")
        assert "     " not in result
        assert "Hello World" in result

    def test_collapses_excessive_newlines(self) -> None:
        """More than 2 consecutive newlines should be collapsed."""
        result = sanitize_text("Hello\n\n\n\n\nWorld")
        assert "\n\n\n" not in result

    def test_empty_string(self) -> None:
        """Empty string should return empty string."""
        assert sanitize_text("") == ""

    def test_non_string_input(self) -> None:
        """Non-string input should return empty string."""
        assert sanitize_text(None) == ""  # type: ignore[arg-type]
        assert sanitize_text(123) == ""  # type: ignore[arg-type]

    def test_normal_text_unchanged(self) -> None:
        """Normal text without special characters should pass through."""
        text = "How to get a Birth Certificate in Maharashtra?"
        assert sanitize_text(text) == text


class TestValidateComplaintForm:
    """Tests for the validate_complaint_form function."""

    def test_valid_form(self) -> None:
        """A valid form should return True."""
        is_valid, error = validate_complaint_form(
            "Roads & Potholes", "MG Road, Sector 15", "Large pothole near the bus stop"
        )
        assert is_valid is True
        assert error is None

    def test_empty_category(self) -> None:
        """Empty category should be rejected."""
        is_valid, error = validate_complaint_form(
            "", "MG Road", "Description of issue"
        )
        assert is_valid is False
        assert error is not None

    def test_short_location(self) -> None:
        """Location under 3 characters should be rejected."""
        is_valid, error = validate_complaint_form(
            "Roads", "MG", "Description of the issue here"
        )
        assert is_valid is False
        assert "location" in error.lower()

    def test_long_location(self) -> None:
        """Location over 200 characters should be rejected."""
        is_valid, error = validate_complaint_form(
            "Roads", "A" * 201, "Description of issue"
        )
        assert is_valid is False
        assert "200" in error

    def test_short_description(self) -> None:
        """Description under 10 characters should be rejected."""
        is_valid, error = validate_complaint_form(
            "Roads", "MG Road", "Short"
        )
        assert is_valid is False
        assert "description" in error.lower()

    def test_long_description(self) -> None:
        """Description over 2000 characters should be rejected."""
        is_valid, error = validate_complaint_form(
            "Roads", "MG Road", "A" * 2001
        )
        assert is_valid is False
        assert "2000" in error


class TestValidateSchemeForm:
    """Tests for the validate_scheme_form function."""

    def test_valid_form(self) -> None:
        """A valid form should return True."""
        is_valid, error = validate_scheme_form(
            30, "Farmer", "₹1 Lakh – ₹3 Lakh", "Maharashtra"
        )
        assert is_valid is True
        assert error is None

    def test_invalid_age_zero(self) -> None:
        """Age of 0 should be rejected."""
        is_valid, error = validate_scheme_form(
            0, "Farmer", "₹1 Lakh – ₹3 Lakh", "Maharashtra"
        )
        assert is_valid is False

    def test_invalid_age_too_high(self) -> None:
        """Age over 120 should be rejected."""
        is_valid, error = validate_scheme_form(
            150, "Farmer", "₹1 Lakh – ₹3 Lakh", "Maharashtra"
        )
        assert is_valid is False

    def test_empty_occupation(self) -> None:
        """Empty occupation should be rejected."""
        is_valid, error = validate_scheme_form(
            30, "", "₹1 Lakh – ₹3 Lakh", "Maharashtra"
        )
        assert is_valid is False

    def test_empty_income(self) -> None:
        """Empty income bracket should be rejected."""
        is_valid, error = validate_scheme_form(
            30, "Farmer", "", "Maharashtra"
        )
        assert is_valid is False

    def test_empty_state(self) -> None:
        """Empty state should be rejected."""
        is_valid, error = validate_scheme_form(
            30, "Farmer", "₹1 Lakh – ₹3 Lakh", ""
        )
        assert is_valid is False


class TestGenerateComplaintId:
    """Tests for the generate_complaint_id function."""

    def test_format(self) -> None:
        """Complaint ID should follow the LM-XXXXXXXX format."""
        cid = generate_complaint_id()
        assert cid.startswith("LM-")
        assert len(cid) == 11  # LM- + 8 hex chars

    def test_uniqueness(self) -> None:
        """Multiple calls should generate unique IDs."""
        ids = {generate_complaint_id() for _ in range(100)}
        assert len(ids) == 100

    def test_uppercase(self) -> None:
        """The hex portion should be uppercase."""
        cid = generate_complaint_id()
        hex_part = cid[3:]
        assert hex_part == hex_part.upper()


class TestGetStatusDisplay:
    """Tests for the get_status_display function."""

    def test_known_statuses(self) -> None:
        """Known statuses should return formatted strings."""
        assert get_status_display("Submitted") == "Submitted"
        assert get_status_display("In Review") == "In Review"
        assert get_status_display("In Progress") == "In Progress"
        assert get_status_display("Resolved") == "Resolved"

    def test_unknown_status(self) -> None:
        """Unknown status should return the raw value."""
        assert get_status_display("Custom") == "Custom"


class TestNextStatus:
    """Tests for the next_status function."""

    def test_progression(self) -> None:
        """Status should progress in the correct order."""
        assert next_status("Submitted") == "In Review"
        assert next_status("In Review") == "In Progress"
        assert next_status("In Progress") == "Resolved"

    def test_final_status(self) -> None:
        """Resolved should return None (no next status)."""
        assert next_status("Resolved") is None

    def test_unknown_status(self) -> None:
        """Unknown status should return None."""
        assert next_status("Unknown") is None
