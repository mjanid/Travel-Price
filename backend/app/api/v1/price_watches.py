"""Price watch CRUD route handlers."""

import uuid

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.security import get_current_user
from app.models.user import User
from app.schemas.common import ApiResponse, PaginatedApiResponse
from app.schemas.price_watch import (
    PriceWatchCreateRequest,
    PriceWatchResponse,
    PriceWatchUpdateRequest,
)
from app.services.price_watch_service import PriceWatchService

router = APIRouter(tags=["price-watches"])


# --- Nested under trips ---


@router.post(
    "/trips/{trip_id}/watches",
    response_model=ApiResponse[PriceWatchResponse],
    status_code=201,
)
async def create_price_watch(
    trip_id: uuid.UUID,
    payload: PriceWatchCreateRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> ApiResponse[PriceWatchResponse]:
    """Create a new price watch for a trip."""
    service = PriceWatchService(db)
    watch = await service.create(current_user.id, trip_id, payload)
    return ApiResponse(data=watch)


@router.get(
    "/trips/{trip_id}/watches",
    response_model=PaginatedApiResponse[PriceWatchResponse],
)
async def list_price_watches(
    trip_id: uuid.UUID,
    page: int = Query(default=1, ge=1),
    per_page: int = Query(default=20, ge=1, le=100),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> PaginatedApiResponse[PriceWatchResponse]:
    """List price watches for a trip with pagination."""
    service = PriceWatchService(db)
    watches, total = await service.list_by_trip(
        current_user.id, trip_id, page, per_page
    )
    return PaginatedApiResponse.create(watches, total, page, per_page)


# --- Flat routes for direct access ---


@router.get(
    "/watches/{watch_id}",
    response_model=ApiResponse[PriceWatchResponse],
)
async def get_price_watch(
    watch_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> ApiResponse[PriceWatchResponse]:
    """Get a single price watch by ID."""
    service = PriceWatchService(db)
    watch = await service.get_by_id(current_user.id, watch_id)
    return ApiResponse(data=watch)


@router.patch(
    "/watches/{watch_id}",
    response_model=ApiResponse[PriceWatchResponse],
)
async def update_price_watch(
    watch_id: uuid.UUID,
    payload: PriceWatchUpdateRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> ApiResponse[PriceWatchResponse]:
    """Partially update a price watch."""
    service = PriceWatchService(db)
    watch = await service.update(current_user.id, watch_id, payload)
    return ApiResponse(data=watch)


@router.delete("/watches/{watch_id}", status_code=204)
async def delete_price_watch(
    watch_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> None:
    """Delete a price watch."""
    service = PriceWatchService(db)
    await service.delete(current_user.id, watch_id)
