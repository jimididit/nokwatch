"""Unit tests for monitoring.auth_handler (plan: unit tests for each new service)."""
import pytest
from monitoring.auth_handler import (
    parse_auth_config,
    build_request_auth,
    build_request_kwargs,
)


class TestParseAuthConfig:
    def test_none_returns_none(self):
        assert parse_auth_config(None) is None

    def test_empty_string_returns_none(self):
        assert parse_auth_config("") is None
        assert parse_auth_config("   ") is None

    def test_valid_json_returns_dict(self):
        cfg = parse_auth_config('{"basic": {"username": "u", "password": "p"}}')
        assert cfg == {"basic": {"username": "u", "password": "p"}}

    def test_invalid_json_returns_none(self):
        assert parse_auth_config("not json") is None
        assert parse_auth_config("{ broken }") is None


class TestBuildRequestAuth:
    def test_none_config_returns_empty(self):
        auth, headers, cookies = build_request_auth(None)
        assert auth is None
        assert headers == {}
        assert cookies == {}

    def test_basic_auth(self):
        config = {"basic": {"username": "u", "password": "p"}}
        auth, headers, cookies = build_request_auth(config)
        assert auth == ("u", "p")
        assert headers == {}
        assert cookies == {}

    def test_basic_auth_missing_password(self):
        config = {"basic": {"username": "u"}}
        auth, _, _ = build_request_auth(config)
        assert auth == ("u", "")

    def test_headers_dict(self):
        config = {"headers": {"X-Key": "val", "Accept": "application/json"}}
        auth, headers, _ = build_request_auth(config)
        assert auth is None
        assert headers == {"X-Key": "val", "Accept": "application/json"}

    def test_cookies_dict(self):
        config = {"cookies": {"sess": "xyz", "token": "t"}}
        auth, _, cookies = build_request_auth(config)
        assert auth is None
        assert cookies == {"sess": "xyz", "token": "t"}

    def test_combined_basic_headers_cookies(self, sample_auth_config):
        auth, headers, cookies = build_request_auth(sample_auth_config)
        assert auth == ("user", "pass")
        assert headers == {"X-API-Key": "secret"}
        assert cookies == {"session": "abc123"}


class TestBuildRequestKwargs:
    def test_job_without_auth_returns_empty(self, sample_job):
        sample_job["auth_config"] = None
        kwargs = build_request_kwargs(sample_job)
        assert kwargs == {}

    def test_job_with_auth_dict(self, sample_job, sample_auth_config):
        sample_job["auth_config"] = sample_auth_config
        kwargs = build_request_kwargs(sample_job)
        assert kwargs["auth"] == ("user", "pass")
        assert kwargs["headers"] == {"X-API-Key": "secret"}
        assert kwargs["cookies"] == {"session": "abc123"}

    def test_job_with_auth_json_string(self, sample_job):
        sample_job["auth_config"] = '{"basic": {"username": "j", "password": "p"}}'
        kwargs = build_request_kwargs(sample_job)
        assert kwargs["auth"] == ("j", "p")
