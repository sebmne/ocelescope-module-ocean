from collections.abc import Mapping

from socel import SOCEL
from socel.analysis import ImpactFactors, impact_quantity

from ocelescope_module_socel.application.command import Command
from ocelescope_module_socel.application.ports.socel_statistics import SocelStatistics
from ocelescope_module_socel.domain.models.flow_quantities import (
    DirectionFactors,
    FlowImpact,
    FlowQuantity,
    ImpactReport,
    Period,
    PeriodImpact,
)


class CalculateImpactCommand(Command):
    socel: SOCEL
    period: Period
    # Per flow; factors of flows the log does not have are ignored.
    factors: Mapping[str, DirectionFactors]


class CalculateImpact:
    """The impact of the flows with a factor, in all and per period.

    The thesis has one factor per flow, applied to the signed quantity (Def.
    6.4.1), so a flow out of the objects would lower the impact. Here each
    direction has its own factor on the positive amount: an emission is counted
    by its factor for what flows out, a purchased material by its factor for
    what flows in. Quantities are those of Def. 6.1.2, split by direction."""

    def __init__(self, *, statistics: SocelStatistics) -> None:
        self._statistics = statistics

    def execute(self, command: CalculateImpactCommand) -> ImpactReport:
        flows = self._statistics.flow_quantities(command.socel, command.period)
        given = {flow.flow_id: command.factors.get(flow.flow_id) for flow in flows}
        inflow = ImpactFactors(
            {f: d.inflow for f, d in given.items() if d is not None and d.inflow is not None}
        )
        outflow = ImpactFactors(
            {f: d.outflow for f, d in given.items() if d is not None and d.outflow is not None}
        )

        def impact(flow_id: str, into: float, out_of: float) -> float | None:
            parts = [
                impact_quantity(flow_id, amount, factors)
                for amount, factors in ((into, inflow), (out_of, outflow))
                if flow_id in factors.values
            ]
            return sum(parts) if parts else None

        def factors_of(flow: FlowQuantity) -> DirectionFactors:
            return DirectionFactors(
                inflow=inflow.values.get(flow.flow_id), outflow=outflow.values.get(flow.flow_id)
            )

        rows = tuple(
            FlowImpact(
                flow_id=flow.flow_id,
                unit=flow.unit,
                inflow=flow.inflow,
                outflow=flow.outflow,
                factors=factors_of(flow),
                impact=impact(flow.flow_id, flow.inflow, flow.outflow),
            )
            for flow in flows
        )
        by_period = tuple(
            sorted(
                (
                    PeriodImpact(start=part.start, flow_id=flow.flow_id, impact=value)
                    for flow in flows
                    for part in flow.by_period
                    if (value := impact(flow.flow_id, part.inflow, part.outflow)) is not None
                ),
                key=lambda part: (part.start, part.flow_id),
            )
        )
        return ImpactReport(
            flows=rows,
            total=sum(row.impact for row in rows if row.impact is not None),
            by_period=by_period,
        )
