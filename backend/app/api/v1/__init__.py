"""API v1 router aggregation."""

from fastapi import APIRouter

from app.api.v1.alerts import router as alerts_router
from app.api.v1.auth import router as auth_router
from app.api.v1.prices import router as prices_router
from app.api.v1.trips import router as trips_router
from app.api.v1.watches import router as watches_router

api_v1_router = APIRouter(prefix="/api/v1")
api_v1_router.include_router(auth_router)
api_v1_router.include_router(trips_router)
api_v1_router.include_router(prices_router)
api_v1_router.include_router(watches_router)
api_v1_router.include_router(alerts_router)
