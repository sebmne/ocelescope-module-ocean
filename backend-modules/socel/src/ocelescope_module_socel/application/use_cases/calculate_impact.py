from dataclasses import dataclass

from ocelescope_module_socel.application.ports.flow_analysis import FlowAnalysis
from ocelescope_module_socel.domain.models.impact_analysis import ImpactAnalysis, ImpactReport
from ocelescope_module_socel.domain.services.impact_calculator import ImpactCalculator


@dataclass(frozen=True, kw_only=True)
class CalculateImpactCommand:
    analysis: ImpactAnalysis


class CalculateImpact:
    """Read aggregate quantities and coordinate their domain calculation."""

    def __init__(self, *, flows: FlowAnalysis, calculator: ImpactCalculator) -> None:
        self._flows = flows
        self._calculator = calculator

    def execute(self, command: CalculateImpactCommand) -> ImpactReport:
        quantities = self._flows.quantities(command.analysis.period)
        return self._calculator.calculate(quantities, command.analysis)
