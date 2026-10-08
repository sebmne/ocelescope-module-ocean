from socel import SOCEL

from ocelescope_module_socel.application.command import Command
from ocelescope_module_socel.application.ports.socel_statistics import SocelStatistics
from ocelescope_module_socel.domain.models.flow_inventory import FlowSummary


class GetFlowInventoryCommand(Command):
    socel: SOCEL


class GetFlowInventory:
    """The flows of an sOCEL with their counts, over the log and per object type."""

    def __init__(self, *, statistics: SocelStatistics) -> None:
        self._statistics = statistics

    def execute(self, command: GetFlowInventoryCommand) -> tuple[FlowSummary, ...]:
        return self._statistics.flows(command.socel)
