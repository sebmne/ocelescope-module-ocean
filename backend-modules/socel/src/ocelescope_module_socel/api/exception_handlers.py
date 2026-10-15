from math import isfinite

from fastapi import FastAPI, Request
from fastapi.encoders import jsonable_encoder
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse

from ocelescope_module_socel.application.errors import FlowNotFound
from ocelescope_module_socel.domain.exceptions import SocelBuildError


def register_exception_handlers(app: FastAPI) -> None:
    """Maps the module's own errors to HTTP statuses."""

    @app.exception_handler(FlowNotFound)
    def _(request: Request, error: FlowNotFound) -> JSONResponse:
        return JSONResponse(status_code=404, content={"detail": str(error)})

    @app.exception_handler(SocelBuildError)
    def _(request: Request, error: SocelBuildError) -> JSONResponse:
        return JSONResponse(status_code=422, content={"detail": str(error)})

    @app.exception_handler(RequestValidationError)
    def _(request: Request, error: RequestValidationError) -> JSONResponse:
        # Pydantic rejects nonfinite factors, but its error echoes the input.
        # Encode those values as text so the error itself is valid JSON.
        return JSONResponse(
            status_code=422,
            content=jsonable_encoder(
                {"detail": error.errors()},
                custom_encoder={float: lambda value: value if isfinite(value) else str(value)},
            ),
        )
