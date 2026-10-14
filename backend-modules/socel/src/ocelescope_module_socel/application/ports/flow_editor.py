from collections.abc import Sequence
from typing import Protocol

from ocelescope import OCEL

from ocelescope_module_socel.domain.models.flow_edit import FlowEdit


class FlowEditor(Protocol):
    """Renames, redefines, converts and deletes a log's flows, with their records
    and containment."""

    def flow_ids(self, ocel: OCEL) -> set[str]:
        """The flows the log declares; none when it has no sOCEL tables."""
        ...

    def edit(self, ocel: OCEL, edits: Sequence[FlowEdit]) -> None:
        """Applies the edits to the log; the names they leave are unique."""
        ...
