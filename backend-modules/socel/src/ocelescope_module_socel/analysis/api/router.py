from fastapi import APIRouter

from ocelescope_module_socel.analysis.api.routes import (
    allocation,
    attribution,
    impact,
    series,
    settings,
)

# Everything the analysis offers, under /analysis in the module's API.
router = APIRouter(prefix="/analysis")
router.include_router(settings.router)
router.include_router(series.router)
router.include_router(attribution.router)
router.include_router(allocation.router)
router.include_router(impact.router)
