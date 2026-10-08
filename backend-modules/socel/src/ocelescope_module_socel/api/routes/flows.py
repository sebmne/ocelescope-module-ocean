from typing import Annotated

from fastapi import APIRouter, Depends

from ocelescope_module_socel.api.dependencies import ApiSocel, get_flow_inventory
from ocelescope_module_socel.api.schema import ApiModel
from ocelescope_module_socel.application.use_cases.get_flow_inventory import (
    GetFlowInventory,
    GetFlowInventoryCommand,
)
from ocelescope_module_socel.domain.models.flow_inventory import FlowByObjectType, FlowSummary

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
