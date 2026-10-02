from fastapi import APIRouter

from ocelescope_module_socel.api.routes import classes, flows, status

# Everything the module offers, by resource. Pages are the frontend's concern:
# a page uses whichever resources it needs.
router = APIRouter()
router.include_router(status.router)
router.include_router(flows.router)
router.include_router(classes.router)
