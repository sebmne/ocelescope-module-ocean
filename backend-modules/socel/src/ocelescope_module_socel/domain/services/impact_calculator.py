from collections.abc import Sequence

from ocelescope_module_socel.domain.models.flow_quantities import FlowQuantity
from ocelescope_module_socel.domain.models.impact_analysis import (
    DirectionFactors,
    FlowImpact,
    ImpactAnalysis,
    ImpactReport,
    PeriodImpact,
)


class ImpactCalculator:
    """Combine directional impacts into a report without performing I/O.

    Unlike a single factor on the signed net quantity, each direction has
    its own factor on its nonnegative amount. Factor application belongs to
    DirectionFactors; combining flows and periods belongs here.
    """

    def calculate(self, flows: Sequence[FlowQuantity], analysis: ImpactAnalysis) -> ImpactReport:
        rows: list[FlowImpact] = []
        periods: list[PeriodImpact] = []
        for flow in flows:
            factors = analysis.factors.get(flow.flow_id, DirectionFactors())
            rows.append(
                FlowImpact(
                    flow_id=flow.flow_id,
                    unit=flow.unit,
                    inflow=flow.inflow,
                    outflow=flow.outflow,
                    factors=factors,
                    impact=factors.apply(inflow=flow.inflow, outflow=flow.outflow),
                )
            )
            for part in flow.by_period:
                impact = factors.apply(inflow=part.inflow, outflow=part.outflow)
                if impact is not None:
                    periods.append(
                        PeriodImpact(start=part.start, flow_id=flow.flow_id, impact=impact)
                    )
        return ImpactReport(
            flows=tuple(rows),
            total=sum(row.impact for row in rows if row.impact is not None),
            by_period=tuple(sorted(periods, key=lambda part: (part.start, part.flow_id))),
        )
