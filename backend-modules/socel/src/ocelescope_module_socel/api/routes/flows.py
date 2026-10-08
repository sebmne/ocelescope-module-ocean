from typing import Annotated, Literal

from fastapi import APIRouter, Depends, Query

from ocelescope_module_socel.api.dependencies import (
    ApiSocel,
    get_flow_instances,
    get_flow_inventory,
)
from ocelescope_module_socel.api.schema import ApiModel
from ocelescope_module_socel.application.use_cases.get_flow_instances import (
    MAX_PAGE_SIZE,
    GetFlowInstances,
    GetFlowInstancesCommand,
)
from ocelescope_module_socel.application.use_cases.get_flow_inventory import (
    GetFlowInventory,
    GetFlowInventoryCommand,
)
from ocelescope_module_socel.domain.models.flow_inventory import (
    FlowByObjectType,
    FlowInstancePage,
    FlowInstanceRow,
    FlowSummary,
)

router = APIRouter(tags=["sOCEL"])


class FlowByObjectTypeModel(ApiModel):
    # The flow at the objects of one type: its flow instances there, how many of
    # them lie inside another instance, and their records.
    object_type: str
    instances: int
    contained: int
    interval_records: int
    event_records: int

    @classmethod
    def from_domain(cls, part: FlowByObjectType) -> "FlowByObjectTypeModel":
        return cls(
            object_type=part.object_type,
            instances=part.instances,
            contained=part.contained,
            interval_records=part.interval_records,
            event_records=part.event_records,
        )


class FlowModel(ApiModel):
    flow_id: str
    unit: str
    category: str | None
    external_ref: str | None
    instances: int
    contained: int
    interval_records: int
    event_records: int
    by_object_type: list[FlowByObjectTypeModel]

    @classmethod
    def from_domain(cls, flow: FlowSummary) -> "FlowModel":
        return cls(
            flow_id=flow.flow_id,
            unit=flow.unit,
            category=flow.category,
            external_ref=flow.external_ref,
            instances=flow.instances,
            contained=flow.contained,
            interval_records=flow.interval_records,
            event_records=flow.event_records,
            by_object_type=[FlowByObjectTypeModel.from_domain(p) for p in flow.by_object_type],
        )


@router.get(
    "/{ocel_id}/flows",
    operation_id="getFlowInventory",
    responses={422: {"description": "The OCEL is no sOCEL."}},
)
def get_flows(
    socel: ApiSocel, use_case: Annotated[GetFlowInventory, Depends(get_flow_inventory)]
) -> list[FlowModel]:
    """The flows with their counts, over the log and per object type."""
    result = use_case.execute(GetFlowInventoryCommand(socel=socel))
    response = [FlowModel.from_domain(flow) for flow in result]
    return response


class FlowInstanceModel(ApiModel):
    object_id: str
    object_type: str
    # The object it lies inside for this flow, and how many lie directly inside it.
    parent_object_id: str | None
    contains: int
    interval_records: int
    event_records: int
    # What its records sum to, in the flow's unit.
    quantity: float

    @classmethod
    def from_domain(cls, row: FlowInstanceRow) -> "FlowInstanceModel":
        return cls(
            object_id=row.object_id,
            object_type=row.object_type,
            parent_object_id=row.parent_object_id,
            contains=row.contains,
            interval_records=row.interval_records,
            event_records=row.event_records,
            quantity=row.quantity,
        )


class FlowInstancePageModel(ApiModel):
    # How many objects there are in all under the same filter.
    total: int
    rows: list[FlowInstanceModel]
    # With `inside`: the objects from the outermost one down to it.
    path: list[str]

    @classmethod
    def from_domain(cls, page: FlowInstancePage) -> "FlowInstancePageModel":
        return cls(
            total=page.total,
            rows=[FlowInstanceModel.from_domain(row) for row in page.rows],
            path=list(page.path),
        )


@router.get(
    "/{ocel_id}/flows/{flow_id}/instances",
    operation_id="getFlowInstances",
    responses={422: {"description": "The OCEL is no sOCEL."}},
)
def get_instances(
    socel: ApiSocel,
    flow_id: str,
    use_case: Annotated[GetFlowInstances, Depends(get_flow_instances)],
    object_type: Annotated[str | None, Query(description="Keep the objects of one type.")] = None,
    inside: Annotated[
        str | None, Query(description="Keep the objects directly inside this one.")
    ] = None,
    search: Annotated[
        str | None, Query(description="Keep the objects whose id contains this.")
    ] = None,
    order: Literal["quantity", "object"] = "quantity",
    offset: Annotated[int, Query(ge=0)] = 0,
    limit: Annotated[int, Query(ge=1, le=MAX_PAGE_SIZE)] = 50,
) -> FlowInstancePageModel:
    """A page of the objects the flow is observed at: what they lie inside, what
    lies inside them, and their records."""
    result = use_case.execute(
        GetFlowInstancesCommand(
            socel=socel,
            flow_id=flow_id,
            object_type=object_type,
            inside=inside,
            search=search,
            order=order,
            offset=offset,
            limit=limit,
        )
    )
    response = FlowInstancePageModel.from_domain(result)
    return response
