"""API v1 router aggregation."""

from fastapi import APIRouter

from app.api.v1.auth import router as auth_router
from app.api.v1.price_watches import router as price_watches_router
from app.api.v1.trips import router as trips_router

api_v1_router = APIRouter(prefix="/api/v1")
api_v1_router.include_router(auth_router)
api_v1_router.include_router(trips_router)
api_v1_router.include_router(price_watches_router)
