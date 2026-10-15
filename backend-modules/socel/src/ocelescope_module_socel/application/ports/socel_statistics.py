from typing import Literal, Protocol

from ocelescope_module_socel.domain.models.class_counts import ClassCounts
from ocelescope_module_socel.domain.models.flow_inventory import FlowInstanceRow, FlowSummary
from ocelescope_module_socel.domain.models.socel_status import SocelStatus

# Items, total matching the filters, and containment breadcrumbs.
type InstanceSlice = tuple[tuple[FlowInstanceRow, ...], int, tuple[str, ...]]
type InstanceOrder = Literal["quantity", "object"]


class SocelStatistics(Protocol):
    """Aggregate and bounded reads over the log/view bound by the entry adapter."""

    def status(self) -> SocelStatus: ...

    def flows(self) -> tuple[FlowSummary, ...]: ...

    def flow_instances(
        self,
        flow_id: str,
        *,
        object_type: str | None,
        inside: str | None,
        search: str | None,
        order: InstanceOrder,
        offset: int,
        limit: int,
    ) -> InstanceSlice:
        """Return a slice with its total; raise FlowNotFound for a missing flow."""
        ...

    def class_counts(self) -> ClassCounts: ...
