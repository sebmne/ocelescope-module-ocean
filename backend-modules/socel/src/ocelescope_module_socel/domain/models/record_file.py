from datetime import datetime
from typing import Literal

from ocelescope_module_socel.domain.models.base import Model

# What keeps rows of a record file out of the sOCEL.
IssueKind = Literal[
    "unknown_object",
    "unknown_event",
    "missing_flow",
    "missing_object",
    "quantity_not_a_number",
    "neither_interval_nor_event",
    "time_not_readable",
    "end_not_after_start",
    "event_end_not_after_start",
    "conflicting_event_end",
]


class FlowDefinition(Model):
    """What a record file cannot know about a flow: set once, by hand.
    `external_ref` points to the flow in another system, e.g. a database of
    emission factors."""

    unit: str
    category: str
    external_ref: str | None = None


class FlowInFile(Model):
    """A flow named in a record file: its rows by kind, how many of all its rows
    can be taken over, and on how many objects. `known` is the flow's definition
    when the log already has the flow."""

    flow_id: str
    rows: int
    usable_rows: int
    interval_records: int
    event_records: int
    objects: int
    known: FlowDefinition | None


class RecordIssue(Model):
    """Rows that cannot be taken over, by reason; `examples` are a few of the ids
    not found in the log, or of the file's line numbers."""

    kind: IssueKind
    rows: int
    examples: tuple[str, ...]


class RecordFilePreview(Model):
    """What a record file holds, seen against a log. `event_ends` is the number
    of events the file gives an end time."""

    rows: int
    usable_rows: int
    event_ends: int
    flows: tuple[FlowInFile, ...]
    issues: tuple[RecordIssue, ...]
    records_from: datetime | None
    records_to: datetime | None
