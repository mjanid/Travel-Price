"""Base notification abstraction."""

from __future__ import annotations

import abc
import uuid
from dataclasses import dataclass


@dataclass
class NotificationPayload:
    """Data needed to send a notification.

    Attributes:
        recipient_email: The recipient's email address.
        recipient_name: The recipient's display name.
        subject: Notification subject line.
        body: Notification message body.
        alert_id: The associated Alert record ID.
    """

    recipient_email: str
    recipient_name: str
    subject: str
    body: str
    alert_id: uuid.UUID


class BaseNotifier(abc.ABC):
    """Abstract base for notification dispatchers."""

    @abc.abstractmethod
    async def send(self, payload: NotificationPayload) -> bool:
        """Send a notification.

        Args:
            payload: The notification data.

        Returns:
            True on success, False on failure.
        """
        ...
