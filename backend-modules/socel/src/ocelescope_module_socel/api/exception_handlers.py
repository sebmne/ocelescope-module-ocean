from math import isfinite

from fastapi import FastAPI, Request
from fastapi.encoders import jsonable_encoder
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse

from ocelescope_module_socel.application.errors import FlowNotFound
from ocelescope_module_socel.domain.exceptions import SocelBuildError

# A handler also catches the subclasses of its error, so SocelBuildError
# covers every domain error.
_STATUS: dict[type[Exception], int] = {
    FlowNotFound: 404,
    SocelBuildError: 422,
}


def register_exception_handlers(app: FastAPI) -> None:
    """Maps the module's own errors to HTTP statuses."""
    for error_type, status in _STATUS.items():

        def handle(request: Request, error: Exception, status: int = status) -> JSONResponse:
            return JSONResponse(status_code=status, content={"detail": str(error)})

        app.add_exception_handler(error_type, handle)

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
