from collections.abc import Mapping, Sequence
from typing import Protocol

from ocelescope import OCEL

from ocelescope_module_socel.domain.models.attribute_flows import AttributeFlow
from ocelescope_module_socel.domain.models.record_file import FlowDefinition


class AttributeFlowImporter(Protocol):
    """Takes flows from the attributes of a log's events."""

    def write(
        self,
        ocel: OCEL,
        flows: Sequence[AttributeFlow],
        definitions: Mapping[str, FlowDefinition],
    ) -> None:
        """Adds one event-linked record per value to the log's sOCEL tables, and
        the flows with them where the log does not have them yet.

        Raises:
            UnknownAttribute: If the log's events have no numeric attribute of
                a flow's name.
        """
        ...
