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


class ColumnMapping(Model):
    """Which column of a record file holds what, by the column's name in the
    file; None where the file has no such column. A file can be read once it
    names flow, object and quantity, and either start and end or the event."""

    flow: str | None = None
    object: str | None = None
    quantity: str | None = None
    start_time: str | None = None
    end_time: str | None = None
    event: str | None = None


class RecordFileColumns(Model):
    """The names of an uploaded file's columns, how many rows it has, the
    character that separates its columns, and its first rows as they are (a
    value per column, None where a cell is empty)."""

    columns: tuple[str, ...]
    rows: int
    delimiter: str
    sample: tuple[tuple[str | None, ...], ...]


class FlowDefinition(Model):
    """What a record file cannot know about a flow: set once, by hand.
    `external_ref` points to the flow in another system, e.g. a database of
    emission factors."""

    unit: str
    category: str
    external_ref: str | None = None


class FlowInFile(Model):
    """A flow named in a record file: its rows by kind, how many of all its rows
    can be taken over, and on how many objects."""

    flow_id: str
    rows: int
    usable_rows: int
    interval_records: int
    event_records: int
    objects: int


class RecordIssue(Model):
    """Rows that cannot be taken over, by reason; `examples` are a few of the ids
    not found in the log, or of the file's line numbers."""

    kind: IssueKind
    rows: int
    examples: tuple[str, ...]


class SampleIssue(Model):
    """Why a row of the file's first rows cannot be taken over; `row` counts
    from 0, as the sample does."""

    row: int
    kind: IssueKind


class RecordFilePreview(Model):
    """What a record file holds, seen against a log. `event_ends` is the number
    of events the file gives an end time; `sample_issues` say which of the
    first rows are left out; `decimal_comma` and `day_first_dates` whether
    numbers and times were read in the German way."""

    rows: int
    usable_rows: int
    event_ends: int
    flows: tuple[FlowInFile, ...]
    issues: tuple[RecordIssue, ...]
    records_from: datetime | None
    records_to: datetime | None
    sample_issues: tuple[SampleIssue, ...] = ()
    decimal_comma: bool = False
    day_first_dates: bool = False
