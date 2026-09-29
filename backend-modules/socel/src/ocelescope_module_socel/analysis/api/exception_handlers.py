from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

from ocelescope_module_socel.analysis.domain.exceptions import (
    AnalysisError,
    NotAnSocelError,
    UnknownFlowError,
)

# Error -> HTTP status, most specific first: the first matching entry wins.
_STATUS_CODES: dict[type[AnalysisError], int] = {
    NotAnSocelError: 409,
    UnknownFlowError: 404,
    AnalysisError: 400,
}


def register_exception_handlers(app: FastAPI) -> None:
    @app.exception_handler(AnalysisError)
    async def handle(_: Request, exc: AnalysisError) -> JSONResponse:
        status = next(code for cls, code in _STATUS_CODES.items() if isinstance(exc, cls))
        return JSONResponse(status_code=status, content={"detail": str(exc)})
