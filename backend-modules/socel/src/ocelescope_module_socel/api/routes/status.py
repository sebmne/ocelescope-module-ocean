from typing import Annotated

from fastapi import APIRouter, Depends

from ocelescope_module_socel.api.dependencies import get_socel_status
from ocelescope_module_socel.application.use_cases.get_socel_status import (
    GetSocelStatus,
    GetSocelStatusCommand,
)
from ocelescope_module_socel.domain.models.socel_status import SocelStatus

router = APIRouter()


@router.get(
    "/summary",
    operation_id="getSocelStatus",
    name="socel-summary",
    responses={422: {"description": "The OCEL is no sOCEL."}},
)
def get_status(use_case: Annotated[GetSocelStatus, Depends(get_socel_status)]) -> SocelStatus:
    return use_case.execute(GetSocelStatusCommand())
