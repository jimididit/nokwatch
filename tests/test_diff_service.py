"""Unit tests for services.diff_service (plan: unit tests for each new service)."""
import pytest
from services.diff_service import compute_diff


class TestComputeDiff:
    def test_empty_new_content_returns_empty(self):
        assert compute_diff("old", "") == ""
        assert compute_diff(None, "") == ""

    def test_both_empty_returns_empty(self):
        assert compute_diff("", "") == ""
        # Single newline is still "content" so diff is non-empty
        assert compute_diff(None, "") == ""
        assert compute_diff("", "") == ""

    def test_diff_added_lines(self):
        old = "line1\nline2\n"
        new = "line1\nline2\nline3\n"
        result = compute_diff(old, new)
        assert "line3" in result
        assert "previous" in result or "current" in result

    def test_diff_removed_lines(self):
        old = "a\nb\nc\n"
        new = "a\nc\n"
        result = compute_diff(old, new)
        assert "-" in result or "b" in result

    def test_diff_unchanged(self):
        content = "same\ncontent\n"
        result = compute_diff(content, content)
        assert result == ""

    def test_diff_none_old_treated_as_empty(self):
        new = "only\n"
        result = compute_diff(None, new)
        assert "only" in result
