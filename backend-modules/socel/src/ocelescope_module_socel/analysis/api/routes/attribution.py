from typing import Annotated

from fastapi import APIRouter, Depends

from ocelescope_module_socel.analysis.api.dependencies import get_attribution
from ocelescope_module_socel.analysis.application.use_cases.get_attribution import (
    GetAttribution,
    GetAttributionCommand,
)
from ocelescope_module_socel.analysis.domain.models.flow_attribution import (
    ActivityQuantity,
    FlowAttribution,
    MeterAttribution,
)
from ocelescope_module_socel.api_schema import ApiModel

router = APIRouter(tags=["sOCEL analysis"])


class ActivityQuantityModel(ApiModel):
    activity: str
    quantity: float
    operations: int

    @classmethod
    def from_domain(cls, activity: ActivityQuantity) -> "ActivityQuantityModel":
        return cls(
            activity=activity.activity, quantity=activity.quantity, operations=activity.operations
        )


class MeterAttributionModel(ApiModel):
    object_id: str
    object_type: str
    nested: bool
    recorded: float
    attributed: float
    remainder: float

    @classmethod
    def from_domain(cls, meter: MeterAttribution) -> "MeterAttributionModel":
        return cls(
            object_id=meter.object_id,
            object_type=meter.object_type,
            nested=meter.nested,
            recorded=meter.recorded,
            attributed=meter.attributed,
            remainder=meter.remainder,
        )


class FlowAttributionModel(ApiModel):
    flow_id: str
    unit: str
    recorded: float
    attributed: float
    remainder: float
    activities: list[ActivityQuantityModel]
    meters: list[MeterAttributionModel]

    @classmethod
    def from_domain(cls, flow: FlowAttribution) -> "FlowAttributionModel":
        return cls(
            flow_id=flow.flow_id,
            unit=flow.unit,
            recorded=flow.recorded,
            attributed=flow.attributed,
            remainder=flow.remainder,
            activities=[ActivityQuantityModel.from_domain(a) for a in flow.activities],
            meters=[MeterAttributionModel.from_domain(m) for m in flow.meters],
        )


@router.get(
    "/{ocel_id}/attribution",
    operation_id="getAttribution",
    responses={409: {"description": "The OCEL has no sOCEL tables."}},
)
def get_flow_attribution(
    ocel_id: str, use_case: Annotated[GetAttribution, Depends(get_attribution)]
) -> list[FlowAttributionModel]:
    """Every flow attributed to the operations it was recorded during: totals,
    activities, meters."""
    command = GetAttributionCommand(ocel_id=ocel_id)
    result = use_case.execute(command)
    response = [FlowAttributionModel.from_domain(flow) for flow in result]
    return response
