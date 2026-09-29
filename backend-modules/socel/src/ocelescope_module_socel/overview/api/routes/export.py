from typing import Annotated

from fastapi import APIRouter, Depends, Response

from ocelescope_module_socel.overview.api.dependencies import get_export_socel
from ocelescope_module_socel.overview.application.use_cases.export_socel import (
    ExportSocel,
    ExportSocelCommand,
)

router = APIRouter(tags=["sOCEL overview"])


@router.get(
    "/{ocel_id}/export",
    operation_id="exportSocel",
    response_class=Response,
    responses={
        200: {
            "content": {
                "application/octet-stream": {"schema": {"type": "string", "format": "binary"}}
            },
            "description": "The sOCEL as SQLite, its tables as the thesis declares them.",
        },
        409: {"description": "The OCEL has no sOCEL tables."},
        422: {"description": "The sOCEL does not conform to V1–V9."},
    },
)
def export_socel(
    ocel_id: str, use_case: Annotated[ExportSocel, Depends(get_export_socel)]
) -> Response:
    """The sOCEL as its SQLite serialization (Section 5.5), validated first."""
    command = ExportSocelCommand(ocel_id=ocel_id)
    result = use_case.execute(command)
    return Response(
        content=result.content,
        media_type="application/octet-stream",
        headers={"Content-Disposition": f'attachment; filename="{result.file_name}"'},
    )
