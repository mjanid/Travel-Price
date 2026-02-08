"""Alert ORM model for sent notification records."""

import enum
import uuid
from datetime import datetime, timezone

from sqlalchemy import DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base


class AlertType(str, enum.Enum):
    """Types of price alerts."""

    PRICE_DROP = "price_drop"


class AlertChannel(str, enum.Enum):
    """Notification delivery channels."""

    EMAIL = "email"


class AlertStatus(str, enum.Enum):
    """Alert delivery status."""

    SENT = "sent"
    FAILED = "failed"


class Alert(Base):
    """An immutable record of a sent (or failed) price alert notification.

    Attributes:
        id: Unique identifier (UUID).
        price_watch_id: The watch that triggered this alert (FK).
        user_id: The user who owns this alert (FK).
        price_snapshot_id: The snapshot that triggered the alert (FK).
        alert_type: Type of alert (e.g. 'price_drop').
        channel: Delivery channel (e.g. 'email').
        status: Delivery status ('sent' or 'failed').
        target_price: The target price at time of alert (cents, denormalized).
        triggered_price: The actual price that triggered the alert (cents).
        message: The notification message body.
        sent_at: When the notification was delivered (None if failed).
        created_at: Record creation timestamp (UTC).
    """

    __tablename__ = "alerts"

    id: Mapped[uuid.UUID] = mapped_column(
        primary_key=True, default=uuid.uuid4
    )
    price_watch_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("price_watches.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )
    price_snapshot_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("price_snapshots.id", ondelete="CASCADE"), nullable=False
    )
    alert_type: Mapped[str] = mapped_column(
        String(20), nullable=False, default=AlertType.PRICE_DROP.value
    )
    channel: Mapped[str] = mapped_column(
        String(20), nullable=False, default=AlertChannel.EMAIL.value
    )
    status: Mapped[str] = mapped_column(String(20), nullable=False)
    target_price: Mapped[int] = mapped_column(Integer, nullable=False)
    triggered_price: Mapped[int] = mapped_column(Integer, nullable=False)
    message: Mapped[str | None] = mapped_column(Text, nullable=True)
    sent_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    created_at: Mapped[datetime] = mapped_column(
        default=lambda: datetime.now(timezone.utc)
    )

    price_watch = relationship("PriceWatch", backref="alerts")
    user = relationship("User", backref="alerts")
    price_snapshot = relationship("PriceSnapshot", backref="alerts")
