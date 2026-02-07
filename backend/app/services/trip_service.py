"""Business logic for trip management."""

import uuid

from fastapi import HTTPException, status
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.trip import Trip
from app.schemas.trip import TripCreateRequest, TripResponse, TripUpdateRequest


class TripService:
    """Service handling trip CRUD operations.

    Args:
        db: The async database session.
    """

    def __init__(self, db: AsyncSession) -> None:
        self.db = db

    async def create(
        self, user_id: uuid.UUID, payload: TripCreateRequest
    ) -> TripResponse:
        """Create a new trip for the given user.

        Args:
            user_id: The owner's user ID.
            payload: Trip creation data.

        Returns:
            The created trip's data.
        """
        trip = Trip(
            user_id=user_id,
            origin=payload.origin,
            destination=payload.destination,
            departure_date=payload.departure_date,
            return_date=payload.return_date,
            travelers=payload.travelers,
            trip_type=payload.trip_type.value,
            notes=payload.notes,
        )
        self.db.add(trip)
        await self.db.flush()
        await self.db.refresh(trip)
        return TripResponse.model_validate(trip)

    async def get_by_id(
        self, user_id: uuid.UUID, trip_id: uuid.UUID
    ) -> TripResponse:
        """Get a single trip by ID, enforcing ownership.

        Args:
            user_id: The requesting user's ID.
            trip_id: The trip to retrieve.

        Returns:
            The trip data.

        Raises:
            HTTPException: 404 if not found or not owned by user.
        """
        trip = await self._get_trip_or_404(user_id, trip_id)
        return TripResponse.model_validate(trip)

    async def list(
        self, user_id: uuid.UUID, page: int = 1, per_page: int = 20
    ) -> tuple[list[TripResponse], int]:
        """List trips for a user with pagination.

        Args:
            user_id: The owner's user ID.
            page: Page number (1-indexed).
            per_page: Items per page.

        Returns:
            Tuple of (list of trip responses, total count).
        """
        count_result = await self.db.execute(
            select(func.count()).select_from(Trip).where(Trip.user_id == user_id)
        )
        total = count_result.scalar_one()

        offset = (page - 1) * per_page
        result = await self.db.execute(
            select(Trip)
            .where(Trip.user_id == user_id)
            .order_by(Trip.departure_date.asc())
            .offset(offset)
            .limit(per_page)
        )
        trips = result.scalars().all()
        return [TripResponse.model_validate(t) for t in trips], total

    async def update(
        self, user_id: uuid.UUID, trip_id: uuid.UUID, payload: TripUpdateRequest
    ) -> TripResponse:
        """Partially update a trip, enforcing ownership.

        Args:
            user_id: The requesting user's ID.
            trip_id: The trip to update.
            payload: Fields to update (only non-None values applied).

        Returns:
            The updated trip data.

        Raises:
            HTTPException: 404 if not found or not owned by user.
        """
        trip = await self._get_trip_or_404(user_id, trip_id)
        update_data = payload.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            if field == "trip_type" and value is not None:
                value = value.value
            setattr(trip, field, value)
        await self.db.flush()
        await self.db.refresh(trip)
        return TripResponse.model_validate(trip)

    async def delete(self, user_id: uuid.UUID, trip_id: uuid.UUID) -> None:
        """Delete a trip, enforcing ownership.

        Args:
            user_id: The requesting user's ID.
            trip_id: The trip to delete.

        Raises:
            HTTPException: 404 if not found or not owned by user.
        """
        trip = await self._get_trip_or_404(user_id, trip_id)
        await self.db.delete(trip)
        await self.db.flush()

    async def _get_trip_or_404(self, user_id: uuid.UUID, trip_id: uuid.UUID) -> Trip:
        """Fetch a trip by ID scoped to the given user.

        Raises:
            HTTPException: 404 if not found or not owned by user.
        """
        result = await self.db.execute(
            select(Trip).where(Trip.id == trip_id, Trip.user_id == user_id)
        )
        trip = result.scalar_one_or_none()
        if trip is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Trip not found",
            )
        return trip
