from typing import Annotated

from fastapi import APIRouter, Depends

from ocelescope_module_socel.api.dependencies import get_class_counts
from ocelescope_module_socel.application.use_cases.get_class_counts import (
    GetClassCounts,
    GetClassCountsCommand,
)
from ocelescope_module_socel.domain.models.class_counts import ClassCounts

router = APIRouter()


@router.get(
    "/class-counts",
    operation_id="getClassCounts",
    responses={422: {"description": "The OCEL is no sOCEL."}},
)
def get_classes(use_case: Annotated[GetClassCounts, Depends(get_class_counts)]) -> ClassCounts:
    return use_case.execute(GetClassCountsCommand())
