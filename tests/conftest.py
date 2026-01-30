"""Pytest fixtures for Nokwatch tests (plan: unit tests per service, integration, mocked AI)."""
import pytest


@pytest.fixture
def sample_job():
    """Minimal job dict for monitor/notification tests."""
    return {
        "id": 1,
        "name": "Test Job",
        "url": "https://httpbin.org/html",
        "check_interval": 300,
        "match_type": "string",
        "match_pattern": "test",
        "match_condition": "contains",
        "email_recipient": "test@example.com",
        "is_active": True,
        "auth_config": None,
    }


@pytest.fixture
def sample_auth_config():
    """Auth config with basic, headers, cookies."""
    return {
        "basic": {"username": "user", "password": "pass"},
        "headers": {"X-API-Key": "secret"},
        "cookies": {"session": "abc123"},
    }
