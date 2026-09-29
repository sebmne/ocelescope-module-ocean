from typing import Annotated

from fastapi import APIRouter, Depends

from ocelescope_module_socel.api_schema import ApiModel
from ocelescope_module_socel.overview.api.dependencies import get_flow_inventory
from ocelescope_module_socel.overview.application.use_cases.get_flow_inventory import (
    GetFlowInventory,
    GetFlowInventoryCommand,
)
from ocelescope_module_socel.overview.domain.models.flow_inventory import (
    FlowInstanceSummary,
    FlowSummary,
)

router = APIRouter(tags=["sOCEL overview"])


class FlowInstanceModel(ApiModel):
    object_id: str
    object_type: str
    parent_object_id: str | None
    interval_records: int
    event_records: int

    @classmethod
    def from_domain(cls, instance: FlowInstanceSummary) -> "FlowInstanceModel":
        return cls(
            object_id=instance.object_id,
            object_type=instance.object_type,
            parent_object_id=instance.parent_object_id,
            interval_records=instance.interval_records,
            event_records=instance.event_records,
        )


class FlowModel(ApiModel):
    flow_id: str
    unit: str
    category: str | None
    external_ref: str | None
    instances: list[FlowInstanceModel]

    @classmethod
    def from_domain(cls, flow: FlowSummary) -> "FlowModel":
        return cls(
            flow_id=flow.flow_id,
            unit=flow.unit,
            category=flow.category,
            external_ref=flow.external_ref,
            instances=[FlowInstanceModel.from_domain(i) for i in flow.instances],
        )


@router.get(
    "/{ocel_id}/flows",
    operation_id="getFlowInventory",
    responses={409: {"description": "The OCEL has no sOCEL tables."}},
)
def get_flows(
    ocel_id: str, use_case: Annotated[GetFlowInventory, Depends(get_flow_inventory)]
) -> list[FlowModel]:
    """The flows, each with its flow instances, their metering scopes and records."""
    command = GetFlowInventoryCommand(ocel_id=ocel_id)
    result = use_case.execute(command)
    response = [FlowModel.from_domain(flow) for flow in result]
    return response
