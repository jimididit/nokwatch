"""Unit tests for core.crypto (credential encryption for auth and notification config)."""
import pytest
from cryptography.fernet import Fernet

from core import crypto
from core.config import Config


@pytest.fixture
def encryption_key(monkeypatch):
    """Set a valid Fernet key for tests that need encryption."""
    key = Fernet.generate_key().decode()
    monkeypatch.setattr(Config, "ENCRYPTION_KEY", key)
    crypto._reset_for_tests()
    return key


@pytest.fixture
def no_encryption_key(monkeypatch):
    """Ensure no encryption key is set."""
    monkeypatch.setattr(Config, "ENCRYPTION_KEY", "")
    crypto._reset_for_tests()


class TestEncryptDecryptRoundTrip:
    def test_round_trip_with_key(self, encryption_key):
        plain = '{"basic": {"username": "u", "password": "p"}}'
        encrypted = crypto.encrypt_credentials(plain)
        assert encrypted != plain
        assert isinstance(encrypted, str)
        decrypted = crypto.decrypt_credentials(encrypted)
        assert decrypted == plain

    def test_round_trip_notification_config(self, encryption_key):
        plain = '{"webhook_url": "https://discord.com/api/webhooks/secret"}'
        encrypted = crypto.encrypt_credentials(plain)
        assert encrypted != plain
        decrypted = crypto.decrypt_credentials(encrypted)
        assert decrypted == plain

    def test_empty_string_with_key(self, encryption_key):
        assert crypto.encrypt_credentials("") == ""
        assert crypto.decrypt_credentials("") is None
        assert crypto.decrypt_credentials(None) is None


class TestNoEncryptionKey:
    def test_encrypt_returns_plaintext_when_no_key(self, no_encryption_key):
        plain = '{"basic": {"username": "u", "password": "p"}}'
        result = crypto.encrypt_credentials(plain)
        assert result == plain

    def test_decrypt_returns_plaintext_when_no_key(self, no_encryption_key):
        plain = '{"basic": {"username": "u", "password": "p"}}'
        result = crypto.decrypt_credentials(plain)
        assert result == plain


class TestLegacyPlaintextPassthrough:
    """When DB contains unencrypted (legacy) data, decrypt returns it unchanged."""

    def test_decrypt_plain_json_returns_unchanged_with_key_set(self, encryption_key):
        legacy = '{"basic": {"username": "u", "password": "p"}}'
        result = crypto.decrypt_credentials(legacy)
        assert result == legacy

    def test_decrypt_invalid_fernet_returns_unchanged(self, encryption_key):
        not_fernet = "not-encrypted-data"
        result = crypto.decrypt_credentials(not_fernet)
        assert result == not_fernet
