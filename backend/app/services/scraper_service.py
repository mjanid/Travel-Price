"""Business logic for scraping and storing price snapshots."""

from __future__ import annotations

import json
import uuid

from fastapi import HTTPException, status
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.price_snapshot import PriceSnapshot
from app.models.trip import Trip
from app.scrapers.registry import get_scraper
from app.scrapers.types import PriceResult, ScrapeError, ScrapeQuery
from app.schemas.price_snapshot import PriceSnapshotResponse


class ScraperService:
    """Service that orchestrates scraping and stores results as PriceSnapshots.

    Args:
        db: The async database session.
    """

    def __init__(self, db: AsyncSession) -> None:
        self.db = db

    async def scrape_trip(
        self,
        trip_id: uuid.UUID,
        user_id: uuid.UUID,
        provider: str = "google_flights",
        cabin_class: str = "economy",
    ) -> list[PriceSnapshotResponse]:
        """Scrape prices for a trip and store results.

        Args:
            trip_id: The trip to scrape prices for.
            user_id: The requesting user's ID (ownership check).
            provider: Scraper provider name.
            cabin_class: Desired cabin class.

        Returns:
            List of stored price snapshot responses.

        Raises:
            HTTPException: 404 if trip not found, 400 if scraper fails,
                422 if provider is unknown.
        """
        trip = await self._get_trip_or_404(user_id, trip_id)

        try:
            scraper = get_scraper(provider)
        except ValueError as exc:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail=str(exc),
            )

        query = ScrapeQuery(
            origin=trip.origin,
            destination=trip.destination,
            departure_date=trip.departure_date,
            return_date=trip.return_date,
            travelers=trip.travelers,
            cabin_class=cabin_class,
            trip_id=trip.id,
            user_id=user_id,
        )

        try:
            results = await scraper.execute(query)
        except ScrapeError as exc:
            raise HTTPException(
                status_code=status.HTTP_502_BAD_GATEWAY,
                detail=f"Scraping failed: {exc}",
            )

        snapshots = await self._store_results(results, trip_id, user_id)
        return snapshots

    async def get_price_history(
        self,
        trip_id: uuid.UUID,
        user_id: uuid.UUID,
        page: int = 1,
        per_page: int = 20,
        provider: str | None = None,
    ) -> tuple[list[PriceSnapshotResponse], int]:
        """Get paginated price history for a trip.

        Args:
            trip_id: The trip to get prices for.
            user_id: The requesting user's ID (ownership check).
            page: Page number (1-indexed).
            per_page: Items per page.
            provider: Optional filter by provider name.

        Returns:
            Tuple of (list of price snapshot responses, total count).

        Raises:
            HTTPException: 404 if trip not found.
        """
        await self._get_trip_or_404(user_id, trip_id)

        conditions = [
            PriceSnapshot.trip_id == trip_id,
            PriceSnapshot.user_id == user_id,
        ]
        if provider:
            conditions.append(PriceSnapshot.provider == provider)

        count_result = await self.db.execute(
            select(func.count())
            .select_from(PriceSnapshot)
            .where(*conditions)
        )
        total = count_result.scalar_one()

        offset = (page - 1) * per_page
        result = await self.db.execute(
            select(PriceSnapshot)
            .where(*conditions)
            .order_by(PriceSnapshot.scraped_at.desc())
            .offset(offset)
            .limit(per_page)
        )
        snapshots = result.scalars().all()
        return [PriceSnapshotResponse.model_validate(s) for s in snapshots], total

    async def _store_results(
        self,
        results: list[PriceResult],
        trip_id: uuid.UUID,
        user_id: uuid.UUID,
    ) -> list[PriceSnapshotResponse]:
        """Store scrape results as PriceSnapshot records.

        Args:
            results: List of PriceResult from the scraper.
            trip_id: Associated trip ID.
            user_id: Associated user ID.

        Returns:
            List of stored PriceSnapshotResponse objects.
        """
        snapshots: list[PriceSnapshotResponse] = []
        for result in results:
            raw_data_str = None
            if result.raw_data is not None:
                try:
                    raw_data_str = json.dumps(result.raw_data, default=str)
                except (TypeError, ValueError):
                    raw_data_str = str(result.raw_data)

            snapshot = PriceSnapshot(
                trip_id=trip_id,
                user_id=user_id,
                provider=result.provider,
                price=result.price,
                currency=result.currency,
                cabin_class=result.cabin_class,
                airline=result.airline,
                outbound_departure=result.outbound_departure,
                outbound_arrival=result.outbound_arrival,
                return_departure=result.return_departure,
                return_arrival=result.return_arrival,
                stops=result.stops,
                raw_data=raw_data_str,
                scraped_at=result.scraped_at,
            )
            self.db.add(snapshot)
            await self.db.flush()
            await self.db.refresh(snapshot)
            snapshots.append(PriceSnapshotResponse.model_validate(snapshot))

        return snapshots

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
