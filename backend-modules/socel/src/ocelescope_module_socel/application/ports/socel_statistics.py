from typing import Protocol

from socel import SOCEL

from ocelescope_module_socel.domain.models.class_counts import ClassCounts
from ocelescope_module_socel.domain.models.flow_inventory import FlowSummary
from ocelescope_module_socel.domain.models.socel_status import SocelStatus


class SocelStatistics(Protocol):
    """Counts over an sOCEL. Logs hold hundreds of thousands of events and
    objects, so nothing here returns or walks single ones: every answer is as
    large as the number of flows, classes and object types, not of the log."""

    def status(self, socel: SOCEL) -> SocelStatus:
        """What the sOCEL holds, in counts, and the period its records span."""
        ...

    def flows(self, socel: SOCEL) -> tuple[FlowSummary, ...]:
        """The flows with their counts, over the log and per object type."""
        ...

    def class_counts(self, socel: SOCEL) -> ClassCounts:
        """How many objects and events carry each sOCEL class, most frequent
        first; the unclassified ones under None."""
        ...
