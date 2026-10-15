from dataclasses import dataclass

from ocelescope_module_socel.application.ports.socel_statistics import SocelStatistics
from ocelescope_module_socel.domain.models.class_counts import ClassCounts


@dataclass(frozen=True, kw_only=True)
class GetClassCountsCommand:
    pass


class GetClassCounts:
    def __init__(self, *, statistics: SocelStatistics) -> None:
        self._statistics = statistics

    def execute(self, command: GetClassCountsCommand) -> ClassCounts:
        return self._statistics.class_counts()
