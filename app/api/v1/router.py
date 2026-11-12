"""API v1 router aggregating all endpoint routers."""

from fastapi import APIRouter

from app.api.v1.endpoints import estimate, greeks, health, required_spot, target_price

router = APIRouter()

router.include_router(health.router, tags=["Health"])
router.include_router(estimate.router, prefix="/options", tags=["Options Pricing"])
router.include_router(target_price.router, prefix="/options", tags=["Options Pricing"])
router.include_router(required_spot.router, prefix="/options", tags=["Options Pricing"])
router.include_router(greeks.router, prefix="/options", tags=["Options Pricing"])

