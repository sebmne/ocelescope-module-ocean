from typing import Annotated

from fastapi import APIRouter, Depends, Query

from ocelescope_module_socel.api.dependencies import get_flow_records
from ocelescope_module_socel.api.models.pagination import Page, Pagination
from ocelescope_module_socel.application.use_cases.get_flow_records import (
    GetFlowRecords,
    GetFlowRecordsCommand,
)
from ocelescope_module_socel.domain.models.flow_inventory import FlowRecord

router = APIRouter()


@router.get(
    "/flows/{flow_id}/records",
    operation_id="getFlowRecords",
    responses={
        404: {"description": "The flow does not exist."},
        422: {"description": "The OCEL is no sOCEL, or pagination is invalid."},
    },
)
def get_records(
    flow_id: str,
    object_id: Annotated[str, Query(description="The object the records are at.")],
    use_case: Annotated[GetFlowRecords, Depends(get_flow_records)],
    pagination: Annotated[Pagination, Depends()],
) -> Page[FlowRecord]:
    items, total = use_case.execute(
        GetFlowRecordsCommand(
            flow_id=flow_id,
            object_id=object_id,
            offset=pagination.offset,
            limit=pagination.limit,
        )
    )
    return Page[FlowRecord].from_result(pagination, items, total)
