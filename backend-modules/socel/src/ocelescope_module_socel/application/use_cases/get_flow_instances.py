from dataclasses import dataclass

from ocelescope_module_socel.application.ports.socel_statistics import (
    InstanceOrder,
    InstanceSlice,
    SocelStatistics,
)


@dataclass(frozen=True, kw_only=True)
class GetFlowInstancesCommand:
    flow_id: str
    offset: int
    limit: int
    object_type: str | None = None
    inside: str | None = None
    search: str | None = None
    order: InstanceOrder = "quantity"


class GetFlowInstances:
    def __init__(self, *, statistics: SocelStatistics) -> None:
        self._statistics = statistics

    def execute(self, command: GetFlowInstancesCommand) -> InstanceSlice:
        if command.offset < 0 or command.limit < 1:
            raise ValueError("Offset must be nonnegative and limit must be positive.")
        search = command.search.strip() or None if command.search is not None else None
        return self._statistics.flow_instances(
            command.flow_id,
            object_type=command.object_type or None,
            inside=command.inside or None,
            search=search,
            order=command.order,
            offset=command.offset,
            limit=command.limit,
        )
