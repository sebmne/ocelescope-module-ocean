from collections.abc import Mapping
from typing import Protocol

from ocelescope import OCEL

from ocelescope_module_socel.domain.models.record_file import (
    ColumnMapping,
    FlowDefinition,
    RecordFileColumns,
    RecordFilePreview,
)


class RecordImporter(Protocol):
    """Reads a record file: a CSV whose columns are told apart by a mapping
    (flow, object, quantity, start_time, end_time, event; the last three as far
    as the file has them). A row is one of:

    - an interval record: flow, object, quantity, start_time and end_time;
    - an event-linked record: flow, object, quantity and event, with end_time if
      the event has a duration;
    - an event's end alone: event and end_time, nothing else.

    Raises:
        InvalidRecordFile: If the content is no such file.
    """

    def columns(self, ocel: OCEL, content: bytes) -> RecordFileColumns:
        """The file's columns and its first rows."""
        ...

    def preview(self, ocel: OCEL, content: bytes, mapping: ColumnMapping) -> RecordFilePreview:
        """What the file holds and which of its rows fit the log."""
        ...

    def write(
        self,
        ocel: OCEL,
        content: bytes,
        mapping: ColumnMapping,
        flows: Mapping[str, FlowDefinition],
    ) -> None:
        """Adds the file's usable rows to the log's sOCEL tables as records of the
        defined flows, and those flows with them; rows of other flows are left
        out. Events the file gives an end time get it."""
        ...
