"""Tests for notification dispatchers."""

import uuid

import pytest

from app.notifications.base import BaseNotifier, NotificationPayload
from app.notifications.email import LogEmailNotifier, get_notifier


def _make_payload() -> NotificationPayload:
    """Create a test notification payload."""
    return NotificationPayload(
        recipient_email="test@example.com",
        recipient_name="Test User",
        subject="Price Drop Alert",
        body="A flight is now $200.00",
        alert_id=uuid.uuid4(),
    )


async def test_log_email_notifier_returns_true():
    """LogEmailNotifier.send() always returns True."""
    notifier = LogEmailNotifier()
    result = await notifier.send(_make_payload())
    assert result is True


async def test_log_email_notifier_is_base_notifier():
    """LogEmailNotifier implements BaseNotifier."""
    notifier = LogEmailNotifier()
    assert isinstance(notifier, BaseNotifier)


def test_get_notifier_email():
    """get_notifier('email') returns LogEmailNotifier."""
    notifier = get_notifier("email")
    assert isinstance(notifier, LogEmailNotifier)


def test_get_notifier_unknown_channel():
    """get_notifier raises ValueError for unknown channel."""
    with pytest.raises(ValueError, match="Unknown notification channel"):
        get_notifier("sms")


def test_notification_payload_fields():
    """NotificationPayload has all required fields."""
    payload = _make_payload()
    assert payload.recipient_email == "test@example.com"
    assert payload.recipient_name == "Test User"
    assert payload.subject == "Price Drop Alert"
    assert payload.body == "A flight is now $200.00"
    assert isinstance(payload.alert_id, uuid.UUID)
