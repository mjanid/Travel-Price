"""Response schema for alert endpoints."""

import uuid
from datetime import datetime

from pydantic import BaseModel


class AlertResponse(BaseModel):
    """Schema for alert data in API responses."""

    id: uuid.UUID
    price_watch_id: uuid.UUID
    user_id: uuid.UUID
    price_snapshot_id: uuid.UUID
    alert_type: str
    channel: str
    status: str
    target_price: int
    triggered_price: int
    message: str | None
    sent_at: datetime | None
    created_at: datetime

    model_config = {"from_attributes": True}
