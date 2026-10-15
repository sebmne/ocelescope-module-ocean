from typing import Annotated

from fastapi import APIRouter, Depends, Query

from ocelescope_module_socel.api.dependencies import get_flow_instances
from ocelescope_module_socel.api.models.flow_instance_page import FlowInstancePage
from ocelescope_module_socel.api.models.pagination import Pagination
from ocelescope_module_socel.application.ports.socel_statistics import InstanceOrder
from ocelescope_module_socel.application.use_cases.get_flow_instances import (
    GetFlowInstances,
    GetFlowInstancesCommand,
)

router = APIRouter()


@router.get(
    "/flows/{flow_id}/instances",
    operation_id="getFlowInstances",
    responses={
        404: {"description": "The flow does not exist."},
        422: {"description": "The OCEL is no sOCEL, or pagination is invalid."},
    },
)
def get_instances(
    flow_id: str,
    use_case: Annotated[GetFlowInstances, Depends(get_flow_instances)],
    pagination: Annotated[Pagination, Depends()],
    object_type: Annotated[str | None, Query(description="Keep the objects of one type.")] = None,
    inside: Annotated[
        str | None, Query(description="Keep objects directly inside this one.")
    ] = None,
    search: Annotated[
        str | None, Query(description="Keep object ids containing this text.")
    ] = None,
    order: InstanceOrder = "quantity",
) -> FlowInstancePage:
    items, total, path = use_case.execute(
        GetFlowInstancesCommand(
            flow_id=flow_id,
            object_type=object_type,
            inside=inside,
            search=search,
            order=order,
            offset=pagination.offset,
            limit=pagination.limit,
        )
    )
    return FlowInstancePage.from_result(pagination, items, total, path=path)
