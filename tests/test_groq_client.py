"""Tests for lib/groq_client.py — prompt construction and mocked API calls."""

from unittest.mock import MagicMock, patch

import pytest

from lib.groq_client import (
    _trim_chat_history,
    build_system_prompt,
    chat_with_assistant,
    classify_issue,
    recommend_schemes,
    summarize_service,
)


class TestBuildSystemPrompt:
    """Tests for the build_system_prompt function."""

    def test_includes_language_directive(self) -> None:
        """The system prompt should include the target language."""
        prompt = build_system_prompt("Hindi")
        assert "Hindi" in prompt

    def test_english_default(self) -> None:
        """Default language should be English."""
        prompt = build_system_prompt()
        assert "English" in prompt

    def test_includes_safety_instructions(self) -> None:
        """The prompt should include anti-injection instructions."""
        prompt = build_system_prompt()
        assert "NEVER" in prompt
        assert "override" in prompt.lower()

    def test_includes_civic_context(self) -> None:
        """The prompt should ground the AI in civic services context."""
        prompt = build_system_prompt()
        assert "LokMitra AI" in prompt
        assert "government" in prompt.lower()

    def test_includes_clarification_rule(self) -> None:
        """The prompt should instruct the AI to ask clarifying questions."""
        prompt = build_system_prompt()
        assert "clarifying" in prompt.lower()


class TestTrimChatHistory:
    """Tests for the _trim_chat_history function."""

    def test_trims_to_max(self) -> None:
        """History should be trimmed to max_messages non-system messages."""
        messages = [{"role": "user", "content": f"msg {i}"} for i in range(20)]
        result = _trim_chat_history(messages, max_messages=5)
        non_system = [m for m in result if m["role"] != "system"]
        assert len(non_system) == 5

    def test_preserves_system_message(self) -> None:
        """System message should always be preserved at the start."""
        messages = [
            {"role": "system", "content": "System prompt"},
            {"role": "user", "content": "msg 1"},
            {"role": "assistant", "content": "reply 1"},
            {"role": "user", "content": "msg 2"},
        ]
        result = _trim_chat_history(messages, max_messages=2)
        assert result[0]["role"] == "system"
        assert len(result) == 3  # system + 2 recent

    def test_short_history_unchanged(self) -> None:
        """History shorter than max should not be trimmed."""
        messages = [
            {"role": "user", "content": "Hello"},
            {"role": "assistant", "content": "Hi"},
        ]
        result = _trim_chat_history(messages, max_messages=10)
        assert len(result) == 2

    def test_keeps_most_recent(self) -> None:
        """Trimming should keep the most recent messages."""
        messages = [
            {"role": "user", "content": f"msg {i}"} for i in range(10)
        ]
        result = _trim_chat_history(messages, max_messages=3)
        assert result[-1]["content"] == "msg 9"
        assert result[0]["content"] == "msg 7"


class TestChatWithAssistant:
    """Tests for the chat_with_assistant function (mocked API)."""

    @patch("lib.groq_client.get_groq_client")
    def test_returns_response(self, mock_get_client: MagicMock) -> None:
        """Should return the assistant's response content."""
        # Mock the Groq client and response
        mock_client = MagicMock()
        mock_get_client.return_value = mock_client

        mock_response = MagicMock()
        mock_response.choices = [MagicMock()]
        mock_response.choices[0].message.content = "Here is your answer."
        mock_client.chat.completions.create.return_value = mock_response

        messages = [{"role": "user", "content": "How to get PAN card?"}]
        result = chat_with_assistant(messages, language="English")

        assert result == "Here is your answer."
        mock_client.chat.completions.create.assert_called_once()

    @patch("lib.groq_client.get_groq_client")
    def test_uses_correct_model(self, mock_get_client: MagicMock) -> None:
        """Should use the specified model."""
        mock_client = MagicMock()
        mock_get_client.return_value = mock_client

        mock_response = MagicMock()
        mock_response.choices = [MagicMock()]
        mock_response.choices[0].message.content = "Response"
        mock_client.chat.completions.create.return_value = mock_response

        chat_with_assistant(
            [{"role": "user", "content": "Test"}],
            model="llama-3.3-70b-versatile",
        )

        call_kwargs = mock_client.chat.completions.create.call_args[1]
        assert call_kwargs["model"] == "llama-3.3-70b-versatile"

    @patch("lib.groq_client.get_groq_client")
    def test_caps_max_tokens(self, mock_get_client: MagicMock) -> None:
        """Should set max_tokens to 1024."""
        mock_client = MagicMock()
        mock_get_client.return_value = mock_client

        mock_response = MagicMock()
        mock_response.choices = [MagicMock()]
        mock_response.choices[0].message.content = "Response"
        mock_client.chat.completions.create.return_value = mock_response

        chat_with_assistant([{"role": "user", "content": "Test"}])

        call_kwargs = mock_client.chat.completions.create.call_args[1]
        assert call_kwargs["max_tokens"] == 1024

    @patch("lib.groq_client.get_groq_client")
    def test_includes_system_prompt(self, mock_get_client: MagicMock) -> None:
        """The system prompt should be included in the messages."""
        mock_client = MagicMock()
        mock_get_client.return_value = mock_client

        mock_response = MagicMock()
        mock_response.choices = [MagicMock()]
        mock_response.choices[0].message.content = "Response"
        mock_client.chat.completions.create.return_value = mock_response

        chat_with_assistant(
            [{"role": "user", "content": "Test"}],
            language="Hindi",
        )

        call_kwargs = mock_client.chat.completions.create.call_args[1]
        messages = call_kwargs["messages"]
        system_msgs = [m for m in messages if m["role"] == "system"]
        assert len(system_msgs) == 1
        assert "Hindi" in system_msgs[0]["content"]

    @patch("lib.groq_client.get_groq_client")
    def test_api_error_raises_runtime(self, mock_get_client: MagicMock) -> None:
        """API errors should be wrapped in RuntimeError."""
        mock_client = MagicMock()
        mock_get_client.return_value = mock_client
        mock_client.chat.completions.create.side_effect = Exception("API error")

        with pytest.raises(RuntimeError, match="Unable to get a response"):
            chat_with_assistant([{"role": "user", "content": "Test"}])


