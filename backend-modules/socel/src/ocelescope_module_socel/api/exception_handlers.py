from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

from ocelescope_module_socel.domain.exceptions import SocelBuildError


def register_exception_handlers(app: FastAPI) -> None:
    """Maps the module's own errors to HTTP statuses."""

    @app.exception_handler(SocelBuildError)
    def _(request: Request, error: SocelBuildError) -> JSONResponse:
        return JSONResponse(status_code=422, content={"detail": str(error)})
