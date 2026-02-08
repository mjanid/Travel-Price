"""Email notification dispatcher."""

from __future__ import annotations

import logging

from app.notifications.base import BaseNotifier, NotificationPayload

logger = logging.getLogger(__name__)


class LogEmailNotifier(BaseNotifier):
    """Email notifier that logs messages instead of sending via SMTP.

    For MVP/development use. Replace with an SMTP-based notifier for production.
    """

    async def send(self, payload: NotificationPayload) -> bool:
        """Log the email notification.

        Args:
            payload: The notification data.

        Returns:
            Always True (logging never fails).
        """
        logger.info(
            "EMAIL ALERT [to=%s, subject=%s]: %s",
            payload.recipient_email,
            payload.subject,
            payload.body,
        )
        return True


def get_notifier(channel: str = "email") -> BaseNotifier:
    """Return a notifier instance for the given channel.

    Args:
        channel: The notification channel name.

    Returns:
        A BaseNotifier implementation.

    Raises:
        ValueError: If the channel is not supported.
    """
    if channel == "email":
        return LogEmailNotifier()
    raise ValueError(f"Unknown notification channel: {channel}")
