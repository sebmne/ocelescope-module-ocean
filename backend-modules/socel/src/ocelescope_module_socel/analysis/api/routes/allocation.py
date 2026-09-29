from typing import Annotated

from fastapi import APIRouter, Depends

from ocelescope_module_socel.analysis.api.dependencies import get_allocation
from ocelescope_module_socel.analysis.application.use_cases.get_allocation import (
    GetAllocation,
    GetAllocationCommand,
)
from ocelescope_module_socel.analysis.domain.models.flow_allocation import (
    AllocationOverview,
    FlowAllocation,
    UnitAllocation,
)
from ocelescope_module_socel.api_schema import ApiModel

router = APIRouter(tags=["sOCEL analysis"])


class UnitAllocationModel(ApiModel):
    object_id: str
    object_type: str
    allocated: float
    carried: float | None
    is_end_unit: bool

    @classmethod
    def from_domain(cls, unit: UnitAllocation) -> "UnitAllocationModel":
        return cls(
            object_id=unit.object_id,
            object_type=unit.object_type,
            allocated=unit.allocated,
            carried=unit.carried,
            is_end_unit=unit.is_end_unit,
        )


class FlowAllocationModel(ApiModel):
    flow_id: str
    unit: str
    recorded: float
    attributed: float
    allocated: float
    unallocated: float
    units: list[UnitAllocationModel]
    unit_count: int

    @classmethod
    def from_domain(cls, flow: FlowAllocation) -> "FlowAllocationModel":
        return cls(
            flow_id=flow.flow_id,
            unit=flow.unit,
            recorded=flow.recorded,
            attributed=flow.attributed,
            allocated=flow.allocated,
            unallocated=flow.unallocated,
            units=[UnitAllocationModel.from_domain(u) for u in flow.units],
            unit_count=flow.unit_count,
        )


class AllocationOverviewModel(ApiModel):
    flows: list[FlowAllocationModel]
    has_lineage: bool
    lineage_problem: str | None

    @classmethod
    def from_domain(cls, overview: AllocationOverview) -> "AllocationOverviewModel":
        return cls(
            flows=[FlowAllocationModel.from_domain(f) for f in overview.flows],
            has_lineage=overview.has_lineage,
            lineage_problem=overview.lineage_problem,
        )


@router.get(
    "/{ocel_id}/allocation",
    operation_id="getAllocation",
    responses={409: {"description": "The OCEL has no sOCEL tables."}},
)
def get_unit_allocation(
    ocel_id: str, use_case: Annotated[GetAllocation, Depends(get_allocation)]
) -> AllocationOverviewModel:
    """Every flow allocated to the handling units of its operations, and carried
    down their lineage."""
    command = GetAllocationCommand(ocel_id=ocel_id)
    result = use_case.execute(command)
    response = AllocationOverviewModel.from_domain(result)
    return response
