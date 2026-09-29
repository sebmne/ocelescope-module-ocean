from typing import Annotated

from fastapi import APIRouter, Depends

from ocelescope_module_socel.analysis.api.dependencies import get_impact
from ocelescope_module_socel.analysis.application.use_cases.get_impact import (
    GetImpact,
    GetImpactCommand,
)
from ocelescope_module_socel.analysis.domain.models.impact_overview import (
    ActivityImpact,
    EndUnitFootprint,
    FlowImpact,
    FootprintBin,
    ImpactOverview,
)
from ocelescope_module_socel.api_schema import ApiModel

router = APIRouter(tags=["sOCEL analysis"])


class FlowImpactModel(ApiModel):
    flow_id: str
    unit: str
    impact_per_unit: float
    recorded: float
    attributed: float
    allocated: float

    @classmethod
    def from_domain(cls, flow: FlowImpact) -> "FlowImpactModel":
        return cls(
            flow_id=flow.flow_id,
            unit=flow.unit,
            impact_per_unit=flow.impact_per_unit,
            recorded=flow.recorded,
            attributed=flow.attributed,
            allocated=flow.allocated,
        )


class ActivityImpactModel(ApiModel):
    activity: str
    impact: float
    operations: int

    @classmethod
    def from_domain(cls, activity: ActivityImpact) -> "ActivityImpactModel":
        return cls(
            activity=activity.activity, impact=activity.impact, operations=activity.operations
        )


class EndUnitFootprintModel(ApiModel):
    object_id: str
    object_type: str
    footprint: float
    mass: float | None
    footprint_per_kg: float | None

    @classmethod
    def from_domain(cls, unit: EndUnitFootprint) -> "EndUnitFootprintModel":
        return cls(
            object_id=unit.object_id,
            object_type=unit.object_type,
            footprint=unit.footprint,
            mass=unit.mass,
            footprint_per_kg=unit.footprint_per_kg,
        )


class FootprintBinModel(ApiModel):
    lower: float
    upper: float
    end_units: int

    @classmethod
    def from_domain(cls, bin: FootprintBin) -> "FootprintBinModel":
        return cls(lower=bin.lower, upper=bin.upper, end_units=bin.end_units)


class ImpactOverviewModel(ApiModel):
    recorded: float
    attributed: float
    allocated: float
    flows: list[FlowImpactModel]
    activities: list[ActivityImpactModel]
    end_units: list[EndUnitFootprintModel]
    end_unit_count: int
    median_footprint_per_kg: float | None
    footprint_bins: list[FootprintBinModel]
    lineage_problem: str | None

    @classmethod
    def from_domain(cls, overview: ImpactOverview) -> "ImpactOverviewModel":
        return cls(
            recorded=overview.recorded,
            attributed=overview.attributed,
            allocated=overview.allocated,
            flows=[FlowImpactModel.from_domain(f) for f in overview.flows],
            activities=[ActivityImpactModel.from_domain(a) for a in overview.activities],
            end_units=[EndUnitFootprintModel.from_domain(u) for u in overview.end_units],
            end_unit_count=overview.end_unit_count,
            median_footprint_per_kg=overview.median_footprint_per_kg,
            footprint_bins=[FootprintBinModel.from_domain(b) for b in overview.footprint_bins],
            lineage_problem=overview.lineage_problem,
        )


@router.get(
    "/{ocel_id}/impact",
    operation_id="getImpact",
    responses={409: {"description": "The OCEL has no sOCEL tables."}},
)
def get_flow_impact(
    ocel_id: str, use_case: Annotated[GetImpact, Depends(get_impact)]
) -> ImpactOverviewModel:
    """The traced flows in kg CO2e with the emission factors set: per flow, per
    activity, per end unit."""
    command = GetImpactCommand(ocel_id=ocel_id)
    result = use_case.execute(command)
    response = ImpactOverviewModel.from_domain(result)
    return response
