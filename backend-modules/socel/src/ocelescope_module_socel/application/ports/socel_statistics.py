from typing import Literal, Protocol

from socel import SOCEL

from ocelescope_module_socel.domain.models.class_counts import ClassCounts
from ocelescope_module_socel.domain.models.flow_inventory import FlowInstancePage, FlowSummary
from ocelescope_module_socel.domain.models.socel_status import SocelStatus

# How a page of flow instances is ordered: largest quantity first, or by object id.
type InstanceOrder = Literal["quantity", "object"]


class SocelStatistics(Protocol):
    """Counts over an sOCEL. Logs hold hundreds of thousands of events and
    objects, so nothing here walks them one by one, and single objects are only
    returned a page at a time: no answer grows with the log."""

    def status(self, socel: SOCEL) -> SocelStatus:
        """What the sOCEL holds, in counts, and the period its records span."""
        ...

    def flows(self, socel: SOCEL) -> tuple[FlowSummary, ...]:
        """The flows with their counts, over the log and per object type."""
        ...

    def flow_instances(
        self,
        socel: SOCEL,
        flow_id: str,
        *,
        object_type: str | None,
        inside: str | None,
        search: str | None,
        order: InstanceOrder,
        offset: int,
        limit: int,
    ) -> FlowInstancePage:
        """A page of the objects a flow is observed at. `object_type` keeps one
        type, `inside` the objects directly inside the given one, `search` those
        whose id contains the text."""
        ...

    def class_counts(self, socel: SOCEL) -> ClassCounts:
        """How many objects and events carry each sOCEL class, most frequent
        first; the unclassified ones under None."""
        ...
