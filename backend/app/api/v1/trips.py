"""Trip CRUD route handlers."""

import uuid

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.security import get_current_user
from app.models.user import User
from app.schemas.common import ApiResponse, PaginatedApiResponse
from app.schemas.trip import TripCreateRequest, TripResponse, TripUpdateRequest
from app.services.trip_service import TripService

router = APIRouter(prefix="/trips", tags=["trips"])


@router.post("/", response_model=ApiResponse[TripResponse], status_code=201)
async def create_trip(
    payload: TripCreateRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> ApiResponse[TripResponse]:
    """Create a new trip for the authenticated user."""
    service = TripService(db)
    trip = await service.create(current_user.id, payload)
    return ApiResponse(data=trip)


@router.get("/", response_model=PaginatedApiResponse[TripResponse])
async def list_trips(
    page: int = Query(default=1, ge=1),
    per_page: int = Query(default=20, ge=1, le=100),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> PaginatedApiResponse[TripResponse]:
    """List trips for the authenticated user with pagination."""
    service = TripService(db)
    trips, total = await service.list(current_user.id, page, per_page)
    return PaginatedApiResponse.create(trips, total, page, per_page)


@router.get("/{trip_id}", response_model=ApiResponse[TripResponse])
async def get_trip(
    trip_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> ApiResponse[TripResponse]:
    """Get a single trip by ID."""
    service = TripService(db)
    trip = await service.get_by_id(current_user.id, trip_id)
    return ApiResponse(data=trip)


@router.patch("/{trip_id}", response_model=ApiResponse[TripResponse])
async def update_trip(
    trip_id: uuid.UUID,
    payload: TripUpdateRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> ApiResponse[TripResponse]:
    """Partially update a trip."""
    service = TripService(db)
    trip = await service.update(current_user.id, trip_id, payload)
    return ApiResponse(data=trip)


@router.delete("/{trip_id}", status_code=204)
async def delete_trip(
    trip_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> None:
    """Delete a trip."""
    service = TripService(db)
    await service.delete(current_user.id, trip_id)
