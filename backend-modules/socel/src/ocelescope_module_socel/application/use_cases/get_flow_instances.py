from socel import SOCEL

from ocelescope_module_socel.application.command import Command
from ocelescope_module_socel.application.ports.socel_statistics import (
    InstanceOrder,
    SocelStatistics,
)
from ocelescope_module_socel.domain.models.flow_inventory import FlowInstancePage

MAX_PAGE_SIZE = 200


class GetFlowInstancesCommand(Command):
    socel: SOCEL
    flow_id: str
    """Keep the objects of one type; None for all."""
    object_type: str | None = None
    """Keep the objects directly inside this one; None for all."""
    inside: str | None = None
    """Keep the objects whose id contains this text; None for all."""
    search: str | None = None
    order: InstanceOrder = "quantity"
    offset: int = 0
    limit: int = 50


class GetFlowInstances:
    """A page of the objects a flow is observed at, with what they lie inside,
    what lies inside them, and their records. A log has too many objects to
    hand them out at once."""

    def __init__(self, *, statistics: SocelStatistics) -> None:
        self._statistics = statistics

    def execute(self, command: GetFlowInstancesCommand) -> FlowInstancePage:
        return self._statistics.flow_instances(
            command.socel,
            command.flow_id,
            object_type=command.object_type or None,
            inside=command.inside or None,
            search=(command.search or "").strip() or None,
            order=command.order,
            offset=max(0, command.offset),
            limit=min(max(1, command.limit), MAX_PAGE_SIZE),
        )
