"""Price watch CRUD and alert history route handlers."""

import uuid

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.security import get_current_user
from app.models.user import User
from app.schemas.alert import AlertResponse
from app.schemas.common import ApiResponse, PaginatedApiResponse
from app.schemas.price_watch import (
    PriceWatchCreateRequest,
    PriceWatchResponse,
    PriceWatchUpdateRequest,
)
from app.services.alert_service import AlertService
from app.services.price_watch_service import PriceWatchService

router = APIRouter(prefix="/watches", tags=["watches"])


@router.post("/", response_model=ApiResponse[PriceWatchResponse], status_code=201)
async def create_watch(
    payload: PriceWatchCreateRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> ApiResponse[PriceWatchResponse]:
    """Create a new price watch for the authenticated user."""
    service = PriceWatchService(db)
    watch = await service.create(current_user.id, payload)
    return ApiResponse(data=watch)


@router.get("/", response_model=PaginatedApiResponse[PriceWatchResponse])
async def list_watches(
    page: int = Query(default=1, ge=1),
    per_page: int = Query(default=20, ge=1, le=100),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> PaginatedApiResponse[PriceWatchResponse]:
    """List price watches for the authenticated user with pagination."""
    service = PriceWatchService(db)
    watches, total = await service.list_for_user(current_user.id, page, per_page)
    return PaginatedApiResponse.create(watches, total, page, per_page)


@router.get("/{watch_id}", response_model=ApiResponse[PriceWatchResponse])
async def get_watch(
    watch_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> ApiResponse[PriceWatchResponse]:
    """Get a single price watch by ID."""
    service = PriceWatchService(db)
    watch = await service.get_by_id(current_user.id, watch_id)
    return ApiResponse(data=watch)


@router.patch("/{watch_id}", response_model=ApiResponse[PriceWatchResponse])
async def update_watch(
    watch_id: uuid.UUID,
    payload: PriceWatchUpdateRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> ApiResponse[PriceWatchResponse]:
    """Partially update a price watch."""
    service = PriceWatchService(db)
    watch = await service.update(current_user.id, watch_id, payload)
    return ApiResponse(data=watch)


@router.delete("/{watch_id}", status_code=204)
async def delete_watch(
    watch_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> None:
    """Delete a price watch."""
    service = PriceWatchService(db)
    await service.delete(current_user.id, watch_id)


@router.get(
    "/{watch_id}/alerts",
    response_model=PaginatedApiResponse[AlertResponse],
)
async def list_watch_alerts(
    watch_id: uuid.UUID,
    page: int = Query(default=1, ge=1),
    per_page: int = Query(default=20, ge=1, le=100),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> PaginatedApiResponse[AlertResponse]:
    """List alerts for a specific price watch."""
    service = AlertService(db)
    alerts, total = await service.list_alerts_for_watch(
        current_user.id, watch_id, page, per_page
    )
    return PaginatedApiResponse.create(alerts, total, page, per_page)
