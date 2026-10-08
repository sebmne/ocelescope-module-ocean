from socel import SOCEL

from ocelescope_module_socel.application.command import Command
from ocelescope_module_socel.application.ports.socel_statistics import SocelStatistics
from ocelescope_module_socel.domain.models.class_counts import ClassCounts


class GetClassCountsCommand(Command):
    socel: SOCEL


class GetClassCounts:
    """How many objects and events carry each sOCEL class, most frequent first;
    the unclassified ones under None."""

    def __init__(self, *, statistics: SocelStatistics) -> None:
        self._statistics = statistics

    def execute(self, command: GetClassCountsCommand) -> ClassCounts:
        return self._statistics.class_counts(command.socel)
