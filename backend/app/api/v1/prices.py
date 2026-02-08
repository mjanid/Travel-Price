"""Price scraping and history route handlers."""

import uuid

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.security import get_current_user
from app.models.user import User
from app.schemas.common import ApiResponse, PaginatedApiResponse
from app.schemas.price_snapshot import PriceSnapshotResponse, ScrapeRequest
from app.schemas.price_watch import PriceWatchResponse
from app.services.price_watch_service import PriceWatchService
from app.services.scraper_service import ScraperService

router = APIRouter(prefix="/trips", tags=["prices"])


@router.post(
    "/{trip_id}/scrape",
    response_model=ApiResponse[list[PriceSnapshotResponse]],
    status_code=201,
)
async def scrape_trip(
    trip_id: uuid.UUID,
    payload: ScrapeRequest | None = None,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> ApiResponse[list[PriceSnapshotResponse]]:
    """Trigger a manual scrape for a trip and return the results.

    Args:
        trip_id: The trip to scrape prices for.
        payload: Optional scrape configuration (provider, cabin class).
        current_user: The authenticated user.
        db: Database session.

    Returns:
        API response containing the list of scraped price snapshots.
    """
    if payload is None:
        payload = ScrapeRequest()
    service = ScraperService(db)
    snapshots = await service.scrape_trip(
        trip_id=trip_id,
        user_id=current_user.id,
        provider=payload.provider,
        cabin_class=payload.cabin_class,
    )
    return ApiResponse(data=snapshots)


@router.get(
    "/{trip_id}/prices",
    response_model=PaginatedApiResponse[PriceSnapshotResponse],
)
async def get_price_history(
    trip_id: uuid.UUID,
    page: int = Query(default=1, ge=1),
    per_page: int = Query(default=20, ge=1, le=100),
    provider: str | None = Query(default=None),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> PaginatedApiResponse[PriceSnapshotResponse]:
    """Get paginated price history for a trip.

    Args:
        trip_id: The trip to get prices for.
        page: Page number.
        per_page: Items per page.
        provider: Optional filter by provider.
        current_user: The authenticated user.
        db: Database session.

    Returns:
        Paginated API response with price snapshots.
    """
    service = ScraperService(db)
    snapshots, total = await service.get_price_history(
        trip_id=trip_id,
        user_id=current_user.id,
        page=page,
        per_page=per_page,
        provider=provider,
    )
    return PaginatedApiResponse.create(snapshots, total, page, per_page)


@router.get(
    "/{trip_id}/watches",
    response_model=PaginatedApiResponse[PriceWatchResponse],
)
async def list_trip_watches(
    trip_id: uuid.UUID,
    page: int = Query(default=1, ge=1),
    per_page: int = Query(default=20, ge=1, le=100),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> PaginatedApiResponse[PriceWatchResponse]:
    """List price watches for a specific trip.

    Args:
        trip_id: The trip to list watches for.
        page: Page number.
        per_page: Items per page.
        current_user: The authenticated user.
        db: Database session.

    Returns:
        Paginated API response with price watches.
    """
    service = PriceWatchService(db)
    watches, total = await service.list_for_trip(
        user_id=current_user.id,
        trip_id=trip_id,
        page=page,
        per_page=per_page,
    )
    return PaginatedApiResponse.create(watches, total, page, per_page)
