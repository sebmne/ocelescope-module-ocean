from typing import Annotated

from fastapi import APIRouter, Depends

from ocelescope_module_socel.api.dependencies import get_log_classification
from ocelescope_module_socel.application.use_cases.get_log_classification import (
    GetLogClassification,
    GetLogClassificationCommand,
)
from ocelescope_module_socel.domain.models.log_classification import LogClassification

router = APIRouter()


@router.get("/classification", operation_id="getLogClassification")
def get_classification(
    use_case: Annotated[GetLogClassification, Depends(get_log_classification)],
) -> LogClassification:
    """Return current classification for the selected view of any log."""
    return use_case.execute(GetLogClassificationCommand())
