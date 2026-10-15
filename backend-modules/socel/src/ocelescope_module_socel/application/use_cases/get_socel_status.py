from dataclasses import dataclass

from ocelescope_module_socel.application.ports.socel_statistics import SocelStatistics
from ocelescope_module_socel.domain.models.socel_status import SocelStatus


@dataclass(frozen=True, kw_only=True)
class GetSocelStatusCommand:
    pass


class GetSocelStatus:
    def __init__(self, *, statistics: SocelStatistics) -> None:
        self._statistics = statistics

    def execute(self, command: GetSocelStatusCommand) -> SocelStatus:
        return self._statistics.status()
