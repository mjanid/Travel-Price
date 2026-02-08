"""Business logic for price watch management."""

import uuid

from fastapi import HTTPException, status
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.price_watch import PriceWatch
from app.models.trip import Trip
from app.schemas.price_watch import (
    PriceWatchCreateRequest,
    PriceWatchResponse,
    PriceWatchUpdateRequest,
)


class PriceWatchService:
    """Service handling price watch CRUD operations.

    Args:
        db: The async database session.
    """

    def __init__(self, db: AsyncSession) -> None:
        self.db = db

    async def create(
        self, user_id: uuid.UUID, payload: PriceWatchCreateRequest
    ) -> PriceWatchResponse:
        """Create a new price watch for the given user.

        Args:
            user_id: The owner's user ID.
            payload: Watch creation data.

        Returns:
            The created watch's data.

        Raises:
            HTTPException: 404 if trip not found or not owned by user.
        """
        result = await self.db.execute(
            select(Trip).where(Trip.id == payload.trip_id, Trip.user_id == user_id)
        )
        if result.scalar_one_or_none() is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Trip not found",
            )

        watch = PriceWatch(
            user_id=user_id,
            trip_id=payload.trip_id,
            provider=payload.provider,
            target_price=payload.target_price,
            currency=payload.currency,
            alert_cooldown_hours=payload.alert_cooldown_hours,
        )
        self.db.add(watch)
        await self.db.flush()
        await self.db.refresh(watch)
        return PriceWatchResponse.model_validate(watch)

    async def get_by_id(
        self, user_id: uuid.UUID, watch_id: uuid.UUID
    ) -> PriceWatchResponse:
        """Get a single price watch by ID, enforcing ownership.

        Args:
            user_id: The requesting user's ID.
            watch_id: The watch to retrieve.

        Returns:
            The watch data.

        Raises:
            HTTPException: 404 if not found or not owned by user.
        """
        watch = await self._get_watch_or_404(user_id, watch_id)
        return PriceWatchResponse.model_validate(watch)

    async def list_for_user(
        self, user_id: uuid.UUID, page: int = 1, per_page: int = 20
    ) -> tuple[list[PriceWatchResponse], int]:
        """List price watches for a user with pagination.

        Args:
            user_id: The owner's user ID.
            page: Page number (1-indexed).
            per_page: Items per page.

        Returns:
            Tuple of (list of watch responses, total count).
        """
        conditions = [PriceWatch.user_id == user_id]
        return await self._paginated_list(conditions, page, per_page)

    async def list_for_trip(
        self,
        user_id: uuid.UUID,
        trip_id: uuid.UUID,
        page: int = 1,
        per_page: int = 20,
    ) -> tuple[list[PriceWatchResponse], int]:
        """List price watches for a specific trip with pagination.

        Args:
            user_id: The owner's user ID.
            trip_id: The trip to filter by.
            page: Page number (1-indexed).
            per_page: Items per page.

        Returns:
            Tuple of (list of watch responses, total count).
        """
        conditions = [PriceWatch.user_id == user_id, PriceWatch.trip_id == trip_id]
        return await self._paginated_list(conditions, page, per_page)

    async def update(
        self,
        user_id: uuid.UUID,
        watch_id: uuid.UUID,
        payload: PriceWatchUpdateRequest,
    ) -> PriceWatchResponse:
        """Partially update a price watch.

        Args:
            user_id: The requesting user's ID.
            watch_id: The watch to update.
            payload: Fields to update.

        Returns:
            The updated watch data.

        Raises:
            HTTPException: 404 if not found or not owned by user.
        """
        watch = await self._get_watch_or_404(user_id, watch_id)

        update_data = payload.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(watch, field, value)

        await self.db.flush()
        await self.db.refresh(watch)
        return PriceWatchResponse.model_validate(watch)

    async def delete(self, user_id: uuid.UUID, watch_id: uuid.UUID) -> None:
        """Delete a price watch, enforcing ownership.

        Args:
            user_id: The requesting user's ID.
            watch_id: The watch to delete.

        Raises:
            HTTPException: 404 if not found or not owned by user.
        """
        watch = await self._get_watch_or_404(user_id, watch_id)
        await self.db.delete(watch)
        await self.db.flush()

    async def _get_watch_or_404(
        self, user_id: uuid.UUID, watch_id: uuid.UUID
    ) -> PriceWatch:
        """Fetch a price watch by ID scoped to the given user.

        Raises:
            HTTPException: 404 if not found or not owned by user.
        """
        result = await self.db.execute(
            select(PriceWatch).where(
                PriceWatch.id == watch_id, PriceWatch.user_id == user_id
            )
        )
        watch = result.scalar_one_or_none()
        if watch is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Price watch not found",
            )
        return watch

    async def _paginated_list(
        self,
        conditions: list,
        page: int,
        per_page: int,
    ) -> tuple[list[PriceWatchResponse], int]:
        """Run a paginated query with the given conditions."""
        count_result = await self.db.execute(
            select(func.count()).select_from(PriceWatch).where(*conditions)
        )
        total = count_result.scalar_one()

        offset = (page - 1) * per_page
        result = await self.db.execute(
            select(PriceWatch)
            .where(*conditions)
            .order_by(PriceWatch.created_at.desc())
            .offset(offset)
            .limit(per_page)
        )
        watches = result.scalars().all()
        return [PriceWatchResponse.model_validate(w) for w in watches], total
