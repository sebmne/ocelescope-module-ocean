from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

from ocelescope_module_socel.overview.domain.exceptions import (
    NotAnSocelError,
    NotConformingError,
    OverviewError,
)

# Error -> HTTP status, most specific first: the first matching entry wins.
_STATUS_CODES: dict[type[OverviewError], int] = {
    NotAnSocelError: 409,
    NotConformingError: 422,
    OverviewError: 400,
}


def register_exception_handlers(app: FastAPI) -> None:
    @app.exception_handler(OverviewError)
    async def handle(_: Request, exc: OverviewError) -> JSONResponse:
        status = next(code for cls, code in _STATUS_CODES.items() if isinstance(exc, cls))
        return JSONResponse(status_code=status, content={"detail": str(exc)})
