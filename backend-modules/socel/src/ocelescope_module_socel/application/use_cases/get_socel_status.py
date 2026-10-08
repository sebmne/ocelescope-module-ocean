from socel import SOCEL

from ocelescope_module_socel.application.command import Command
from ocelescope_module_socel.application.ports.socel_statistics import SocelStatistics
from ocelescope_module_socel.domain.models.socel_status import SocelStatus


class GetSocelStatusCommand(Command):
    socel: SOCEL


class GetSocelStatus:
    """What the sOCEL holds, in counts, and the period its records span."""

    def __init__(self, *, statistics: SocelStatistics) -> None:
        self._statistics = statistics

    def execute(self, command: GetSocelStatusCommand) -> SocelStatus:
        return self._statistics.status(command.socel)
