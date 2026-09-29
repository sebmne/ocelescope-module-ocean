from fastapi import APIRouter

from ocelescope_module_socel.overview.api.routes import classes, export, flows, status, validation

# Everything the overview offers, under /overview in the module's API.
router = APIRouter(prefix="/overview")
router.include_router(status.router)
router.include_router(flows.router)
router.include_router(classes.router)
router.include_router(validation.router)
router.include_router(export.router)
