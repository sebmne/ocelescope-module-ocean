import math
from datetime import datetime
from typing import Annotated, Literal

from fastapi import APIRouter, Depends
from pydantic import AfterValidator

from ocelescope_module_socel.api.dependencies import ApiSocel, get_calculate_impact
from ocelescope_module_socel.api.schema import ApiModel
from ocelescope_module_socel.application.use_cases.calculate_impact import (
    CalculateImpact,
    CalculateImpactCommand,
)
from ocelescope_module_socel.domain.models.flow_quantities import (
    DirectionFactors,
    FlowImpact,
    ImpactReport,
    PeriodImpact,
)

router = APIRouter(tags=["sOCEL"])


def _finite(factor: float) -> float:
    if not math.isfinite(factor):
        raise ValueError("A factor must be a finite number.")
    return factor


type Factor = Annotated[float, AfterValidator(_finite)]


class DirectionFactorsModel(ApiModel):
    # kg CO2e per unit flowing into the objects, and per unit flowing out of
    # them; None counts that direction not at all.
    inflow: Factor | None = None
    outflow: Factor | None = None

    @classmethod
    def from_domain(cls, factors: DirectionFactors) -> "DirectionFactorsModel":
        return cls(inflow=factors.inflow, outflow=factors.outflow)

    def to_domain(self) -> DirectionFactors:
        return DirectionFactors(inflow=self.inflow, outflow=self.outflow)


class ImpactRequest(ApiModel):
    period: Literal["hour", "day", "week", "month"] = "day"
    factors: dict[str, DirectionFactorsModel]


class FlowImpactModel(ApiModel):
    flow_id: str
    unit: str
    # What flows into the objects and out of them over the log, both positive,
    # in the flow's unit.
    inflow: float
    outflow: float
    factors: DirectionFactorsModel
    # kg CO2e; None without a factor.
    impact: float | None

    @classmethod
    def from_domain(cls, flow: FlowImpact) -> "FlowImpactModel":
        return cls(
            flow_id=flow.flow_id,
            unit=flow.unit,
            inflow=flow.inflow,
            outflow=flow.outflow,
            factors=DirectionFactorsModel.from_domain(flow.factors),
            impact=flow.impact,
        )


class PeriodImpactModel(ApiModel):
    # Where the period begins.
    start: datetime
    flow_id: str
    impact: float

    @classmethod
    def from_domain(cls, part: PeriodImpact) -> "PeriodImpactModel":
        return cls(start=part.start, flow_id=part.flow_id, impact=part.impact)


class ImpactReportModel(ApiModel):
    flows: list[FlowImpactModel]
    # kg CO2e of the flows with a factor.
    total: float
    by_period: list[PeriodImpactModel]

    @classmethod
    def from_domain(cls, report: ImpactReport) -> "ImpactReportModel":
        return cls(
            flows=[FlowImpactModel.from_domain(flow) for flow in report.flows],
            total=report.total,
            by_period=[PeriodImpactModel.from_domain(part) for part in report.by_period],
        )


@router.post(
    "/{ocel_id}/impact",
    operation_id="calculateImpact",
    responses={422: {"description": "The OCEL is no sOCEL, or a factor is no finite number."}},
)
def calculate_impact(
    socel: ApiSocel,
    request: ImpactRequest,
    use_case: Annotated[CalculateImpact, Depends(get_calculate_impact)],
) -> ImpactReportModel:
    """The impact of the flows with a factor, in kg CO2e: per flow, in all, and
    per period. Each direction has its own factor, applied to the amount that
    flows into or out of the objects. Each record counts by its share of the
    period; records of an
    instance inside one with records of its own are left out, as the outer
    records hold them already."""
    result = use_case.execute(
        CalculateImpactCommand(
            socel=socel,
            period=request.period,
            factors={flow: factors.to_domain() for flow, factors in request.factors.items()},
        )
    )
    response = ImpactReportModel.from_domain(result)
    return response
