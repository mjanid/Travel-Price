"""Alert history route handlers."""

import uuid

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.security import get_current_user
from app.models.user import User
from app.schemas.alert import AlertResponse
from app.schemas.common import ApiResponse, PaginatedApiResponse
from app.services.alert_service import AlertService

router = APIRouter(prefix="/alerts", tags=["alerts"])


@router.get("/", response_model=PaginatedApiResponse[AlertResponse])
async def list_alerts(
    page: int = Query(default=1, ge=1),
    per_page: int = Query(default=20, ge=1, le=100),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> PaginatedApiResponse[AlertResponse]:
    """List alerts for the authenticated user with pagination."""
    service = AlertService(db)
    alerts, total = await service.list_alerts_for_user(
        current_user.id, page, per_page
    )
    return PaginatedApiResponse.create(alerts, total, page, per_page)


@router.get("/{alert_id}", response_model=ApiResponse[AlertResponse])
async def get_alert(
    alert_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> ApiResponse[AlertResponse]:
    """Get a single alert by ID."""
    service = AlertService(db)
    alert = await service.get_alert_by_id(current_user.id, alert_id)
    return ApiResponse(data=alert)
