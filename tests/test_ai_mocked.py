"""Unit tests for AI features with mocked OpenAI (plan: mock AI API responses for testing)."""
from unittest.mock import patch, MagicMock
import pytest
from ai.smart_detector import analyze_content


def test_analyze_content_returns_none_when_no_api_key(monkeypatch):
    """When AI is not available (no key), analyze_content returns None."""
    import ai.smart_detector as sm
    monkeypatch.setattr(sm, "is_ai_available", lambda: False)
    result = analyze_content("some content", "What changed?")
    assert result is None


def test_analyze_content_returns_none_for_empty_prompt(monkeypatch):
    """Empty prompt should return None without calling API."""
    import ai.smart_detector as sm
    monkeypatch.setattr(sm, "is_ai_available", lambda: True)
    result = analyze_content("content here", "")
    assert result is None


def test_analyze_content_returns_mock_response_when_mocked(monkeypatch):
    """When OpenAI is mocked, analyze_content returns the mocked content."""
    import ai.smart_detector as sm
    monkeypatch.setattr(sm, "is_ai_available", lambda: True)
    mock_content = "Summary: page discusses availability."
    mock_message = MagicMock()
    mock_message.content = mock_content
    mock_choice = MagicMock()
    mock_choice.message = mock_message
    mock_response = MagicMock()
    mock_response.choices = [mock_choice]

    # OpenAI is imported inside analyze_content as "from openai import OpenAI"
    with patch("openai.OpenAI") as MockClient:
        MockClient.return_value.chat.completions.create.return_value = mock_response
        result = analyze_content("page text", "Summarize")
    assert result == mock_content
