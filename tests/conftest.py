"""Pytest fixtures for Nokwatch tests (plan: unit tests per service, integration, mocked AI)."""
import os
import sys
import tempfile
from pathlib import Path
import pytest

# Use a dedicated test DB so we don't touch the dev DB (set before any app/config import)
if "DATABASE_PATH" not in os.environ:
    os.environ["DATABASE_PATH"] = os.path.join(tempfile.gettempdir(), "nokwatch_test.db")

# Allow importing nokwatch_scan when running from project root (plugin not pip-installed)
_plugin_src = Path(__file__).resolve().parent.parent / "plugins" / "nokwatch-scan" / "src"
if _plugin_src.exists() and str(_plugin_src) not in sys.path:
    sys.path.insert(0, str(_plugin_src))

# Ensure test DB has base + plugin columns (so job_type / listing_scan tests can run)
from core.models import get_db, init_db

init_db()
try:
    from nokwatch_scan.migrations import run_migrations
    run_migrations(get_db)
except ImportError:
    pass


@pytest.fixture
def client():
    """Flask test client for API tests."""
    from app import app
    app.config["TESTING"] = True
    return app.test_client()


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