class TestClassifyIssue:
    """Tests for the classify_issue function (mocked API)."""

    @patch("lib.groq_client.get_groq_client")
    def test_returns_classification(self, mock_get_client: MagicMock) -> None:
        """Should return a dict with severity, category, and summary."""
        mock_client = MagicMock()
        mock_get_client.return_value = mock_client

        mock_response = MagicMock()
        mock_response.choices = [MagicMock()]
        mock_response.choices[0].message.content = (
            '{"severity": "High", "category": "Roads & Potholes", '
            '"summary": "Large pothole on MG Road"}'
        )
        mock_client.chat.completions.create.return_value = mock_response

        result = classify_issue("There is a big pothole on MG Road")
        assert result["severity"] == "High"
        assert result["category"] == "Roads & Potholes"
        assert "pothole" in result["summary"].lower()

    @patch("lib.groq_client.get_groq_client")
    def test_fallback_on_parse_error(self, mock_get_client: MagicMock) -> None:
        """Should return fallback values if JSON parsing fails."""
        mock_client = MagicMock()
        mock_get_client.return_value = mock_client

        mock_response = MagicMock()
        mock_response.choices = [MagicMock()]
        mock_response.choices[0].message.content = "not valid json"
        mock_client.chat.completions.create.return_value = mock_response

        result = classify_issue("Some issue")
        assert result["severity"] == "Medium"
        assert result["category"] == "Other"


class TestSummarizeService:
    """Tests for the summarize_service function (mocked API)."""

    @patch("lib.groq_client.get_groq_client")
    def test_returns_summary(self, mock_get_client: MagicMock) -> None:
        """Should return a summary string."""
        mock_client = MagicMock()
        mock_get_client.return_value = mock_client

        mock_response = MagicMock()
        mock_response.choices = [MagicMock()]
        mock_response.choices[0].message.content = "PAN Card is a tax identification number."
        mock_client.chat.completions.create.return_value = mock_response

        service = {
            "name": "PAN Card",
            "description": "Tax ID card",
            "required_documents": ["Aadhaar", "Photo"],
            "eligibility": "Any Indian citizen",
            "how_to_apply_link": "https://example.com",
        }
        result = summarize_service(service, language="English")
        assert "PAN" in result

    @patch("lib.groq_client.get_groq_client")
    def test_fallback_on_error(self, mock_get_client: MagicMock) -> None:
        """Should return fallback message on API error."""
        mock_client = MagicMock()
        mock_get_client.return_value = mock_client
        mock_client.chat.completions.create.side_effect = Exception("API error")

        result = summarize_service({"name": "Test"})
        assert "unable" in result.lower() or "try again" in result.lower()


class TestRecommendSchemes:
    """Tests for the recommend_schemes function (mocked API)."""

    @patch("lib.groq_client.get_groq_client")
    def test_returns_recommendations(self, mock_get_client: MagicMock) -> None:
        """Should return recommendation text."""
        mock_client = MagicMock()
        mock_get_client.return_value = mock_client

        mock_response = MagicMock()
        mock_response.choices = [MagicMock()]
        mock_response.choices[0].message.content = (
            "**PM Kisan**\nWhy this fits you: You are a farmer."
        )
        mock_client.chat.completions.create.return_value = mock_response

        profile = {
            "age": 35,
            "occupation": "Farmer",
            "income_bracket": "₹1 Lakh – ₹3 Lakh",
            "state": "Maharashtra",
        }
        schemes = [
            {"name": "PM Kisan", "category": "scheme", "description": "Farmer support", "eligibility": "Farmers"},
        ]
        result = recommend_schemes(profile, schemes, language="English")
        assert "PM Kisan" in result
