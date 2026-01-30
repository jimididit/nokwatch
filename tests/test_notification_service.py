"""Unit/integration tests for services.notification_service (plan: integration tests for notification channels)."""
from unittest.mock import patch, MagicMock
import pytest
from services import notification_service


def test_send_notification_test_email_calls_email_sender(monkeypatch):
    """For is_test=True and email_recipient, send_notification calls email sender and returns its result."""
    sent = []

    def fake_email(job, match_status, is_test=False):
        sent.append((job.get("email_recipient"), is_test))
        return True

    monkeypatch.setattr(
        notification_service,
        "send_email_notification",
        fake_email,
    )
    job = {"id": 1, "email_recipient": "test@example.com"}
    match_status = {"match_found": True}
    result = notification_service.send_notification(job, match_status, is_test=True)
    assert result is True
    assert len(sent) == 1
    assert sent[0][0] == "test@example.com"
    assert sent[0][1] is True


def test_send_notification_test_email_no_recipient_returns_false():
    """For is_test=True and no email_recipient, send_notification returns False."""
    job = {"id": 0, "name": "Test"}
    match_status = {}
    result = notification_service.send_notification(job, match_status, is_test=True)
    assert result is False


def test_send_notification_no_job_id_returns_false():
    """When job has no id (and not test), send_notification returns False."""
    job = {"name": "No ID", "email_recipient": "x@y.com"}
    match_status = {}
    result = notification_service.send_notification(job, match_status, is_test=False)
    assert result is False
