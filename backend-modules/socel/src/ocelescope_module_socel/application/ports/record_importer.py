from collections.abc import Mapping
from typing import Protocol

from ocelescope import OCEL

from ocelescope_module_socel.domain.models.record_file import FlowDefinition, RecordFilePreview


class RecordImporter(Protocol):
    """Reads a record file: one flow record per row, with the columns flow,
    object, quantity, and either start_time and end_time or event.

    Raises:
        InvalidRecordFile: If the content is no such file.
    """

    def preview(self, ocel: OCEL, content: bytes) -> RecordFilePreview:
        """What the file holds and which of its rows fit the log."""
        ...

    def write(self, ocel: OCEL, content: bytes, flows: Mapping[str, FlowDefinition]) -> None:
        """Adds the file's usable rows to the log's sOCEL tables as records of the
        defined flows, and those flows with them. Rows of other flows are left out."""
        ...
