from dataclasses import dataclass

from ocelescope_module_socel.application.ports.socel_statistics import (
    RecordSlice,
    SocelStatistics,
)


@dataclass(frozen=True, kw_only=True)
class GetFlowRecordsCommand:
    flow_id: str
    object_id: str
    offset: int
    limit: int


class GetFlowRecords:
    def __init__(self, *, statistics: SocelStatistics) -> None:
        self._statistics = statistics

    def execute(self, command: GetFlowRecordsCommand) -> RecordSlice:
        if command.offset < 0 or command.limit < 1:
            raise ValueError("Offset must be nonnegative and limit must be positive.")
        return self._statistics.flow_records(
            command.flow_id, command.object_id, offset=command.offset, limit=command.limit
        )
