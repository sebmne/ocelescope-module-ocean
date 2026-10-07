from fastapi import APIRouter

from ocelescope_module_ocean.api.routes import allocation, emission_rules, emissions

# Everything OCEAn offers.
router = APIRouter()
router.include_router(emission_rules.router)
router.include_router(emissions.router)
router.include_router(allocation.router)
