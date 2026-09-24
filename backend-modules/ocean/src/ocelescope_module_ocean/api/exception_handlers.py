from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

from ocelescope_module_ocean.domain.exceptions import (
    AllocationIncompleteError,
    EmissionsNotComputedError,
    InvalidEmissionRuleError,
    NoTargetObjectsError,
    OceanError,
)

# Domain error -> HTTP status, most specific first: the first matching entry wins.
_STATUS_CODES: dict[type[OceanError], int] = {
    InvalidEmissionRuleError: 422,
    NoTargetObjectsError: 422,
    EmissionsNotComputedError: 409,
    AllocationIncompleteError: 500,
    OceanError: 400,
}


def register_exception_handlers(app: FastAPI) -> None:
    @app.exception_handler(OceanError)
    async def handle_ocean_error(_: Request, exc: OceanError) -> JSONResponse:
        status = next(code for cls, code in _STATUS_CODES.items() if isinstance(exc, cls))
        return JSONResponse(status_code=status, content={"detail": str(exc)})
