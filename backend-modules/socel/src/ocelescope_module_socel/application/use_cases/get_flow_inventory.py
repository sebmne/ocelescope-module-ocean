from dataclasses import dataclass

from ocelescope_module_socel.application.ports.socel_statistics import SocelStatistics
from ocelescope_module_socel.domain.models.flow_inventory import FlowSummary


@dataclass(frozen=True, kw_only=True)
class GetFlowInventoryCommand:
    pass


class GetFlowInventory:
    def __init__(self, *, statistics: SocelStatistics) -> None:
        self._statistics = statistics

    def execute(self, command: GetFlowInventoryCommand) -> tuple[FlowSummary, ...]:
        return self._statistics.flows()
