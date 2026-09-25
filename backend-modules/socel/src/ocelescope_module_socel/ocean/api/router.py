from fastapi import APIRouter

from ocelescope_module_socel.ocean.api.routes import allocation, emission_rules, emissions

# Everything OCEAn offers, under /ocean in the module's API.
router = APIRouter(prefix="/ocean")
router.include_router(emission_rules.router)
router.include_router(emissions.router)
router.include_router(allocation.router)
