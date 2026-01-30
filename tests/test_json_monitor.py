"""Unit tests for monitoring.json_monitor (plan: unit tests for each new service)."""
import pytest
from monitoring.json_monitor import (
    is_json_response,
    extract_text_from_json,
    JSONPATH_AVAILABLE,
)


class TestIsJsonResponse:
    def test_content_type_json_returns_true(self):
        assert is_json_response("application/json", b"{}") is True
        assert is_json_response("application/json; charset=utf-8", b"[]") is True

    def test_content_empty_or_short_returns_false(self):
        assert is_json_response(None, b"") is False
        assert is_json_response(None, b"x") is False

    def test_content_starts_with_brace_or_bracket(self):
        assert is_json_response(None, b'{"a":1}') is True
        assert is_json_response(None, b"[1,2]") is True
        assert is_json_response(None, b"  [") is True

    def test_content_not_json_returns_false(self):
        assert is_json_response(None, b"<html>") is False
        assert is_json_response("text/html", b"<html>") is False


class TestExtractTextFromJson:
    def test_empty_json_path_returns_error(self):
        ok, text, err = extract_text_from_json(b'{"a":1}', "")
        assert ok is False
        assert err is not None
        assert "empty" in err.lower() or "jsonpath" in err.lower()

    @pytest.mark.skipif(not JSONPATH_AVAILABLE, reason="jsonpath-ng not installed")
    def test_valid_jsonpath_single_value(self):
        ok, text, err = extract_text_from_json(b'{"name": "Nokwatch"}', "$.name")
        assert ok is True
        assert err is None
        assert text == "Nokwatch"

    @pytest.mark.skipif(not JSONPATH_AVAILABLE, reason="jsonpath-ng not installed")
    def test_valid_jsonpath_array(self):
        ok, text, err = extract_text_from_json(b'{"items": [1, 2, 3]}', "$.items")
        assert ok is True
        assert err is None
        assert "1" in text and "2" in text

    @pytest.mark.skipif(not JSONPATH_AVAILABLE, reason="jsonpath-ng not installed")
    def test_invalid_json_returns_error(self):
        ok, text, err = extract_text_from_json(b"not json", "$.x")
        assert ok is False
        assert "invalid" in err.lower() or "decode" in err.lower()

    @pytest.mark.skipif(not JSONPATH_AVAILABLE, reason="jsonpath-ng not installed")
    def test_path_no_match_returns_empty_string(self):
        ok, text, err = extract_text_from_json(b'{"a": 1}', "$.nonexistent")
        assert ok is True
        assert text == ""
        assert err is None
